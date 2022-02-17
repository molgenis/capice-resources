#!/usr/bin/env python3

import os
import argparse
import warnings

import math
import pickle
import pandas as pd
from matplotlib import pyplot as plt
from sklearn.metrics import roc_auc_score


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
            prog='Make VEP TSV train ready',
            description='Converts an VEP output TSV (after conversion) to make it train ready.'
                        'PLEASE NOTE: This script does NOT validate your input!'
        )
        required = parser.add_argument_group('Required arguments')

        required.add_argument(
            '--old_model_results',
            type=str,
            required=True,
            help='Input location of the results file generated with the old CAPICE model '
                 '(XGBoost >= 0.90). Has to be a (gzipped) tsv!'
        )

        required.add_argument(
            '--new_model_results',
            type=str,
            required=True,
            help='Input location of the results file generated with the new CAPICE model '
                 '(XGBoost == 1.4.2). Has to be a gzipped tsv!'
        )

        required.add_argument(
            '--vep_processed_capice_input',
            type=str,
            required=True,
            help='Input location of the new CAPICE (XGBoost == 1.4.2) input TSV, processed using '
                 'the -t flag in the conversion script. Has to be a gzipped tsv!'
        )

        required.add_argument(
            '--new_model',
            type=str,
            required=True,
            help='Input location of the XGBoost == 1.4.2 model. Has to be a .pickle.dat!'
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

    def validate_old_input_argument(self, old_input_path):
        self._validate_argument(old_input_path, ('.tsv', '.tsv.gz'))

    def validate_ol_input_argument(self, ol_input_path):
        self._validate_argument(ol_input_path, '.tsv.gz')

    def validate_new_input_argument(self, new_input_path):
        self._validate_argument(new_input_path, '.tsv.gz')

    def validate_model_input_argument(self, model_input_path):
        self._validate_argument(model_input_path, '.pickle.dat')

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

    def validate_old_dataset(self, data):
        required_columns = ['chr_pos_ref_alt', 'GeneName', 'probabilities']
        self._validate_dataframe(data, required_columns, 'Old CAPICE generated dataset')

    def validate_ol_dataset(self, data):
        required_columns = ['%ID']
        self._validate_dataframe(data, required_columns, 'Original labels dataset')

    def validate_new_dataset(self, data):
        required_columns = ['score', 'chr', 'pos', 'ref', 'alt', 'gene_name']
        self._validate_dataframe(data, required_columns, 'New CAPICE generated dataset')

    @staticmethod
    def _validate_dataframe(data, required_columns, dataset):
        for column in required_columns:
            if column not in data.columns:
                raise DataError(f'Required column {column} not found in: {dataset}!')


def main():
    print('Obtaining command line arguments')
    cla = CommandLineDigest()
    cadd_location = cla.get_argument('old_model_results')
    ol_location = cla.get_argument('vep_processed_capice_input')
    vep_location = cla.get_argument('new_model_results')
    model_location = cla.get_argument('new_model')
    output = cla.get_argument('output')
    print('Validating command line arguments')
    validator = Validator()
    validator.validate_old_input_argument(cadd_location)
    validator.validate_ol_input_argument(ol_location)
    validator.validate_new_input_argument(vep_location)
    validator.validate_model_input_argument(model_location)
    validator.validate_output_argument(output)
    print('Arguments passed\n')

    # Reading in data
    print('Reading data')
    cadd = pd.read_csv(cadd_location, sep='\t')
    original_labels = pd.read_csv(ol_location, sep='\t')
    vep = pd.read_csv(vep_location, sep='\t')
    print('Validating data')
    validator.validate_old_dataset(cadd)
    validator.validate_ol_dataset(original_labels)
    validator.validate_new_dataset(vep)
    print('Data passed, processing model data')

    with open(model_location, 'rb') as model_file:
        model = pickle.load(model_file)
    importances = model.get_booster().get_score(importance_type='gain')
    importances_dataframe = pd.DataFrame(data=list(importances.values()),
                                         index=list(importances.keys()),
                                         columns=['score']).sort_values(by='score', ascending=False)
    importances_dataframe['feature'] = importances_dataframe.index
    importances_dataframe.reset_index(drop=True, inplace=True)
    print('All data loaded:')
    print(f'Amount of variants within old CAPICE generated dataset: {cadd.shape[0]}. '
          f'Columns: {cadd.shape[1]}')
    print(f'Amount of variants within the original labels dataset: {original_labels.shape[0]}. '
          f'Columns: {original_labels.shape[1]}')
    print(f'Amount of variants within new CAPICE generated dataset '
          f'(should match the original labels dataset!): {vep.shape[0]}. '
          f'Columns: {vep.shape[1]}\n')

    print('Starting making merge columns.')
    # Making merge column
    cadd['ID'] = cadd[['chr_pos_ref_alt', 'GeneName']].astype(str).agg('_'.join, axis=1)
    vep['ID'] = vep[['chr', 'pos', 'ref', 'alt', 'gene_name']].astype(str).agg('_'.join, axis=1)

    # Getting the true original labels
    original_labels['binarized_label'] = original_labels['%ID'].str.split('_', expand=True)[
        5].astype(float)
    original_labels['ID'] = original_labels['%ID'].str.split('_', expand=True).loc[:, :4].astype(
        str).agg('_'.join, axis=1)
    print('Merge columns made, starting cleaning.')

    # Preparing all datasets
    vep = vep[['ID', 'score']]
    vep._is_copy = None
    vep.rename(columns={'score': 'score_new'}, inplace=True)
    cadd.rename(columns={'probabilities': 'score_old'}, inplace=True)
    original_labels = original_labels[['ID', 'binarized_label']]
    original_labels._is_copy = None
    print('Cleaning done.\n')

    print('Starting merge.')
    # Merging
    merge = cadd.merge(original_labels, on='ID', how='left')
    merge.drop(index=merge[merge['binarized_label'].isnull()].index, inplace=True)
    merge = merge.merge(vep, on='ID', how='left')
    merge.drop(index=merge[merge['score_new'].isnull()].index, inplace=True)
    print(f'Merge done. Merge has {merge.shape[0]} variants.\n')

    print('Preparing plots.')
    # Preparing plots
    consequences = merge['Consequence'].unique()
    ncols = 4
    nrows = math.ceil((consequences.size / ncols) + 1)
    index = 1
    fig_auc = plt.figure(figsize=(20, 40))
    fig_auc.suptitle(
        f'Old model vs new model AUC comparison.\n'
        f'Old: {cadd_location}\n'
        f'New: {vep_location}')
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

