import gc

from molgenis.capice_resources.core import Module, GlobalEnums
from molgenis.capice_resources.utilities import merge_dataset_rows
from molgenis.capice_resources.train_data_creator import TrainDataCreatorEnums
from molgenis.capice_resources.train_data_creator.data_parsers.vkgl import VKGLParser
from molgenis.capice_resources.train_data_creator.sample_weighter import SampleWeighter
from molgenis.capice_resources.train_data_creator.dataset_splitter import SplitDatasets
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
            GlobalEnums.TSV_EXTENSIONS.value
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
                TrainDataCreatorEnums.CHROMOSOME.value,
                TrainDataCreatorEnums.START.value,
                TrainDataCreatorEnums.SUPPORT.value,
                TrainDataCreatorEnums.CLASSIFICATION.value
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

        train_test, validation = SplitDatasets().split(merge)

        del merge
        gc.collect()

        return {
            GlobalEnums.OUTPUT.value: arguments['output'],
            GlobalEnums.TRAIN_TEST.value: train_test,
            GlobalEnums.VALIDATION.value: validation
        }

    def export(self, output):
        pass


def main():
    TrainDataCreator().run()


if __name__ == '__main__':
    main()
