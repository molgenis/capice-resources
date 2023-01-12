import gc
import os
import gzip

from molgenis.capice_resources.core import Module
from molgenis.capice_resources.core import GlobalEnums as Genums
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
        vkgl = self.input_validator.validate_icli_file(
            parser.get_argument('input_vkgl'),
            Genums.TSV_EXTENSIONS.value
        )
        clinvar = self.input_validator.validate_icli_file(
            parser.get_argument('input_clinvar'),
            ['.vcf.gz', '.vcf']
        )
        output = self.input_validator.validate_ocli_directory(
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
            [
                Menums.CHROMOSOME.value,
                Menums.START.value,
                Menums.SUPPORT.value,
                Menums.CLASSIFICATION.value
            ]
        )
        parsed_vkgl = VKGLParser().parse(vkgl)
        clinvar = self._read_vcf_file(
            arguments['input_clinvar']
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
            Genums.OUTPUT.value: arguments['output'],
            Genums.TRAIN_TEST.value: train_test,
            Genums.VALIDATION.value: validation
        }

    def export(self, output):
        fake_vcf_header = [
            '##fileformat=VCFv4.2',
            '##contig=<ID=1,length=249250621,assembly=b37>',
            '##contig=<ID=2,assembly=b37,length=243199373>',
            '##contig=<ID=3,assembly=b37,length=198022430>',
            '##contig=<ID=4,length=191154276,assembly=b37>',
            '##contig=<ID=5,length=180915260,assembly=b37>',
            '##contig=<ID=6,length=171115067,assembly=b37>',
            '##contig=<ID=7,length=159138663,assembly=b37>',
            '##contig=<ID=8,length=146364022,assembly=b37>',
            '##contig=<ID=9,length=141213431,assembly=b37>',
            '##contig=<ID=10,length=135534747,assembly=b37>',
            '##contig=<ID=11,length=135006516,assembly=b37>',
            '##contig=<ID=12,length=133851895,assembly=b37>',
            '##contig=<ID=13,length=115169878,assembly=b37>',
            '##contig=<ID=14,length=107349540,assembly=b37>',
            '##contig=<ID=15,length=102531392,assembly=b37>',
            '##contig=<ID=16,length=90354753,assembly=b37>',
            '##contig=<ID=17,length=81195210,assembly=b37>',
            '##contig=<ID=18,length=78077248,assembly=b37>',
            '##contig=<ID=19,length=59128983,assembly=b37>',
            '##contig=<ID=20,length=63025520,assembly=b37>',
            '##contig=<ID=21,length=48129895,assembly=b37>',
            '##contig=<ID=22,length=51304566,assembly=b37>',
            '##contig=<ID=X,assembly=b37,length=155270560>',
            '##contig=<ID=Y,length=59373566,assembly=b37>',
            '##contig=<ID=MT,length=16569,assembly=b37>',
            '##fileDate=20200320'
        ]
        for types in [Genums.TRAIN_TEST.value, Genums.VALIDATION.value]:
            export_loc = os.path.join(
                output[Genums.OUTPUT.value],
                types + '.vcf.gz'
            )
            with gzip.open(export_loc, 'wt') as fh:
                for line in fake_vcf_header:
                    fh.write(f'{line}\n')

            frame = output[types]

            frame['QUAL'] = Menums.EMTPY_VALUE.value
            frame['FILTER'] = 'PASS'
            frame[Genums.INFO.value] = Menums.EMTPY_VALUE.value

            frame[Genums.ID.value] = frame[
                [
                    *Menums.further_processing_columns(),
                    Genums.BINARIZED_LABEL.value,
                    Genums.SAMPLE_WEIGHT.value
                ]
            ].astype(str).agg(Genums.SEPARATOR.value.join, axis=1)

            self.exporter.export_pandas_file(
                export_loc,
                frame[
                    Genums.VCF_CHROM.value,
                    Genums.POS.value,
                    Genums.ID.value,
                    Genums.REF.value,
                    Genums.ALT.value,
                    'QUAL',
                    'FILTER',
                    Genums.INFO.value
                ], mode='a', compression='gzip', na_rep='.'
            )


def main():
    TrainDataCreator().run()


if __name__ == '__main__':
    main()
