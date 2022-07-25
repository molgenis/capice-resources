#!/usr/bin/env python3

import os
import gzip
import argparse
import warnings

import pandas as pd
from matplotlib import pyplot as plt
from sklearn.metrics import roc_curve, auc

from utility_scripts.compare_models import correct_column_names

ID_SEPARATOR = '!'


# Defining errors
class IncorrectFileError(Exception):
    pass


class DataError(Exception):
    pass


class CommandLineDigest:
    def __init__(self):
        parser = self._create_argument_parser()
        self.arguments = parser.parse_args()

    def _create_argument_parser(self):
        parser = argparse.ArgumentParser(
            prog='Compare to legacy model',
            description='Compares a new model to the legacy model created by Li et al.'
        )
        required = parser.add_argument_group('Required arguments')

        required.add_argument(
            '--old_model_results',
            type=str,
            required=True,
            help='Input location of the scores file generated with the old Li et al. CAPICE model '
                 '(XGBoost >= 0.90). Has to be a (gzipped) tsv!'
        )

        required.add_argument(
            '--old_model_cadd_input',
            type=str,
            required=True,
            help='Location of the input VCF that is uploaded to CADD for annotations using CADD '
                 '1.4 as an input for the legacy Li et al. CAPICE model. Has to be a gzipped VCF!'
        )

        required.add_argument(
            '--new_model_results',
            type=str,
            required=True,
            help='Input location of the scores file generated with the new CAPICE model '
                 '(XGBoost == 1.4.2). Has to be a gzipped tsv!'
        )

        required.add_argument(
            '--new_model_capice_input',
            type=str,
            required=True,
            help='Location of the file to generate the scores from `new_model_results`. Has to '
                 'contain the binarized_labels to that file! Has to match the `new_model_results` '
                 'sample size! Required in (gzipped) tsv!'
        )

        required.add_argument(
            '--output',
            type=str,
            required=True,
            help='Output directory.'
        )

        return parser

    def get_argument(self, argument_key):
        value = None
        if argument_key in self.arguments:
            value = getattr(self.arguments, argument_key)
        return value


class Validator:

    def validate_old_scores_argument(self, old_input_path):
        self._validate_argument(old_input_path, ('.tsv', '.tsv.gz'))

    def validate_old_labels_argument(self, ol_input_path):
        self._validate_argument(ol_input_path, '.vcf.gz')

    def validate_new_input_argument(self, new_input_path):
        self._validate_argument(new_input_path, '.tsv.gz')

    @staticmethod
    def _validate_argument(argument, extension):
        if not argument.endswith(extension):
            raise IncorrectFileError(
                f'Argument {argument} was supplied an incorrect extension. '
                f'Required extensions: {extension}'
            )

    @staticmethod
    def validate_output_argument(output):
        if not os.path.isdir(output):
            warnings.warn(f'Output path {output} does not exist! Creating...')
            try:
                os.makedirs(output)
            except Exception as e:
                print(f'Error encoutered creating output path: {e}')
                exit(1)

    def validate_old_scores_dataset(self, data):
        required_columns = ['chr_pos_ref_alt', 'GeneName', 'probabilities']
        self._validate_dataframe(data, required_columns, 'Old CAPICE scores dataset')

    def validate_old_labels_dataset(self, data):
        required_columns = ['ID']
        self._validate_dataframe(data, required_columns, 'Old CAPICE CADD input')

    def validate_new_scores_dataset(self, data):
        required_columns = ['score', 'chr', 'pos', 'ref', 'alt', 'gene_name']
        self._validate_dataframe(data, required_columns, 'New CAPICE scores dataset')

    def validate_new_labels_dataset(self, data):
        required_columns = ['binarized_label']
        self._validate_dataframe(data, required_columns, 'New CAPICE labels dataset')

    def validate_can_merge_new_scores(self, data):
        required_columns = ['chr', 'pos', 'ref', 'alt', 'gene_name']
        self._validate_dataframe(data, required_columns, 'New CAPICE scores dataset for merging')

    def validate_can_merge_new_labels(self, data):
        required_columns = ['CHROM', 'POS', 'REF', 'ALT', 'SYMBOL']
        self._validate_dataframe(data, required_columns, 'New CAPICE labels dataset for merging')

    @staticmethod
    def _validate_dataframe(data, required_columns, dataset):
        for column in required_columns:
            if column not in data.columns:
                raise DataError(f'Required column {column} not found in: {dataset}!')


def main():
    warnings.warn('This script will become obsolete once the performance of the newer models '
                  'match or surpass the performance of the model by Li et al.', DeprecationWarning)
    print('Obtaining command line arguments')
    cla = CommandLineDigest()
    old_scores = cla.get_argument('old_model_results')
    old_labels = cla.get_argument('old_model_cadd_input')
    new_scores = cla.get_argument('new_model_results')
    new_labels = cla.get_argument('new_model_capice_input')
    output = cla.get_argument('output')
    print('Validating command line arguments')
    validator = Validator()
    validator.validate_old_scores_argument(old_scores)
    validator.validate_old_labels_argument(old_labels)
    validator.validate_new_input_argument(new_scores)
    validator.validate_new_input_argument(new_labels)
    validator.validate_output_argument(output)
    print('Arguments passed\n')

    # Reading in data
    print('Reading data')
    old_scores = pd.read_csv(old_scores, sep='\t')
    n_skip = 0
    if old_labels.endswith('.gz'):
        fh = gzip.open(old_labels, 'rt')
    else:
        fh = open(old_labels, 'rt')
    for line in fh:
        if line.startswith('##'):
            n_skip += 1
        else:
            break
    fh.close()
    old_labels = pd.read_csv(old_labels, sep='\t', skiprows=n_skip)
    new_scores = pd.read_csv(new_scores, sep='\t')
    new_labels = pd.read_csv(new_labels, sep='\t')
    new_labels.columns = correct_column_names(new_labels.columns)
    print('Validating data')
    validator.validate_old_scores_dataset(old_scores)
    validator.validate_old_labels_dataset(old_labels)
    validator.validate_new_scores_dataset(new_scores)
    validator.validate_new_labels_dataset(new_labels)
    print('All data loaded:')
    print(f'Amount of variants within the old CAPICE scores dataset: {old_scores.shape[0]}. '
          f'Columns: {old_scores.shape[1]}')
    print(f'Amount of variants within the old CAPICE labels dataset: {old_labels.shape[0]}. '
          f'Columns: {old_labels.shape[1]}')
    print(f'Amount of variants within the new CAPICE scores dataset" {new_scores.shape[0]}. '
          f'Columns: {new_scores.shape[1]}')
    print(f'Amount of variants within the new CAPICE labels dataset" {new_labels.shape[0]}. '
          f'Columns: {new_labels.shape[1]}')
    print('Data passed.')

    print('Merging datasets.')
    if new_scores.shape[0] != new_labels.shape[0]:
        warnings.warn('Score and label file of the new CAPICE model mismatch in size, attempting '
                      'to merge back together.')
        validator.validate_can_merge_new_scores(new_scores)
        validator.validate_can_merge_new_labels(new_labels)
        new_scores['merge_column'] = new_scores[
            ['chr', 'pos', 'ref', 'alt', 'gene_name']
        ].astype(str).agg(ID_SEPARATOR.join, axis=1)
        new_labels['merge_column'] = new_labels[
            ['CHROM', 'POS', 'REF', 'ALT', 'SYMBOL']
        ].astype(str).agg(ID_SEPARATOR.join, axis=1)
        new_merged = new_scores.merge(new_labels, on='merge_column', how='left')
    else:
        new_merged = pd.concat(
            [
                new_scores,
                new_labels['binarized_label']
            ], axis=1
        )
    new_merged = new_merged[['score', 'binarized_label']]

    # Making merge column
    old_scores['chr_pos_ref_alt'] = old_scores['chr_pos_ref_alt'].str.split(
        '_', expand=True).astype(str).agg(ID_SEPARATOR.join, axis=1)
    old_scores['merge_column'] = old_scores[
        ['chr_pos_ref_alt', 'GeneName']
    ].astype(str).agg(ID_SEPARATOR.join, axis=1)
    try:
        old_labels['merge_column'] = old_labels['ID'].str.split(
            ID_SEPARATOR, expand=True).loc[:, :4].astype(
            str).agg(ID_SEPARATOR.join, axis=1)
    except (ValueError, KeyError):
        raise IncorrectFileError(f'Could not separate the old labels file on the ID column! Is '
                                 f'this column up to date? (current string split: {ID_SEPARATOR})')

    # Merging
    old_merged = old_scores.merge(old_labels, on='merge_column', how='left')

    # Attempting to obtain the binarized_label for the old model datasets.
    old_merged['binarized_label'] = old_merged['ID'].str.split(
        ID_SEPARATOR, expand=True)[5].astype(float)

    old_merged = old_merged[['probabilities', 'binarized_label']]
    old_merged.rename(columns={'probabilities': 'score'}, inplace=True)
    print('Merging done.')

    print('Plotting.')
    # Preparing the difference column
    new_merged['diff'] = abs(new_merged['score'] - new_merged['binarized_label'])
    old_merged['diff'] = abs(old_merged['score'] - old_merged['binarized_label'])

    # Preparing plots
    fig_roc = plt.figure()
    fig_roc.suptitle('ROC curves legacy model versus new model.')

    fig_score_dist = plt.figure()
    fig_score_dist.suptitle('Raw score distributions of legacy model versus new model.')

    fig_score_diff = plt.figure()
    fig_score_diff.suptitle('Absolute difference between the score and labels ')

    # Calculating global AUC
    old_merged.dropna(inplace=True)
    fpr_old, tpr_old, _ = roc_curve(old_merged['binarized_label'], old_merged['score'])
    auc_old = auc(fpr_old, tpr_old)
    new_merged.dropna(inplace=True)
    fpr_new, tpr_new, _ = roc_curve(new_merged['binarized_label'], new_merged['score'])
    auc_new = auc(fpr_new, tpr_new)

    # Plotting ROC curves
    ax_roc = fig_roc.add_subplot(1, 1, 1)
    ax_roc.plot(fpr_old, tpr_old, color='red', label=f'Legacy: {auc_old}')
    ax_roc.plot(fpr_new, tpr_new, color='blue', label=f'New: {auc_new}')
    ax_roc.set_xlim(0.0, 1.0)
    ax_roc.set_ylim(0.0, 1.0)
    ax_roc.legend(loc='lower right')

    # Plotting raw score distributions
    ax_score_dist = fig_score_dist.add_subplot(1, 1, 1)
    ax_score_dist.boxplot(
        [
            old_merged[old_merged['binarized_label'] == 0]['score'],
            old_merged[old_merged['binarized_label'] == 1]['score'],
            new_merged[new_merged['binarized_label'] == 0]['score'],
            new_merged[new_merged['binarized_label'] == 1]['score']
        ], labels=['L_B', 'L_P', 'N_B', 'N_P']
    )
    ax_score_dist.set_ylim(0.0, 1.0)

    # Plotting the score differences to the true label
    ax_score_diff = fig_score_diff.add_subplot(1, 1, 1)
    ax_score_diff.boxplot(
        [
            old_merged[old_merged['binarized_label'] == 0]['diff'],
            old_merged[old_merged['binarized_label'] == 1]['diff'],
            new_merged[new_merged['binarized_label'] == 0]['diff'],
            new_merged[new_merged['binarized_label'] == 1]['diff']
        ], labels=['B_old', 'B_new', 'P_old', 'P_new']
    )
    ax_score_diff.set_ylim(0.0, 1.0)
    print('Plotting global AUC done.')

    print(f'Exporting plots to: {output}')
    fig_roc.savefig(os.path.join(output, 'roc.png'))
    fig_score_dist.savefig(os.path.join(output, 'distribution.png'))
    fig_score_diff.savefig(os.path.join(output, 'difference.png'))
    print('Done.')


if __name__ == '__main__':
    main()

