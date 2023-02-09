import os

import pandas as pd

from molgenis.capice_resources.core import Module, CommandLineInterface, \
    TSVFileEnums, AlleleFrequencyEnums, ColumnEnums, DatasetIdentifierEnums
from molgenis.capice_resources.balance_dataset import BalanceDatasetEnums
from molgenis.capice_resources.balance_dataset.balancer import Balancer


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
        self.bins = AlleleFrequencyEnums.AF_BINS.value

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
        input_file = self.input_validator.validate_input_command_line_interface_file(
            parser.get_argument('input'),
            TSVFileEnums.TSV_EXTENSIONS.value
        )
        output = self.input_validator.validate_output_command_line_interface_path(
            parser.get_argument('output')
        )
        verbose = parser.get_argument('verbose')
        return {
            **input_file,
            **output,
            **verbose
        }

    def run_module(self, arguments):
        dataset = self._read_pandas_tsv(
            arguments['input'],
            [  # type: ignore
                ColumnEnums.GNOMAD_AF.value,
                ColumnEnums.CONSEQUENCE.value,
                ColumnEnums.BINARIZED_LABEL.value
            ]
        )
        self._validate_benign_pathogenic_present(dataset)
        balancer = Balancer(arguments['verbose'])
        balanced, remainder = balancer.balance(dataset)
        return {
            BalanceDatasetEnums.BALANCED.value: balanced,
            BalanceDatasetEnums.REMAINDER.value: remainder,
            DatasetIdentifierEnums.OUTPUT.value: arguments['output']
        }

    @staticmethod
    def _validate_benign_pathogenic_present(dataset: pd.DataFrame) -> None:
        """
        Function to check if both pathogenic and benign samples are present.
        Note: this is different from /core/validator/DataValidator since this specifically
        checks benign and pathogenic. Expanding that validator would decrease its usability in
        multiple modules.

        Args:
            dataset:
                The loaded in pandas.DataFrame of the dataset over which should be balanced.

        Raises:
            ValueError:
                ValueError is raised when either no benign or pathogenic samples are present.

        """
        n_benign = dataset[dataset[ColumnEnums.BINARIZED_LABEL.value] == 0].shape[0]
        n_pathogenic = dataset[dataset[ColumnEnums.BINARIZED_LABEL.value] == 1].shape[0]
        if n_benign == 0:
            raise ValueError('No benign samples present. Balancing not possible.')
        if n_pathogenic == 0:
            raise ValueError('No pathogenic samples present. Balancing not possible.')

    def export(self, output) -> None:
        self.exporter.export_pandas_file(
            os.path.join(  # type: ignore
                output[DatasetIdentifierEnums.OUTPUT.value],
                BalanceDatasetEnums.BALANCED.value
            ) + TSVFileEnums.TSV_EXTENSIONS.value[0],
            output[BalanceDatasetEnums.BALANCED.value]
        )
        self.exporter.export_pandas_file(
            os.path.join(  # type: ignore
                output[DatasetIdentifierEnums.OUTPUT.value],
                BalanceDatasetEnums.REMAINDER.value
            ) + TSVFileEnums.TSV_EXTENSIONS.value[0],
            output[BalanceDatasetEnums.REMAINDER.value]
        )


def main():
    BalanceDataset().run()


if __name__ == '__main__':
    main()
