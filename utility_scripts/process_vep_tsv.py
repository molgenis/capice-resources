#!/usr/bin/env python3

import os
import json
import argparse
import typing
import warnings
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd


SAMPLE_WEIGHTS = [0.8, 0.9, 1.0]
# Must be equal to `train_data_creator/src/main/exporter.py` & files in `utility_scripts`
ID_SEPARATOR = '!'


# Defining it here so the initial size can be set, removing duplicated printing code
class ProgressPrinter:
    def __init__(self):
        self.before_drop = {}

    def set_initial_size(self,
                         sample_size: int,
                         dataset_source: Literal['train_test', 'validation']
                         ):
        self.before_drop[dataset_source] = sample_size

    def new_shape(self,
                  sample_size: int,
                  dataset_source: Literal['train_test', 'validation']
                  ):
        print(
            f'Dropped {self.before_drop[dataset_source] - sample_size} variants from '
            f'{dataset_source}.', end='\n\n')
        self.before_drop[dataset_source] = sample_size

    def print_final_shape(self, dataset_type: Literal['train_test', 'validation']):
        print(f'Final number of samples in train_test: {self.before_drop[dataset_type]}')


progress_printer = ProgressPrinter()


class CommandLineParser:
    def __init__(self):
        parser = self._create_argument_parser()
        self.arguments = parser.parse_args()

    @staticmethod
    def _create_argument_parser():
        parser = argparse.ArgumentParser(
            prog='Process VEP TSV',
            description='Processes an VEP output TSV (after running it through BCFTools). '
                        'Removes duplicates, variants that end up on mismatching genes and '
                        'variants that got corrupted on the binarized label or sample weight.'
        )
        required = parser.add_argument_group('Required arguments')
        optional = parser.add_argument_group('Optional arguments')

        required.add_argument(
            '-it',
            '--input_train',
            type=str,
            required=True,
            help='Input location of the train-test VEP TSV'
        )
        required.add_argument(
            '-iv',
            '--input_validation',
            type=str,
            required=True,
            help='Input location of the validation VEP TSV'
        )
        required.add_argument(
            '-o',
            '--output',
            type=str,
            required=True,
            help='Output path'
        )
        required.add_argument(
            '-j',
            '--train_features_json',
            type=str,
            required=True,
            help='The train features json that is used in CAPICE training.'
        )
        required.add_argument(
            '-g',
            '--genes',
            type=str,
            required=True,
            help='File containing all Autosomal Recessive genes, each gene on a newline. '
                 'Available at: https://research.nhgri.nih.gov/CGD/download/txt/CGD.txt.gz'
        )
        optional.add_argument(
            '-a',
            '--assembly',
            action='store_true',
            help='Flag to enable GRCh38 mode.'
        )
        return parser

    def get_argument(self, argument_key):
        value = None
        if argument_key in self.arguments:
            value = getattr(self.arguments, argument_key)
        return value


class Validator:
    def validate_cla_dataset(self, input_path):
        self._validate_input(input_path, ('.tsv.gz', '.tsv'))
        return input_path

    def validate_cla_json(self, input_path):
        self._validate_input(input_path, ('.json', ))
        return input_path

    @staticmethod
    def _validate_input(input_path: os.PathLike, required_extension: tuple[str]):
        if not os.path.isfile(input_path):
            raise FileNotFoundError(f'{input_path} does not exist!')
        if not input_path.endswith(required_extension):
            raise IOError(f'{input_path} does not match the required extension: '
                          f'{", ".join(required_extension)}')

    @staticmethod
    def validate_output_cla(output_path):
        output_path = Path(output_path).absolute()
        if not os.path.isdir(output_path):
            os.makedirs(output_path)
        return output_path

    def validate_cgd_path(self, path):
        self._validate_input(path, ('.txt.gz', '.tsv.gz'))
        return path

    @staticmethod
    def validate_cgd_content(cgd_data):
        required_columns = ['#GENE', 'INHERITANCE']
        for column in required_columns:
            if column not in cgd_data.columns:
                raise KeyError(f'Missing required column in CGD data: {column}')

    @staticmethod
    def validate_input_dataset(input_data: pd.DataFrame, train_features: list):
        required_features = ['SYMBOL', 'CHROM', 'ID', 'gnomAD_HN']
        required_features.extend(train_features)
        missing = []
        for column in required_features:
            if column not in input_data.columns:
                missing.append(column)
        if len(missing) > 0:
            raise KeyError(f'Missing required column in supplied dataset: {", ".join(missing)}')


def load_and_correct_cgd(path, present_genes: typing.Iterable):
    validator = Validator()
    cgd = pd.read_csv(path, sep='\t')
    validator.validate_cgd_content(cgd)
    # Correct TENM1 since it can absolutely not be AR
    cgd.drop(index=cgd[cgd['#GENE'] == 'TENM1'].index, inplace=True)
    return_genes = []
    genes_in_cgd = cgd[cgd['INHERITANCE'].str.contains('AR')]['#GENE'].values
    for gene in genes_in_cgd:
        if gene in present_genes:
            return_genes.append(gene)
    return return_genes


def process_cli(validator):
    print('Obtaining CLA.')
    cli = CommandLineParser()
    train_test_path = validator.validate_cla_dataset(cli.get_argument('input_train'))
    validation_path = validator.validate_cla_dataset(cli.get_argument('input_validation'))
    cgd = validator.validate_cgd_path(cli.get_argument('genes'))
    train_features = validator.validate_cla_json(cli.get_argument('train_features_json'))
    output = validator.validate_output_cla(cli.get_argument('output'))
    grch38 = cli.get_argument('assembly')
    print('Input arguments passed.', end='\n\n')
    return train_test_path, validation_path, output, grch38, cgd, train_features


def print_stats_dataset(data: pd.DataFrame, type_dataset: Literal['train_test', 'validation']):
    print(f'Statistics for dataset: {type_dataset}')
    n_samples = data.shape[0]
    print(f'Sample size: {n_samples}')
    print(f'Feature size: {data.shape[1]}')
    progress_printer.set_initial_size(n_samples, type_dataset)
    print('Head:')
    with pd.option_context('display.max_rows', None, 'display.max_columns', None,
                           'display.precision', 3):
        print(data.head(), end='\n\n')


def drop_genes_empty(data: pd.DataFrame):
    print('Dropping variants without a gene.')
    data.drop(index=data[data['SYMBOL'].isnull()].index, inplace=True)
    progress_printer.new_shape(data[data['dataset_source'] == 'train_test'].shape[0], 'train_test')
    progress_printer.new_shape(data[data['dataset_source'] == 'validation'].shape[0], 'validation')


def process_grch38(data: pd.DataFrame):
    print('Processing GRCh38.')
    data['CHROM'] = data['CHROM'].str.split('chr', expa2nd=True)[1]
    y = np.append(np.arange(1, 23).astype(str), ['X', 'Y', 'MT'])
    data.drop(data[~data["CHROM"].isin(y)].index, inplace=True)
    progress_printer.new_shape(data[data['dataset_source'] == 'train_test'].shape[0], 'train_test')
    progress_printer.new_shape(data[data['dataset_source'] == 'validation'].shape[0], 'validation')


def drop_duplicate_entries(data: pd.DataFrame):
    print('Dropping duplicated variants.')
    data.drop_duplicates(inplace=True)
    progress_printer.new_shape(data[data['dataset_source'] == 'train_test'].shape[0], 'train_test')
    progress_printer.new_shape(data[data['dataset_source'] == 'validation'].shape[0], 'validation')


def drop_mismatching_genes(data: pd.DataFrame):
    print('Dropping variants with mismatching genes.')
    data.drop(
        index=data[data['ID'].str.split(ID_SEPARATOR, expand=True)[4] != data['SYMBOL']].index,
        inplace=True
    )
    progress_printer.new_shape(data[data['dataset_source'] == 'train_test'].shape[0], 'train_test')
    progress_printer.new_shape(data[data['dataset_source'] == 'validation'].shape[0], 'validation')


def drop_heterozygous_variants_in_ar_genes(data: pd.DataFrame, cgd):
    print('Dropping heterozygous variants in AR genes.')
    ar_genes = load_and_correct_cgd(cgd, data['SYMBOL'].unique())
    data.drop(
        data[
            (data['gnomAD_HN'].notnull()) &
            (data['gnomAD_HN'] == 0) &
            (data['SYMBOL'].isin(ar_genes))
        ].index, inplace=True
    )
    progress_printer.new_shape(data[data['dataset_source'] == 'train_test'].shape[0], 'train_test')
    progress_printer.new_shape(data[data['dataset_source'] == 'validation'].shape[0], 'validation')

def extract_label_and_weight(data: pd.DataFrame):
    print('Extracting binarized_label and sample_weight')
    data['binarized_label'] = data['ID'].str.split(ID_SEPARATOR, expand=True)[5].astype(float)
    data['sample_weight'] = data['ID'].str.split(ID_SEPARATOR, expand=True)[6].astype(float)


def drop_variants_incorrect_label_or_weight(data: pd.DataFrame):
    print('Dropping variants with an incorrect label or weight')
    data.drop(index=data[data['binarized_label'].isnull()].index, columns=['ID'], inplace=True)
    data.drop(index=data[~data['binarized_label'].isin([0.0, 1.0])].index, inplace=True)
    data.drop(index=data[~data['sample_weight'].isin(SAMPLE_WEIGHTS)].index, inplace=True)
    progress_printer.new_shape(data[data['dataset_source'] == 'train_test'].shape[0], 'train_test')
    progress_printer.new_shape(data[data['dataset_source'] == 'validation'].shape[0], 'validation')


def print_finalized_statistics(data: pd.DataFrame, dataset_type: Literal['train_test',
                                                                         'validation']):
    progress_printer.print_final_shape(dataset_type)
    print('Value counts of dataset:')
    print(data[['sample_weight', 'binarized_label']].value_counts())
    print(f'Number of benign variants: {data[data["binarized_label"] == 0].shape[0]}')
    print(f'Number of pathogenic variants: {data[data["binarized_label"] == 1].shape[0]}')
    n_other = data[~data["binarized_label"].isin([0, 1])].shape[0]
    if n_other > 0:
        warnings.warn(f'Number of variants that do not have a binarized label of 0 or 1: {n_other}')


def export_data(data: pd.DataFrame, output):
    print(f'Exporting to: {output}')
    data.to_csv(output, index=False, compression='gzip', na_rep='.', sep='\t')


def drop_duplicates(data: pd.DataFrame, features: list) -> None:
    data.drop_duplicates(subset=features, inplace=True)


def merge_data(train_test_data, validation_data):
    train_test_data['dataset_source'] = 'train_test'
    validation_data['dataset_source'] = 'validation'
    return pd.concat([train_test_data, validation_data], ignore_index=True, axis=0)


def split_data(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    train_test = data.loc[data[data['dataset_source'] == 'train_test'].index, :]
    train_test.reset_index(drop=True, inplace=True)
    validation = data.loc[data[data['dataset_source'] == 'validation'].index, :]
    validation.reset_index(drop=True, inplace=True)
    return train_test, validation


def read_dataset(
        path: os.PathLike,
        train_features: list,
        type_dataset: Literal['train_test', 'validation']
) -> pd.DataFrame:
    data = pd.read_csv(path, sep='\t', na_values='.')
    validator = Validator()
    validator.validate_input_dataset(data, train_features)
    print_stats_dataset(data, type_dataset)
    return data


def read_json(path: os.PathLike) -> list[str]:
    with open(path, 'rt') as fh:
        data = list(json.load(fh).keys())
    return data


def main():
    validator = Validator()
    train_test_path, validation_path, output, grch38, cgd, features_path = process_cli(validator)

    print('Reading in dataset')

    train_features = read_json(features_path)
    train_test_data = read_dataset(train_test_path, train_features, 'train_test')
    validation_data = read_dataset(validation_path, train_features, 'validation')

    data = merge_data(train_test_data, validation_data)

    drop_duplicates(data, train_features)

    drop_genes_empty(data)

    if grch38:
        process_grch38(data)

    drop_duplicate_entries(data)

    drop_mismatching_genes(data)

    drop_heterozygous_variants_in_ar_genes(data, cgd)

    extract_label_and_weight(data)

    drop_variants_incorrect_label_or_weight(data)

    train_test, validation = split_data(data)

    print_finalized_statistics(train_test, 'train_test')
    print_finalized_statistics(validation, 'validation')

    export_data(train_test, os.path.join(output, 'train_test.tsv.gz'))
    export_data(validation, os.path.join(output, 'validation.tsv.gz'))


if __name__ == '__main__':
    main()
