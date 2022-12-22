from molgenis.capice_resources.core import Module, GlobalEnums


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
        pass

    def export(self, output):
        pass


def main():
    TrainDataCreator().run()


if __name__ == '__main__':
    main()
