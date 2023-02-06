import gc
import os
import gzip
from importlib.resources import files

import pandas as pd

from molgenis.capice_resources.core import Module, TSVFileEnums, DatasetIdentifierEnums, VCFEnums, \
    ColumnEnums
from molgenis.capice_resources.utilities import merge_dataset_rows
from molgenis.capice_resources.train_data_creator.filter import SVFilter
from molgenis.capice_resources.train_data_creator.data_parsers.vkgl import VKGLParser
from molgenis.capice_resources.train_data_creator.sample_weighter import SampleWeighter
from molgenis.capice_resources.train_data_creator.dataset_splitter import SplitDatasets
from molgenis.capice_resources.train_data_creator import TrainDataCreatorEnums as Menums
from molgenis.capice_resources.train_data_creator.data_parsers.clinvar import ClinVarParser
from molgenis.capice_resources.train_data_creator.consensus_checker import ConsensusChecker
from molgenis.capice_resources.train_data_creator.duplicate_processor import DuplicateProcessor


class TrainDataCreator(Module):
    def __init__(self):
        super(TrainDataCreator, self).__init__(
            program='Train data creator',
            description='Creator of CAPICE train/test and validation datasets.'
        )

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
        vkgl = self._read_pandas_tsv(
            arguments['input_vkgl'],
            [  # type: ignore
                Menums.CHROMOSOME.value,
                Menums.START.value,
                Menums.SUPPORT.value,
                Menums.CLASSIFICATION.value
            ]
        )
        parsed_vkgl = VKGLParser().parse(vkgl)
        clinvar = self._read_vcf_file(
            arguments['input_clinvar']  # type: ignore
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

    def export(self, output):
        fake_vcf_header = files(
            'molgenis.capice_resources.train_data_creator.resources'
        ).joinpath('fake_vcf_header.txt').read_text()
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
                    *Menums.further_processing_columns(),
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
