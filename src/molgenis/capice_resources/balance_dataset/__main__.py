import pandas as pd

from molgenis.capice_resources.core import Module, CommandLineInterface
from molgenis.capice_resources.core import GlobalEnums as Genums


class BalanceDataset(Module):
    def __init__(self):
        super(BalanceDataset, self).__init__(
            program='Balance dataset',
            description='Balancing script to balance a CAPICE dataset on Consequence and allele '
                        'frequency.'
                        'Please note that it balances assuming you have used train-data-creator, '
                        'which add a "binarized_label" to the data. The GnomAD allele frequency '
                        'annotation from VEP is also required (custom or VEP flag). '
                        'Also requires the "consequence" column.'
        )
        self.random_state = 5
        self.bins = Genums.AF_BINS.value

    @staticmethod
    def _create_module_specific_arguments(parser):
        required = parser.add_argument_group('Required arguments')
        optional = parser.add_argument_group('Optional arguments')

        required.add_argument(
            '-i',
            '--input',
            type=str,
            required=True,
            help='The input file location. Must be TSV or gzipped TSV!'
        )

        required.add_argument(
            '-o',
            '--output',
            type=str,
            required=True,
            help='The output directory in which the balanced and remainder files should be placed.'
        )

        optional.add_argument(
            '-v',
            '--verbose',
            action='store_true',
            help='Print verbose messages during balancing.'
        )

        return parser

    def _validate_module_specific_arguments(self, parser: CommandLineInterface):
        input_file = self.input_validator.validate_icli_file(
            parser.get_argument('input'),
            Genums.TSV_EXTENSIONS.value
        )
        output = self.input_validator.validate_ocli_directory(
            parser.get_argument('output')
        )
        verbose = parser.get_argument('verbose')
        return {
            **input_file,
            **output,
            **verbose
        }

    def run_module(self, arguments: dict[str, str | object]) -> dict:
        pass

    def export(self, output: dict[object, object]) -> None:
        pass


def main():
    BalanceDataset().run()


if __name__ == '__main__':
    main()
