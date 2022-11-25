#!/usr/bin/env python3

"""
This is a helper script to balance out an input dataset.
Requires columns (%)Consequence and *_AF.
(%)Consequence: The consequence a variant has (Del, ins, DELINS etc.).
    Can be supplied raw (starting with %) or processed. The most important part
    is Consequence itself.
gnomAD_AF: The desired allele frequency per variant. Can originate from gnomAD or
1000 genomes or NHLBI-ESP, but has to be named gnomAD_AF.

"""
import os
import argparse
import warnings

import numpy as np
import pandas as pd
from pathlib import Path

__random_state__ = 5
__bins__ = [0.0, 0.01, 0.05, 0.1, 0.5, 1.0]


def main():
    # Parse CLA
    cla_parser = ArgumentParser()
    input_path = cla_parser.get_argument('input')
    output_directory = Path(cla_parser.get_argument('output')).absolute()
    # Validate CLA
    cla_validator = CommandLineArgumentsValidator()
    cla_validator.validate_input_path(input_path)
    cla_validator.validate_output_path(output_directory)
    # Load in dataset
    dataset = pd.read_csv(input_path, na_values='.', sep='\t', low_memory=False)
    # Validate dataset
    dataset_validator = InputDatasetValidator()
    dataset_validator.validate_columns_required(dataset)
    dataset_validator.validate_b_p_present(dataset)
    # Run
    balancer = Balancer()
    balanced_dataset = balancer.balance(dataset)
    # Export
    exporter = BalanceExporter(output_path=output_directory)
    exporter.export_balanced_dataset(balanced_dataset)


class ArgumentParser:
    """
    Class to parse the input arguments.
    """

    def __init__(self):
        parser = self._create_argument_parser()
        self.arguments = parser.parse_args()

    @staticmethod
    def _create_argument_parser():
        parser = argparse.ArgumentParser(
            prog=os.path.basename(__file__),
            description='Balancing script to balance a CAPICE dataset on Consequence and allele '
                        'frequency.'
        )

        parser.add_argument(
            '-i',
            '--input',
            type=str,
            action='store',
            required=True,
            help='The input file location. Must be TSV or gzipped TSV!'
        )
        parser.add_argument(
            '-o',
            '--output',
            type=str,
            action='store',
            required=True,
            help='The output directory in which the files should be placed.'
        )

        return parser

    def get_argument(self, argument_key):
        """
        Method to get an input argument.
        :param argument_key: Full command line argument (so --input for the
        input argument).
        :return: List or boolean
        """
        if self.arguments is not None and argument_key in self.arguments:
            value = getattr(self.arguments, argument_key)
        else:
            value = None
        return value


class CommandLineArgumentsValidator:
    """
    Class to check if arguments are valid.
    """

    def validate_input_path(self, input_path):
        self._validate_input_exists(input_path)
        self._validate_input_extension(input_path)

    @staticmethod
    def _validate_input_exists(input_path):
        if not os.path.isfile(input_path):
            raise FileNotFoundError('Input file does not exist!')

    @staticmethod
    def _validate_input_extension(path):
        if not path.endswith('.tsv.gz'):
            raise IOError('Input argument is not gzipped TSV!')

    def validate_output_path(self, output):
        self._validate_output_exists(output)

    @staticmethod
    def _validate_output_exists(output):
        if not os.path.isdir(output):
            warnings.warn(f'Output {output} does not exist, attempting to create.')
            os.makedirs(output)


class InputDatasetValidator:
    """
    Class to check if the input dataset is usable
    """

    @staticmethod
    def validate_columns_required(dataset: pd.DataFrame):
        required_columns = ['Consequence', 'gnomAD_AF', 'binarized_label']
        for col in required_columns:
            if col not in dataset.columns:
                raise KeyError(f'Required column {col} not found in input dataset.')

    @staticmethod
    def validate_b_p_present(dataset: pd.DataFrame):
        """
        Method to validate that at least one pathogenic and one benign sample is present
        """
        if dataset[dataset['binarized_label'] == 0].shape[0] == 0:
            raise ValueError('Not enough benign samples to balance!')
        if dataset[dataset['binarized_label'] == 1].shape[0] == 0:
            raise ValueError('Not enough pathogenic samples to balance!')


class Balancer:
    """
    Class dedicated to performing the balancing algorithm
    """

    def __init__(self):
        self.bins = __bins__
        self.columns = []
        self.drop_benign = pd.Index([])
        self.drop_pathogenic = pd.Index([])

    @staticmethod
    def _obtain_consequences(consequences: pd.Series):
        return pd.Series(
            consequences.str.split('&', expand=True).values.ravel()
        ).dropna().sort_values(ignore_index=True).unique()

    @staticmethod
    def _mark_and_impute(dataset: pd.DataFrame):
        dataset['is_imputed'] = 0
        dataset.loc[dataset['gnomAD_AF'].isnull(), 'is_imputed'] = 1
        dataset['gnomAD_AF'].fillna(0, inplace=True)

    @staticmethod
    def _reset_impute(dataset: pd.DataFrame):
        dataset.loc[dataset['is_imputed'] == 1, 'gnomAD_AF'] = None
        dataset.drop(columns=['is_imputed'], inplace=True)

    def balance(self, dataset: pd.DataFrame):
        self.columns = dataset.columns
        self._mark_and_impute(dataset)
        pathogenic = dataset.loc[dataset[dataset['binarized_label'] == 1].index, :]
        benign = dataset.loc[dataset[dataset['binarized_label'] == 0].index, :]
        return_dataset = pd.DataFrame(columns=self.columns)
        consequences = self._obtain_consequences(dataset['Consequence'])
        for consequence in consequences:
            selected_pathogenic = pathogenic[pathogenic['Consequence'].str.contains(consequence)]
            selected_benign = benign[benign['Consequence'].str.contains(consequence)]
            processed_consequence = self._process_consequence(
                pathogenic_dataset=selected_pathogenic, benign_dataset=selected_benign
            )
            return_dataset = pd.concat(
                [
                    return_dataset,
                    processed_consequence
                ], axis=0
            )
            benign.drop(index=self.drop_benign, inplace=True)
            self.drop_benign = pd.Index([])
            pathogenic.drop(index=self.drop_pathogenic, inplace=True)
            self.drop_pathogenic = pd.Index([])
        self._reset_impute(return_dataset)
        return return_dataset

    def _process_consequence(self, pathogenic_dataset, benign_dataset):
        n_patho = pathogenic_dataset.shape[0]
        n_benign = benign_dataset.shape[0]
        if n_patho > n_benign:
            pathogenic_dataset = pathogenic_dataset.sample(
                n_benign,
                random_state=__random_state__
            )
        pathogenic_histogram, bins = np.histogram(
            pathogenic_dataset['gnomAD_AF'],
            bins=self.bins
        )
        processed_bins = pd.DataFrame(columns=self.columns)
        for ind in range(len(bins) - 1):
            lower_bound = bins[ind]
            upper_bound = bins[ind + 1]
            sample_number = pathogenic_histogram[ind]
            processed_bins = pd.concat(
                [
                    processed_bins,
                    self._process_bins(
                        pathogenic_dataset, benign_dataset, upper_bound, lower_bound, sample_number
                    )
                ], axis=0
            )
        return processed_bins

    def _process_bins(
            self, pathogenic_dataset, benign_dataset, upper_bound, lower_bound, sample_num
    ):
        selected_pathogenic = self._get_variants_within_range(
            pathogenic_dataset, upper_bound=upper_bound, lower_bound=lower_bound
        )
        selected_benign = self._get_variants_within_range(
            benign_dataset, upper_bound=upper_bound, lower_bound=lower_bound
        )
        if sample_num < selected_benign.shape[0]:
            return_benign = selected_benign.sample(
                sample_num,
                random_state=__random_state__
            )
            return_pathogenic = selected_pathogenic
        else:
            return_benign = selected_benign
            return_pathogenic = selected_pathogenic.sample(
                selected_benign.shape[0],
                random_state=__random_state__
            )
        self.drop_benign = self.drop_benign.union(return_benign.index)
        self.drop_pathogenic = self.drop_pathogenic.union(return_pathogenic.index)
        return pd.concat(
            [return_benign, return_pathogenic], axis=0
        )

    @staticmethod
    def _get_variants_within_range(dataset, upper_bound, lower_bound):
        return dataset[(dataset['gnomAD_AF'] >= lower_bound) & (dataset['gnomAD_AF'] < upper_bound)]


class BalanceExporter:
    """
    Class dedicated to exporting of splitting datasets and exporting of the balancing dataset.
    """

    def __init__(self, output_path):
        self.output_path = output_path

    def export_balanced_dataset(self, dataset):
        output_path = os.path.join(self.output_path, 'balanced_dataset.tsv.gz')
        self._export_dataset(dataset, output_path)

    def export_remainder_dataset(self, dataset):
        output_path = os.path.join(self.output_path, 'remainder_dataset.tsv.gz')
        self._export_dataset(dataset, output_path)

    @staticmethod
    def _export_dataset(dataset, path):
        dataset.to_csv(
            path_or_buf=path, sep='\t', na_rep='.', index=False, compression='gzip'
        )
        print(f'Successfully exported {path}')


if __name__ == '__main__':
    main()
