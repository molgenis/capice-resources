#!/usr/bin/env python3

import os
import math
import typing
import argparse
import warnings

import pandas as pd
import xgboost as xgb
from matplotlib import pyplot as plt
from sklearn.metrics import roc_auc_score, roc_curve, auc

ID_SEPARATOR = '!'
MERGE_COLUMNS_LABELS = ['CHROM', 'POS', 'REF', 'ALT', 'SYMBOL']
MERGE_COLUMNS_SCORES = ['chr', 'pos', 'ref', 'alt', 'gene_name']
USE_COLUMNS = ['Consequence', 'score', 'binarized_label']
BINARIZED_LABEL = 'binarized_label'
SCORE = 'score'


# Defining errors
class IncorrectFileError(Exception):
    pass


class DataError(Exception):
    pass


class FileMismatchError(Exception):
    pass


class SampleSizeMismatchError(Exception):
    pass


class CommandLineParser:
    def __init__(self):
        parser = self._create_argument_parser()
        self.arguments = parser.parse_args()

    def _create_argument_parser(self):
        parser = argparse.ArgumentParser(
            prog='Compare models',
            description='Compares the performance of 2 different XGBoost style models. '
                        'Please note that model 1 is leading for '
                        'the per-consequence performance measurements. '
                        'If the size of the label file does not match the size of the scores file, '
                        'an attempt will be made to map the labels to the '
                        'scores through the use of the columns: '
                        '`CHROM`, `POS`, `REF`, `ALT` and `SYMBOL`. '
                        'Will error if one of these columns is missing in either '
                        'the score file or the label file, assuming sizes differ.'
        )
        required = parser.add_argument_group('Required arguments')
        optional = parser.add_argument_group('Optional arguments')

        required.add_argument(
            '-s1',
            '--score_file_model_1',
            type=str,
            required=True,
            help='Input location of the file containing the scores for model 1. '
                 'Column `Consequence` is required to be present in either the score file or '
                 'the label file (or both). '
                 'Has to contain the `score` column and '
                 'must be supplied in either TSV or gzipped TSV format! '
                 'Leading for per-consequence performance metrics.'
        )

        required.add_argument(
            '-l1',
            '--label_file_model_1',
            type=str,
            required=True,
            help='Input location of the file containing the labels for the model 1 score file. '
                 'Column `Consequence` is required to be present in either the score file or '
                 'the label file (or both). '
                 'Has to contain the `binarized_label` column and '
                 'must be supplied in either TSV or gzipped TSV format! '
                 'Leading for per-consequence performance metrics.'
        )

        required.add_argument(
            '-s2',
            '--score_file_model_2',
            type=str,
            required=True,
            help='Input location of the file containing the scores for model 2. '
                 'Column `Consequence` is required to be present in either the score file or '
                 'the label file (or both). '
                 'Has to contain the `score` column and '
                 'must be supplied in either TSV or gzipped TSV format!'
        )

        required.add_argument(
            '-l2',
            '--label_file_model_2',
            type=str,
            required=True,
            help='Input location of the file containing the labels for model 2. '
                 'Column `Consequence` is required to be present in either the score file or '
                 'the label file (or both). '
                 'Has to contain the `binarized_label` column and '
                 'must be supplied in either TSV or gzipped TSV format!'
        )

        required.add_argument(
            '-o',
            '--output',
            type=str,
            required=True,
            help='Output directory.'
        )

        optional.add_argument(
            '-f',
            '--force_merge',
            action='store_true',
            help='Add flag if there is a possibility of a mismatch in sample size between the '
                 'score and label file for any model.'
        )

        return parser

    def get_argument(self, argument_key):
        value = None
        if argument_key in self.arguments:
            value = getattr(self.arguments, argument_key)
        return value


class Validator:
    @staticmethod
    def validate_is_gzipped_tsv(path: str):
        extensions = ('.tsv', '.tsv.gz')
        if not path.endswith(extensions):
            raise IncorrectFileError(f'Input path {path} does not meet the required extension: '
                                     f'{", ".join(extensions)}')

    def validate_score_column_present(self, score_dataset: pd.DataFrame, model_number: int):
        self._validate_column_present(SCORE, score_dataset, SCORE, model_number)

    def validate_bl_column_present(self, label_dataset: pd.DataFrame, model_number: int):
        self._validate_column_present(BINARIZED_LABEL, label_dataset, 'label', model_number)

    @staticmethod
    def validate_consequence_column_present(labels_dataset):
        has_consequence = True
        if 'Consequence' not in labels_dataset.columns:
            has_consequence = False
        return has_consequence

    @staticmethod
    def validate_merge_columns_present_labels(labels_dataset: pd.DataFrame, model_number: int):
        for col in MERGE_COLUMNS_LABELS:
            if col not in labels_dataset.columns:
                raise FileMismatchError(
                    f'Attempt to merge model {model_number} scores and labels failed, '
                    f'column: {col} is missing in the labels dataset.'
                )

    @staticmethod
    def validate_merge_columns_present_scores(scores_dataset: pd.DataFrame, model_number: int):
        for col in MERGE_COLUMNS_SCORES:
            if col not in scores_dataset.columns:
                raise FileMismatchError(
                    f'Attempt to merge model {model_number} scores and labels failed, '
                    f'column: {col} is missing in the scores dataset.'
                )

    @staticmethod
    def _validate_column_present(column: str, dataset: pd.DataFrame, type_file: str,
                                 model_number: int):
        if column not in dataset.columns:
            raise IncorrectFileError(
                f'The {type_file} file of model {model_number} does not contain {column}!'
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


def correct_column_names(columns: typing.Iterable):
    processed_columns = []
    for column in columns:
        if column.startswith('%'):
            processed_columns.append(column.split('%')[1])
        else:
            processed_columns.append(column)
    return processed_columns


def split_consequences(consequences: pd.Series):
    splitted_consequences = consequences.str.split('&', expand=True)
    return pd.Series(splitted_consequences.values.ravel()).dropna().sort_values(
        ignore_index=True).unique()


def prepare_data_file(validator, scores, labels, model_number, force_merge):
    scores_model = pd.read_csv(scores, sep='\t', na_values='.')
    scores_model.columns = correct_column_names(scores_model.columns)
    validator.validate_score_column_present(scores_model, model_number)
    labels_model = pd.read_csv(labels, sep='\t', na_values='.')
    labels_model.columns = correct_column_names(labels_model.columns)
    validator.validate_bl_column_present(labels_model, model_number)
    m_cons = validator.validate_consequence_column_present(labels_model)
    if scores_model.shape[0] == labels_model.shape[0]:
        model = pd.concat([scores_model, labels_model], axis=1)
    else:
        if force_merge:
            warnings.warn(f'Sample sizes for the different files for model {model_number} '
                          f'mismatch, however -f flag is supplied, attempting to merge.')
            validator.validate_merge_columns_present_scores(scores_model, model_number)
            validator.validate_merge_columns_present_labels(labels_model, model_number)
            scores_model['merge_column'] = scores_model[MERGE_COLUMNS_SCORES].astype(str).agg(
                ID_SEPARATOR.join, axis=1)
            labels_model['merge_column'] = labels_model[MERGE_COLUMNS_LABELS].astype(str).agg(
                ID_SEPARATOR.join, axis=1)
            model = scores_model.merge(labels_model, on='merge_column', how='left')
            print('Merge successful.')
        else:
            raise SampleSizeMismatchError(f'Sample sizes for the different files for model '
                                          f'{model_number} mismatch and flag -f is not supplied!')
    model.drop(columns=model.columns.difference(USE_COLUMNS), inplace=True)

    return model, m_cons


def process_cla(validator):
    print('Obtaining CLA.')
    cla = CommandLineParser()
    m1_scores = cla.get_argument('score_file_model_1')
    m1_labels = cla.get_argument('label_file_model_1')
    m2_scores = cla.get_argument('score_file_model_2')
    m2_labels = cla.get_argument('label_file_model_2')
    force_merge = cla.get_argument('force_merge')
    output = cla.get_argument('output')

    print('Validating CLA.')
    validator.validate_is_gzipped_tsv(m1_scores)
    validator.validate_is_gzipped_tsv(m1_labels)
    validator.validate_is_gzipped_tsv(m2_scores)
    validator.validate_is_gzipped_tsv(m2_labels)
    validator.validate_output_argument(output)
    print('Input arguments passed.\n')
    return m1_scores, m1_labels, m2_scores, m2_labels, force_merge, output


def calculate_score_difference(merged_dataset):
    merged_dataset['score_diff'] = abs(merged_dataset[SCORE] - merged_dataset[BINARIZED_LABEL])


class Plotter:
    def __init__(self, process_consequences):
        self.process_consequences = process_consequences
        self.index = 1
        self.fig_auc = plt.figure()
        self.fig_roc = plt.figure()
        self.fig_score_dist = plt.figure()
        self.fig_score_diff = plt.figure()
        self.consequences = []
        self.n_rows = 1
        self.n_cols = 1

    def prepare_plots(self, model_1_score_path, model_1_label_path, model_2_score_path,
                      model_2_label_path):
        print('Preparing plot figures.')
        if self.process_consequences:
            figsize = (20, 40)
        else:
            figsize = (10, 15)  # Default values
        print('Preparing plots.')
        self.fig_auc = plt.figure(figsize=figsize)
        self.fig_auc.suptitle(
            f'Model 1 vs Model 2 Area Under Receiver Operator Curve\n'
            f'Model 1 scores: {model_1_score_path}\n'
            f'Model 1 labels: {model_1_label_path}\n'
            f'Model 2 scores: {model_2_score_path}\n'
            f'Model 2 labels: {model_2_label_path}\n'
        )
        self.fig_roc = plt.figure(figsize=(10, 15))
        self.fig_roc.suptitle(
            f'Model 1 vs Model 2 Receiver Operator Curves\n'
            f'Model 1 scores: {model_1_score_path}\n'
            f'Model 1 labels: {model_1_label_path}\n'
            f'Model 2 scores: {model_2_score_path}\n'
            f'Model 2 labels: {model_2_label_path}\n'
        )
        self.fig_score_dist = plt.figure(figsize=figsize)
        self.fig_score_dist.suptitle(
            f'Model 1 vs Model 2 raw CAPICE score distributions\n'
            f'Model 1 scores: {model_1_score_path}\n'
            f'Model 1 labels: {model_1_label_path}\n'
            f'Model 2 scores: {model_2_score_path}\n'
            f'Model 2 labels: {model_2_label_path}\n'
            f'(M1B = Model 1 Benign, M1P = Model 1 Pathogenic, M2B = Model 2 Benign, M2P = Model 2 '
            f'Pathogenic)\n'
        )
        self.fig_score_diff = plt.figure(figsize=figsize)
        self.fig_score_diff.suptitle(
            f'Model 1 vs Model 2 absolute score difference to the true label\n'
            f'Model 1 scores: {model_1_score_path}\n'
            f'Model 1 labels: {model_1_label_path}\n'
            f'Model 2 scores: {model_2_score_path}\n'
            f'Model 2 labels: {model_2_label_path}\n'
            f'(M1B = Model 1 Benign, M1P = Model 1 Pathogenic, M2B = Model 2 Benign, M2P = Model 2 '
            f'Pathogenic)\n'
        )
        print('Plot figures prepared.\n')

    def prepare_subplots(self, merged_model_1_data):
        if self.process_consequences:
            print(
                'Creating required amount of rows and columns according to present Consequences.\n'
            )
            self.consequences = split_consequences(merged_model_1_data['Consequence'])
            self.n_cols = 4
            self.n_rows = math.ceil((len(self.consequences) / self.n_cols) + 1)
        else:
            print('Creating single plot per figure.\n')

    def plot(self, merged_model_1_data, merged_model_2_data):
        print('Calculating global TPR, FPR and AUC.')
        fpr_m1, tpr_m1, _ = roc_curve(
            merged_model_1_data[BINARIZED_LABEL], merged_model_1_data[SCORE]
        )
        auc_m1 = round(auc(fpr_m1, tpr_m1), 4)
        fpr_m2, tpr_m2, _ = roc_curve(
            merged_model_2_data[BINARIZED_LABEL], merged_model_2_data[SCORE]
        )
        auc_m2 = round(auc(fpr_m2, tpr_m2), 4)
        print('TPR, FPR and AUC calculated globally.\n')

        print('Plotting global ROC, AUC, Score distributions and Score differences.')
        self._plot_roc(fpr_m1, tpr_m1, auc_m1, fpr_m2, tpr_m2, auc_m2)
        self._plot_auc(auc_m1, merged_model_1_data.shape[0], auc_m2, merged_model_2_data.shape[
            0], 'Global')
        self._plot_score_dist(merged_model_1_data, merged_model_2_data, 'Global')
        self._plot_score_diff(merged_model_1_data, merged_model_2_data, 'Global')
        print('Plotting globally done.\n')
        if self.process_consequences:
            print('Plotting per consequence.')
            self.index += 1
            self._plot_consequences(merged_model_1_data, merged_model_2_data)
            print('Plotting per consequence done.\n')

    def _plot_consequences(self, merged_model_1_data, merged_model_2_data):
        for consequence in self.consequences:
            subset_m1 = merged_model_1_data[
                merged_model_1_data['Consequence'].str.contains(consequence)]
            subset_m2 = merged_model_2_data[
                merged_model_2_data['Consequence'].str.contains(consequence)]
            try:
                auc_m1 = round(
                    roc_auc_score(
                        subset_m1[BINARIZED_LABEL],
                        subset_m1[SCORE]
                    ),
                    4
                )
            except ValueError:
                print(f'Could not calculate AUC for Model 1 for consequence: {consequence}')
                continue

            try:
                auc_m2 = round(
                    roc_auc_score(
                        subset_m2[BINARIZED_LABEL],
                        subset_m2[SCORE]
                    ),
                    4
                )
            except ValueError:
                print(f'Could not calculate AUC for Model 2 for consequence: {consequence}')
                continue

            self._plot_auc(
                auc_m1, merged_model_1_data.shape[0], auc_m2, merged_model_2_data.shape[0],
                consequence
            )
            self._plot_score_dist(merged_model_1_data, merged_model_2_data, consequence)
            self._plot_score_diff(merged_model_1_data, merged_model_2_data, consequence)
            self.index += 1

    def _plot_roc(self, fpr_model_1, tpr_model_1, auc_model_1, fpr_model_2, tpr_model_2,
                  auc_model_2):
        # Plotting ROCs
        ax_roc = self.fig_roc.add_subplot(1, 1, 1)
        ax_roc.plot(fpr_model_1, tpr_model_1, color='red', label=f'Model 1 (AUC={auc_model_1})')
        ax_roc.plot(fpr_model_2, tpr_model_2, color='blue', label=f'Model 2 (AUC={auc_model_2})')
        ax_roc.plot([0, 1], [0, 1], color='black', linestyle='--')
        ax_roc.set_xlim([0.0, 1.0])
        ax_roc.set_ylim([0.0, 1.0])
        ax_roc.set_xlabel('False Positive Rate')
        ax_roc.set_ylabel('True Positive Rate')
        ax_roc.legend(loc='lower right')

    def _plot_auc(self, auc_model_1, model_1_n_samples, auc_model_2, model_2_n_samples, title):
        # Plotting AUCs
        ax_auc = self.fig_auc.add_subplot(self.n_rows, self.n_cols, self.index)
        ax_auc.bar(1, auc_model_1, color='red', label=f'Model 1: {auc_model_1}\n'
                                                      f'n: {model_1_n_samples}')
        ax_auc.bar(2, auc_model_2, color='blue', label=f'Model 2: {auc_model_2}\n'
                                                       f'n: {model_2_n_samples}')
        ax_auc.set_title(title)
        ax_auc.set_xticks([1, 2], ['Model 1', 'Model 2'])
        ax_auc.set_xlim(0.0, 3.0)
        ax_auc.set_ylim(0.0, 1.0)
        ax_auc.legend(loc='lower right')

    def _plot_score_dist(self, model_1_data, model_2_data, title):
        # Plotting raw scores
        ax_scores_dist = self.fig_score_dist.add_subplot(self.n_rows, self.n_cols, self.index)
        ax_scores_dist.boxplot(
            [
                model_1_data[model_1_data[BINARIZED_LABEL] == 0][SCORE],
                model_1_data[model_1_data[BINARIZED_LABEL] == 1][SCORE],
                model_2_data[model_2_data[BINARIZED_LABEL] == 0][SCORE],
                model_2_data[model_2_data[BINARIZED_LABEL] == 1][SCORE],
            ], labels=['M1B', 'M1P', 'M2B', 'M2P']
        )
        ax_scores_dist.set_ylim(0.0, 1.0)
        ax_scores_dist.set_title(title)

    def _plot_score_diff(self, model_1_data, model_2_data, title):
        # Plotting score differences
        ax_scores_diff = self.fig_score_diff.add_subplot(self.n_rows, self.n_cols, self.index)
        ax_scores_diff.boxplot(
            [
                model_1_data[model_1_data[BINARIZED_LABEL] == 0]['score_diff'],
                model_1_data[model_1_data[BINARIZED_LABEL] == 1]['score_diff'],
                model_2_data[model_2_data[BINARIZED_LABEL] == 0]['score_diff'],
                model_2_data[model_2_data[BINARIZED_LABEL] == 1]['score_diff'],
            ], labels=['M1B', 'M1P', 'M2B', 'M2P']
        )
        ax_scores_diff.set_ylim(0.0, 1.0)
        ax_scores_diff.set_title(title)

    def export(self, output):
        print(f'Exporting figures to: {output}')
        self.fig_roc.savefig(os.path.join(output, 'roc.png'))
        self.fig_auc.savefig(os.path.join(output, 'auc.png'))
        self.fig_score_dist.savefig(os.path.join(output, 'score_distributions.png'))
        self.fig_score_diff.savefig(os.path.join(output, 'score_differences.png'))
        print('Export done.')


def main():
    # Processing and validating CLA
    validator = Validator()
    m1_scores, m1_labels, m2_scores, m2_labels, force_merge, output = process_cla(validator)

    # Reading in data and validating data
    m1, m1_cons = prepare_data_file(validator, m1_scores, m1_labels, 1, force_merge)
    m2, m2_cons = prepare_data_file(validator, m2_scores, m2_labels, 2, force_merge)

    # Turning processing of consequences on or off based on presence of Consequence column
    process_consequences = True
    if not m1_cons or not m2_cons:
        warnings.warn('Encountered missing Consequence column. Disabling per-consequence '
                      'performance metrics.')
        process_consequences = False

    # Calculating score differences
    calculate_score_difference(m1)
    calculate_score_difference(m2)

    # Plotting
    plotter = Plotter(process_consequences)
    plotter.prepare_plots(m1_scores, m1_labels, m2_scores, m2_labels)
    plotter.prepare_subplots(m1)
    plotter.plot(m1, m2)
    plotter.export(output)


if __name__ == '__main__':
    main()
