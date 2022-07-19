#!/usr/bin/env python3

import os
import argparse
import warnings

import math
import pandas as pd
from matplotlib import pyplot as plt
from sklearn.metrics import roc_auc_score

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
        required_columns = ['%ID']
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
        required_columns = ['%CHROM', '%POS', '%REF', '%ALT', '%SYMBOL']
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
    old_labels = pd.read_csv(old_labels, sep='\t')
    new_scores = pd.read_csv(new_scores, sep='\t')
    new_labels = pd.read_csv(new_labels, sep='\t')
    print('Validating data')
    validator.validate_old_scores_dataset(old_scores)
    validator.validate_old_labels_dataset(old_labels)
    validator.validate_new_scores_dataset(new_scores)
    validator.validate_new_labels_dataset(new_labels)
    if new_scores.shape[0] != new_labels.shape[0]:
        warnings.warn('Score and label file of the new CAPICE model mismatch in size, attempting '
                      'to merge back together.')
        validator.validate_can_merge_new_scores(new_scores)
        validator.validate_can_merge_new_labels(new_labels)
        new_scores['merge_column']
        raise IncorrectFileError('Score and label file of the new CAPICE model should match in '
                                 'size!')
    print('Data passed, processing model data')

    print('All data loaded:')
    print(f'Amount of variants within the old CAPICE scores dataset: {old_scores.shape[0]}. '
          f'Columns: {old_scores.shape[1]}')
    print(f'Amount of variants within the old CAPICE labels dataset: {old_labels.shape[0]}. '
          f'Columns: {old_labels.shape[1]}')
    print(f'Amount of variants within the new CAPICE scores dataset" {new_scores.shape[0]}. '
          f'Columns: {new_scores.shape[1]}')
    print(f'Amount of variants within the new CAPICE labels dataset" {new_labels.shape[0]}. '
          f'Columns: {new_labels.shape[1]}')

    print('Merging datasets.')
    # Making merge column
    old_scores['merge_column'] = old_scores[
        ['chr_pos_ref_alt', 'GeneName']
    ].astype(str).agg(ID_SEPARATOR.join, axis=1)
    old_labels['merge_column'] = old_labels['ID']

    # Merging
    old_merged = old_scores.merge(old_labels, on='merge_column', how='left')

    new_merged = pd.concat(
        [
            new_scores,
            new_labels['binarized_label']
        ], axis=1
    )

    # Attempting to obtain the binarized_label for the old model datasets.
    try:
        old_merged['binarized_label'] = old_merged['ID'].str.split(ID_SEPARATOR, expand=True)[
            5].astype(float)
    except (ValueError, KeyError):
        raise IncorrectFileError(f'Could not separate the old labels file on the ID column! Is '
                                 f'this column up to date? (current string split: {ID_SEPARATOR})')
    print('Merging done.')

    print('Preparing plots.')
    # Preparing plots
    fig_auc = plt.figure(figsize=(20, 40))
    fig_auc.suptitle('Old model vs new model AUC comparison.')
    fig_vio = plt.figure(figsize=(20, 40))
    fig_vio.suptitle(
        f'Old model vs new model score distributions.\n'
        f'Old: {cadd_location}\n'
        f'New: {vep_location}')
    fig_box = plt.figure(figsize=(20, 40))
    fig_box.suptitle(
        f'Old model vs new model score closeness (difference to true label)\n'
        f'Old: {cadd_location}\n'
        f'New: {vep_location}')
    print('Preparation done.\n')

    print('Calculating global AUC.')
    # Calculating global AUC
    auc_old = round(roc_auc_score(merge['binarized_label'], merge['score_old']), 4)
    auc_new = round(roc_auc_score(merge['binarized_label'], merge['score_new']), 4)
    print(f'Global AUC calculated, old: {auc_old} and new: {auc_new}')

    print('Plotting global AUC.')
    # Plotting global AUC
    ax_auc = fig_auc.add_subplot(nrows, ncols, index)
    ax_auc.bar(1, auc_old, color='red', label=f'Old: {auc_old}')
    ax_auc.bar(2, auc_new, color='blue', label=f'New: {auc_new}')
    ax_auc.set_title(f'Global (n={merge.shape[0]})')
    ax_auc.set_xticks([1, 2], ['Old', 'New'])
    ax_auc.set_xlim(0.0, 3.0)
    ax_auc.set_ylim(0.0, 1.0)
    ax_auc.legend(loc='lower right')

    # Plotting Violinplot for global
    ax_vio = fig_vio.add_subplot(nrows, ncols, index)
    ax_vio.violinplot(merge[['score_old', 'binarized_label', 'score_new']])
    ax_vio.set_title(f'Global (n={merge.shape[0]})')
    ax_vio.set_xticks([1, 2, 3], ['Old', 'True', 'New'])
    ax_vio.set_xlim(0.0, 4.0)
    ax_vio.set_ylim(0.0, 1.0)

    # Plotting the score differences to the true label
    merge['score_diff_old'] = abs(merge['binarized_label'] - merge['score_old'])
    merge['score_diff_new'] = abs(merge['binarized_label'] - merge['score_new'])
    ax_box = fig_box.add_subplot(nrows, ncols, index)
    ax_box.boxplot(
        [
            merge[merge['binarized_label'] == 0]['score_diff_old'],
            merge[merge['binarized_label'] == 0]['score_diff_new'],
            merge[merge['binarized_label'] == 1]['score_diff_old'],
            merge[merge['binarized_label'] == 1]['score_diff_new']
        ], labels=['B_old', 'B_new', 'P_old', 'P_new']
    )
    ax_box.set_title(f'Global (n={merge.shape[0]})')
    print('Plotting global AUC done.')

    print('Plotting for each consequence:')
    # Global plots have been made, now for each consequence
    index = 2
    for consequence in consequences:
        print(f'Currently processing: {consequence}')
        # Subsetting
        subset = merge[merge['Consequence'] == consequence]

        # Calculating
        # Try except because when an consequence is encountered with only 1 label,
        # roc_auc_score will throw an error
        try:
            auc_old = round(roc_auc_score(subset['binarized_label'], subset['score_old']), 4)
        except ValueError:
            print(f'For consequence {consequence}, AUC old could not be calculated.')
            continue
        try:
            auc_new = round(roc_auc_score(subset['binarized_label'], subset['score_new']), 4)
        except ValueError:
            print(f'For consequence {consequence}, AUC new could not be calculated.')
            continue

        # Plotting auc
        ax_auc = fig_auc.add_subplot(nrows, ncols, index)
        ax_auc.bar(1, auc_old, color='red', label=f'Old: {auc_old}')
        ax_auc.bar(2, auc_new, color='blue', label=f'New: {auc_new}')
        ax_auc.set_title(f'{consequence} (n={subset.shape[0]})')
        ax_auc.set_xticks([1, 2], ['Old', 'New'])
        ax_auc.set_xlim(0.0, 3.0)
        ax_auc.set_ylim(0.0, 1.0)
        ax_auc.legend(loc='lower right')

        # Plotting Violinplot for global
        ax_vio = fig_vio.add_subplot(nrows, ncols, index)
        ax_vio.violinplot(subset[['score_old', 'binarized_label', 'score_new']])
        ax_vio.set_title(f'{consequence} (n={subset.shape[0]})')
        ax_vio.set_xticks([1, 2, 3], ['Old', 'True', 'New'])
        ax_vio.set_xlim(0.0, 4.0)
        ax_vio.set_ylim(0.0, 1.0)

        # Plotting boxplots
        ax_box = fig_box.add_subplot(nrows, ncols, index)
        ax_box.boxplot(
            [
                subset[subset['binarized_label'] == 0]['score_diff_old'],
                subset[subset['binarized_label'] == 0]['score_diff_new'],
                subset[subset['binarized_label'] == 1]['score_diff_old'],
                subset[subset['binarized_label'] == 1]['score_diff_new']
            ], labels=['B_old', 'B_new', 'P_old', 'P_new']
        )
        ax_box.set_title(f'{consequence} (n={subset.shape[0]})')

        index += 1

    print('Plotting for consequences done.\n')

    print('Plotting feature importances.')
    fig_table, ax_table = plt.subplots(figsize=(10, 20))
    fig_table.suptitle(f'Feature importances model: {model_location}')
    fig_table.patch.set_visible(False)
    ax_table.axis('off')
    ax_table.table(cellText=importances_dataframe.values, colLabels=importances_dataframe.columns,
                   loc='center')
    print('Plotting for feature importances done.\n')

    print(f'Exporting plots to: {output}')
    fig_auc.savefig(os.path.join(output, 'aucs.png'))
    fig_vio.savefig(os.path.join(output, 'violins.png'))
    fig_box.savefig(os.path.join(output, 'box.png'))
    fig_table.savefig(os.path.join(output, 'feature_importances.png'))
    print('Done.')


if __name__ == '__main__':
    main()

