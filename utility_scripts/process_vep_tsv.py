#!/usr/bin/env python3

import os
import argparse
import typing
import warnings

import numpy as np
import pandas as pd


# Defining errors
class IncorrectFileError(Exception):
    pass


class DataError(Exception):
    pass


SAMPLE_WEIGHTS = [0.8, 0.9, 1.0]
# Must be equal to `train_data_creator/src/main/exporter.py` & files in `utility_scripts`
ID_SEPARATOR = '!'


# Defining it here so the initial size can be set, removing duplicated printing code
class ProgressPrinter:
    def __init__(self):
        self.before_drop = 0

    def set_initial_size(self, sample_size: int):
        self.before_drop = sample_size

    def new_shape(self, sample_size: int):
        print(f'Dropped {self.before_drop - sample_size} variants.\n')
        self.before_drop = sample_size

    def print_final_shape(self):
        print(f'Final number of samples: {self.before_drop}')


progress_printer = ProgressPrinter()


class CommandLineParser:
    def __init__(self):
        parser = self._create_argument_parser()
        self.arguments = parser.parse_args()

    def _create_argument_parser(self):
        parser = argparse.ArgumentParser(
            prog='Process VEP TSV',
            description='Processes an VEP output TSV (after running it through BCFTools). '
                        'Removes duplicates, variants that end up on mismatching genes and '
                        'variants that got corrupted on the binarized label or sample weight.'
        )
        required = parser.add_argument_group('Required arguments')
        optional = parser.add_argument_group('Optional arguments')

        required.add_argument(
            '-i',
            '--input',
            type=str,
            required=True,
            help='Input location of the VEP TSV'
        )
        required.add_argument(
            '-o',
            '--output',
            type=str,
            required=True,
            help='Output path + filename'
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
    @staticmethod
    def validate_input_cla(input_path):
        if not input_path.endswith(('.tsv.gz', '.tsv')):
            raise IncorrectFileError('Input file is not a TSV!')

    @staticmethod
    def validate_output_cla(output_path):
        if not output_path.endswith('.tsv.gz'):
            raise IncorrectFileError('Output file has to be defined as .tsv.gz!')
        # This is intentional.
        # You have more than enough time to prepare directories when VEP is running.
        if not os.path.isdir(os.path.dirname(output_path)):
            raise NotADirectoryError('Output file has to be placed in an directory that already '
                                     'exists!')

    @staticmethod
    def validate_cgd(path):
        if not path.endswith('CGD.txt.gz'):
            raise IncorrectFileError('Input CGD is not the raw downloaded CGD file!')

    @staticmethod
    def validate_input_dataset(input_data):
        columns_must_be_present = ['%SYMBOL', '%CHROM', '%ID', '%gnomAD_HN']
        for column in columns_must_be_present:
            if column not in input_data.columns:
                raise DataError(f'Missing required column: {column}')


def load_and_correct_cgd(path, present_genes: typing.Iterable):
    cgd = pd.read_csv(path, sep='\t')
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
    data_path = cli.get_argument('input')
    output = cli.get_argument('output')
    grch38 = cli.get_argument('assembly')
    cgd = cli.get_argument('genes')

    print('Validating CLA.')
    validator.validate_input_cla(data_path)
    validator.validate_cgd(cgd)
    validator.validate_output_cla(output)
    print('Input arguments passed.\n')
    return data_path, output, grch38, cgd


def print_stats_dataset(data: pd.DataFrame, validator):
    print('Validating dataset.')
    validator.validate_input_dataset(data)
    print('Dataset passed.')
    n_samples = data.shape[0]
    print(f'Sample size: {n_samples}')
    print(f'Feature size: {data.shape[1]}')
    progress_printer.set_initial_size(n_samples)
    print('Head:')
    with pd.option_context('display.max_rows', None, 'display.max_columns', None,
                           'display.precision', 3):
        print(data.head())


def drop_genes_empty(data: pd.DataFrame):
    print('Dropping variants without a gene.')
    data.drop(index=data[data['%SYMBOL'].isnull()].index, inplace=True)
    progress_printer.new_shape(data.shape[0])


def process_grch38(data: pd.DataFrame):
    print('Processing GRCh38.')
    data['%CHROM'] = data['%CHROM'].str.split('chr', expand=True)[1]
    y = np.append(np.arange(1, 23).astype(str), ['X', 'Y', 'MT'])
    data.drop(data[~data["%CHROM"].isin(y)].index, inplace=True)
    progress_printer.new_shape(data.shape[0])


def drop_duplicate_entries(data: pd.DataFrame):
    print('Dropping duplicated variants.')
    data.drop_duplicates(inplace=True)
    progress_printer.new_shape(data.shape[0])


def drop_mismatching_genes(data: pd.DataFrame):
    print('Dropping variants with mismatching genes.')
    data.drop(
        index=data[data['%ID'].str.split(ID_SEPARATOR, expand=True)[4] != data['%SYMBOL']].index,
        inplace=True
    )
    progress_printer.new_shape(data.shape[0])


def drop_heterozygous_variants_in_ar_genes(data: pd.DataFrame, cgd):
    print('Dropping heterozygous variants in AR genes.')
    ar_genes = load_and_correct_cgd(cgd, data['%SYMBOL'].unique())
    data.drop(
        data[
            (data['%gnomAD_HN'].notnull()) &
            (data['%gnomAD_HN'] == 0) &
            (data['%SYMBOL'].isin(ar_genes))
        ].index, inplace=True
    )
    progress_printer.new_shape(data.shape[0])


def extract_label_and_weight(data: pd.DataFrame):
    print('Extracting binarized_label and sample_weight')
    data['binarized_label'] = data['%ID'].str.split(ID_SEPARATOR, expand=True)[5].astype(float)
    data['sample_weight'] = data['%ID'].str.split(ID_SEPARATOR, expand=True)[6].astype(float)


def drop_variants_incorrect_label_or_weight(data: pd.DataFrame):
    print('Dropping variants with an incorrect label or weight')
    data.drop(index=data[data['binarized_label'].isnull()].index, columns=['%ID'], inplace=True)
    data.drop(index=data[~data['binarized_label'].isin([0.0, 1.0])].index, inplace=True)
    data.drop(index=data[~data['sample_weight'].isin(SAMPLE_WEIGHTS)].index, inplace=True)
    progress_printer.new_shape(data.shape[0])


def print_finalized_statistics(data: pd.DataFrame):
    progress_printer.print_final_shape()
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


def main():
    validator = Validator()
    data_path, output, grch38, cgd = process_cli(validator)

    print('Reading in dataset')
    data = pd.read_csv(data_path, sep='\t', na_values='.')
    print_stats_dataset(data, validator)
    
    drop_genes_empty(data)

    if grch38:
        process_grch38(data)

    drop_duplicate_entries(data)
    
    drop_mismatching_genes(data)

    drop_heterozygous_variants_in_ar_genes(data, cgd)

    extract_label_and_weight(data)

    drop_variants_incorrect_label_or_weight(data)

    print_finalized_statistics(data)

    export_data(data, output)


if __name__ == '__main__':
    main()
