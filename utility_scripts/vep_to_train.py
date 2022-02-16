#!/usr/bin/env python3

import os
import argparse
import warnings

import numpy as np
import pandas as pd


# Defining errors
class IncorrectFileError(Exception):
    pass


class DataError(Exception):
    pass


SAMPLE_WEIGHTS = [0.8, 0.9, 1.0]


class CommandLineDigest:
    def __init__(self):
        parser = self._create_argument_parser()
        self.arguments = parser.parse_args()

    def _create_argument_parser(self):
        parser = argparse.ArgumentParser(
            prog='Make VEP TSV train ready',
            description='Converts an VEP output TSV (after conversion) to make it train ready.'
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
    def validate_input_dataset(input_data):
        columns_must_be_present = ['%SYMBOL', '%CHROM', '%ID']
        for column in columns_must_be_present:
            if column not in input_data.columns:
                raise DataError(f'Missing required column: {column}')


def main():
    print('Parsing CLI')
    cli = CommandLineDigest()
    data_path = cli.get_argument('input')
    output = cli.get_argument('output')
    grch38 = cli.get_argument('assembly')
    print('')

    print('Validating input arguments.')
    validator = Validator()
    validator.validate_input_cla(data_path)
    validator.validate_output_cla(output)

    print('Reading in dataset')
    data = pd.read_csv(data_path, sep='\t', na_values='.')
    print('Validating dataset')
    validator.validate_input_dataset(data)
    print('Read in dataset.')
    print(f'Shape: {data.shape}')
    print(f'Head:\n{data.head()}\n')
    
    print('Dropping entries without gene.')
    before_drop = data.shape[0]
    data.drop(index=data[data['%SYMBOL'].isnull()].index, inplace=True)
    after_drop = data.shape[0]
    print(f'Dropped {before_drop-after_drop} variants.\n')

    if grch38:
        print('Converting chromosome column')
        data['%CHROM'] = data['%CHROM'].str.split('chr', expand=True)[1]
        y = np.append(np.arange(1, 23).astype(str), ['X', 'Y', 'MT'])
        before_drop = data.shape[0]
        data.drop(data[~data["%CHROM"].isin(y)].index, inplace=True)
        after_drop = data.shape[0]
        print(f'Dropped {before_drop-after_drop} rows due to unknown chromosome.')
        print('Conversion done.\n')

    print('Dropping full duplicates')
    before_drop = data.shape[0]
    data.drop_duplicates(inplace=True)
    after_drop = data.shape[0]
    print(f'Dropped {before_drop-after_drop} duplicates')
    print('Dropping duplicates done.\n')
    
    print('Dropping mismatching gene entries.')
    before_drop = data.shape[0]
    data.drop(
        index=data[data['%ID'].str.split('_', expand=True)[4] != data['%SYMBOL']].index,
        inplace=True
    )
    after_drop = data.shape[0]
    print(f'Dropped {before_drop-after_drop} variants.\n')
    
    print('Extracting sample weight and binarized_label')
    data['binarized_label'] = data['%ID'].str.split('_', expand=True)[5].astype(float)
    data['sample_weight'] = data['%ID'].str.split('_', expand=True)[6].astype(float)
    print('')
    
    print('Correcting possible errors within binarized_label or sample_weight')
    before_drop = data.shape[0]
    # Drop everything that doesn't have a binarized_label, also drop unused columns
    data.drop(index=data[data['binarized_label'].isnull()].index, columns=['%ID'], inplace=True)
    data.drop(index=data[~data['binarized_label'].isin([0.0, 1.0])].index, inplace=True)
    data.drop(index=data[~data['sample_weight'].isin(SAMPLE_WEIGHTS)].index, inplace=True)
    after_drop = data.shape[0]
    print(f'Dropped {before_drop-after_drop} variants due to incorrect binarized_label or '
          f'sample_weight.\n')

    print('Please check the sample weights:')
    print(data[['binarized_label', 'sample_weight']].value_counts())
    print('')

    print(f'Final shape of data: {data.shape}')
    print(f'Of which benign: {data[data["binarized_label"] == 0].shape[0]}')
    print(f'Of which pathogenic: {data[data["binarized_label"] == 1].shape[0]}')
    n_other = data[~data["binarized_label"].isin([0, 1])].shape[0]
    if n_other > 0:
        warnings.warn(f'Of which other: {n_other}')
    print('')

    print(f'Done! Exporting to {output}')
    data.to_csv(output, index=False, compression='gzip', na_rep='.', sep='\t')


if __name__ == '__main__':
    main()
