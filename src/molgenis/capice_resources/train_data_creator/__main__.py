import gc
import os
import gzip
from datetime import datetime
from importlib.resources import files

import pandas as pd

from molgenis.capice_resources import __version__
from molgenis.capice_resources.core import Module, TSVFileEnums, DatasetIdentifierEnums, VCFEnums, \
    ColumnEnums
from molgenis.capice_resources.utilities import merge_dataset_rows
from molgenis.capice_resources.train_data_creator.filter import SVFilter
from molgenis.capice_resources.train_data_creator.data_parsers.vkgl import VKGLParser
from molgenis.capice_resources.train_data_creator.sample_weighter import SampleWeighter
from molgenis.capice_resources.train_data_creator.dataset_splitter import SplitDatasets
from molgenis.capice_resources.train_data_creator import TrainDataCreatorEnums
from molgenis.capice_resources.train_data_creator.data_parsers.clinvar import ClinVarParser
from molgenis.capice_resources.train_data_creator.consensus_checker import ConsensusChecker
from molgenis.capice_resources.train_data_creator.duplicate_processor import DuplicateProcessor


class TrainDataCreator(Module):
    def __init__(self):
        super(TrainDataCreator, self).__init__(
            program='Train data creator',
            description='Creator of CAPICE train/test and validation datasets.'
        )
        self.input_vkgl_filename = ''
        self.input_clinvar_filename = ''

    @staticmethod
    def _create_module_specific_arguments(parser):
        required = parser.add_argument_group('Required arguments')
        required.add_argument(
            '-v',
            '--input-vkgl',
            type=str,
            required=True,
            help='Input location of the public VKGL dataset'
        )
        required.add_argument(
            '-c',
            '--input-clinvar',
            type=str,
            required=True,
            help='Input location of the ClinVar dataset.'
        )
        required.add_argument(
            '-o',
            '--output',
            type=str,
            required=True,
            help='Output directory where the files should be placed.'
        )
        return parser

    def _validate_module_specific_arguments(self, parser):
        vkgl = self.input_validator.validate_input_command_line_interface_file(
            parser.get_argument('input_vkgl'),
            TSVFileEnums.TSV_EXTENSIONS.value
        )
        clinvar = self.input_validator.validate_input_command_line_interface_file(
            parser.get_argument('input_clinvar'),
            ('.vcf.gz', '.vcf')
        )
        output = self.input_validator.validate_output_command_line_interface_path(
            parser.get_argument('output')
        )
        return {
            **vkgl,
            **clinvar,
            **output
        }

    def run_module(self, arguments):
        # Obtaining and further validating CLI
        vkgl_arg = arguments['input_vkgl']
        self.input_vkgl_filename = os.path.basename(vkgl_arg)
        self._validate_vkgl_date()
        clinvar_arg = arguments['input_clinvar']
        self.input_clinvar_filename = os.path.basename(clinvar_arg)
        self._validate_clinvar_date()

        # Parsing
        vkgl = self._read_pandas_tsv(
            vkgl_arg,
            [  # type: ignore
                TrainDataCreatorEnums.CHROMOSOME.value,
                TrainDataCreatorEnums.START.value,
                TrainDataCreatorEnums.SUPPORT.value,
                TrainDataCreatorEnums.CLASSIFICATION.value
            ]
        )
        parsed_vkgl = VKGLParser().parse(vkgl)

        clinvar = self._read_vcf_file(
            clinvar_arg  # type: ignore
        )
        parsed_clinvar = ClinVarParser().parse(clinvar)
        merge = merge_dataset_rows(parsed_clinvar, parsed_vkgl)
        del clinvar, parsed_clinvar, vkgl, parsed_vkgl
        gc.collect()

        ConsensusChecker().check_consensus_clinvar_vkgl_match(merge)

        DuplicateProcessor().process(merge)

        SampleWeighter().apply_sample_weight(merge)

        SVFilter().filter(merge)

        train_test, validation = SplitDatasets().split(merge)

        del merge
        gc.collect()

        return {
            DatasetIdentifierEnums.OUTPUT.value: arguments['output'],
            DatasetIdentifierEnums.TRAIN_TEST.value: train_test,
            DatasetIdentifierEnums.VALIDATION.value: validation
        }

    def _validate_vkgl_date(self) -> None:
        """
        Method to validate that the supplied VKGL file contains the file date.

        Raises:
            IOError:
                IOError is raised when the VKGL file does not adhere
                to the standard datetime format.
        """
        date_in_filename = self.input_vkgl_filename.split('_')[-1].split('.')[0]
        # Check for the "old" format of MMMYYYY
        old_valid = self._check_date_format(date_in_filename, '%b%Y')
        # The "new" format of YYYYMM
        new_valid = self._check_date_format(date_in_filename, '%Y%m')
        if not new_valid and not old_valid:
            raise IOError('Supplied VKGL file does not contain standard datetime format!')

    def _validate_clinvar_date(self) -> None:
        """
        Method to validate that the supplied ClinVar file contains the file date.

        Raises:
            IOError:
                IOError is raised when the ClinVar file does not adhere
                to the standard datetime format.
        """
        date_in_filename = self.input_clinvar_filename.split('_')[-1].split('.')[0]
        date_valid = self._check_date_format(date_in_filename, '%Y%m%d')
        if not date_valid:
            raise IOError('Supplied ClinVar file does not contain the standard datetime format!')

    @staticmethod
    def _check_date_format(date_string: str, format_string: str) -> bool:
        """
        Function to check date_string for format_string.
        Returns True if date_string adheres to format_string, else returns False.

        Args:
            date_string:
                String of the date to be checked.
            format_string:
                datetime string of the format the date_string should be in.

        Returns:
            bool
                Returns boolean True if date_string adheres to format_string, else returns False.
        """
        return_value = True
        try:
            datetime.strptime(date_string, format_string)
        except ValueError:
            return_value = False
        return return_value

    def create_fake_vcf_header(self):
        """
        Method to create the fake VCF header and add train-data-creator specific metadata.
        Also sets the correct VCF date.
        Returns:
            header
                Returns a single string of the VCF header, each metadata point separated by \\n with
                the final metadata point ending in \\n.
        """
        header = files(
            'molgenis.capice_resources.train_data_creator.resources'
        ).joinpath('fake_vcf_header.txt').read_text().strip().split('\n')
        header.append(f'##CAPICE-Resources_version={__version__}')
        header.append(f'##Used_ClinVar_File={self.input_clinvar_filename}')
        header.append(f'##Used_VKGL_File={self.input_vkgl_filename}')
        header.append(f'##fileDate={datetime.now().strftime("%Y%m%d")}\n')
        return '\n'.join(header)

    def export(self, output):
        fake_vcf_header = self.create_fake_vcf_header()
        for types in [
            DatasetIdentifierEnums.TRAIN_TEST.value,
            DatasetIdentifierEnums.VALIDATION.value
        ]:
            export_loc = os.path.join(  # type: ignore
                output[DatasetIdentifierEnums.OUTPUT.value],
                types + '.vcf.gz'
            )
            with gzip.open(export_loc, 'wt') as fh:
                fh.write(fake_vcf_header)

            # Defining frame as pd.DataFrame else "frame" would throw confusion within pycharm
            frame: pd.DataFrame = output[types]  # type: ignore

            frame['QUAL'] = TSVFileEnums.NA_VALUES.value
            frame['FILTER'] = 'PASS'
            frame[VCFEnums.INFO.value] = TSVFileEnums.NA_VALUES.value

            frame[VCFEnums.ID.value] = frame[
                [
                    *TrainDataCreatorEnums.further_processing_columns(),
                    ColumnEnums.BINARIZED_LABEL.value,
                    ColumnEnums.SAMPLE_WEIGHT.value
                ]
            ].astype(str).agg(VCFEnums.ID_SEPARATOR.value.join, axis=1)

            self.exporter.export_pandas_file(
                export_loc,
                frame[
                    [
                        VCFEnums.CHROM.vcf_name,
                        VCFEnums.POS.value,
                        VCFEnums.ID.value,
                        VCFEnums.REF.value,
                        VCFEnums.ALT.value,
                        'QUAL',
                        'FILTER',
                        VCFEnums.INFO.value
                    ]
                ], mode='a', compression='gzip', na_rep=TSVFileEnums.NA_VALUES.value
            )


def main():
    TrainDataCreator().run()


if __name__ == '__main__':
    main()
