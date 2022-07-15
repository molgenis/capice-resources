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
MERGE_COLUMNS = ['CHROM', 'POS', 'REF', 'ALT', 'SYMBOL']
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

        required.add_argument(
            '-s1',
            '--score_file_model_1',
            type=str,
            required=True,
            help='Input location of the file containing the scores for model 1. '
                 'Column `Consequence` is required to be present in either the score file or '
                 'the label file (or both). '
                 'Has to contain the `score` and column and '
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

    @staticmethod
    def validate_is_xgbclassifier(model):
        if not isinstance(model, xgb.XGBClassifier):
            raise DataError('Supplied model is not of an XGBClassifier class!')

    def validate_score_column_present(self, score_dataset: pd.DataFrame, model_number: int):
        self._validate_column_present(SCORE, score_dataset, SCORE, model_number)

    def validate_bl_column_present(self, label_dataset: pd.DataFrame, model_number: int):
        self._validate_column_present(BINARIZED_LABEL, label_dataset, 'label', model_number)

    @staticmethod
    def validate_consequence_column_present(scores_dataset, labels_dataset):
        has_consequence = True
        if 'Consequence' not in scores_dataset.columns and 'Consequence' not in \
                labels_dataset.columns:
            has_consequence = False
        return has_consequence

    @staticmethod
    def validate_merge_columns_present(model_dataset: pd.DataFrame, model_number: int):
        for col in MERGE_COLUMNS:
            if col not in model_dataset.columns:
                raise FileMismatchError(
                    f'Attempt to merge model {model_number} scores and labels failed, '
                    f'column: {col} is missing.'
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
    return pd.Series(splitted_consequences.values.ravel()).dropna().unique()


def main():
    print('Obtaining CLA')
    cla = CommandLineParser()
    m1_scores = cla.get_argument('score_file_model_1')
    m1_labels = cla.get_argument('label_file_model_1')
    m2_scores = cla.get_argument('score_file_model_2')
    m2_labels = cla.get_argument('label_file_model_1')
    output = cla.get_argument('output')
    print('Validating CLA')
    validator = Validator()
    validator.validate_is_gzipped_tsv(m1_scores)
    validator.validate_is_gzipped_tsv(m1_labels)
    validator.validate_is_gzipped_tsv(m2_scores)
    validator.validate_is_gzipped_tsv(m2_labels)
    validator.validate_output_argument(output)
    print('Input arguments passed.\n')

    print('Reading in data.')
    scores_model_1 = pd.read_csv(m1_scores, sep='\t', na_values='.')
    scores_model_1.columns = correct_column_names(scores_model_1.columns)
    validator.validate_score_column_present(scores_model_1, 1)
    labels_model_1 = pd.read_csv(m1_labels, sep='\t', na_values='.')
    labels_model_1.columns = correct_column_names(labels_model_1.columns)
    validator.validate_bl_column_present(labels_model_1, 1)
    m1_cons = validator.validate_consequence_column_present(scores_model_1, labels_model_1)
    if scores_model_1.shape[0] != labels_model_1.shape[0]:
        warnings.warn('Shapes for the different files for model 1 mismatch, attempting to merge.')
        validator.validate_merge_columns_present(scores_model_1, 1)
        validator.validate_merge_columns_present(labels_model_1, 1)
        scores_model_1['merge_column'] = scores_model_1[MERGE_COLUMNS].astype(str).agg(
            ID_SEPARATOR.join, axis=1)
        labels_model_1['merge_column'] = labels_model_1[MERGE_COLUMNS].astype(str).agg(
            ID_SEPARATOR.join, axis=1)
        m1 = scores_model_1.merge(labels_model_1, on='merge_column', how='left')
    else:
        m1 = pd.concat([scores_model_1, labels_model_1], axis=1)
    m1.drop(columns=m1.columns.difference(USE_COLUMNS), inplace=True)
    scores_model_2 = pd.read_csv(m2_scores, sep='\t', na_values='.')
    scores_model_2.columns = correct_column_names(scores_model_2.columns)
    validator.validate_score_column_present(scores_model_2, 2)
    labels_model_2 = pd.read_csv(m2_labels, sep='\t', na_values='.')
    labels_model_2.columns = correct_column_names(labels_model_2)
    validator.validate_bl_column_present(labels_model_2, 2)
    m2_cons = validator.validate_consequence_column_present(scores_model_2, labels_model_2)
    if scores_model_2.shape[0] != labels_model_2.shape[0]:
        warnings.warn('Shapes for the different files for model 2 mismatch, attempting to merge.')
        validator.validate_merge_columns_present(scores_model_2, 2)
        validator.validate_merge_columns_present(labels_model_2, 2)
        scores_model_2['merge_column'] = scores_model_2[MERGE_COLUMNS].astype(str).agg(
            ID_SEPARATOR.join, axis=1)
        labels_model_2['merge_column'] = labels_model_2[MERGE_COLUMNS].astype(str).agg(
            ID_SEPARATOR.join, axis=1)
        m2 = scores_model_2.merge(labels_model_2, on='merge_column', how='left')
    else:
        m2 = pd.concat([scores_model_2, labels_model_2], axis=1)
    m2.drop(columns=m2.columns.difference(USE_COLUMNS))
    process_consequences = True
    if not m1_cons and not m2_cons:
        warnings.warn('Encountered missing Consequence column. Disabling per-consequence '
                      'performance metrics.')
        process_consequences = False
    print('Data read.\n')

    print('Calculating stats')
    m1['score_diff'] = abs(m1[SCORE] - m1[BINARIZED_LABEL])
    m2['score_diff'] = abs(m2[SCORE] - m2[BINARIZED_LABEL])
    print('Stats calculated.\n')

    print('Preparing plots.')
    if process_consequences:
        processed_consequences = split_consequences(m1['Consequence'])
        ncols = 4
        nrows = math.ceil((len(processed_consequences) / ncols) + 1)
        figsize = (20, 40)
    else:
        processed_consequences = None
        ncols = 1,
        nrows = 1,
        figsize = (10, 15)  # Default values
    index = 1
    fig_auc = plt.figure(figsize=figsize)
    fig_auc.suptitle(
        f'Model 1 vs Model 2 Area Under Receiver Operator Curve\n'
        f'Model 1 scores: {m1_scores}\n'
        f'Model 1 labels: {m1_labels}\n'
        f'Model 2 scores: {m2_scores}\n'
        f'Model 2 labels: {m2_labels}\n'
    )
    fig_roc = plt.figure(figsize=(10, 15))
    fig_roc.suptitle(
        f'Model 1 vs Model 2 Receiver Operator Curves\n'
        f'Model 1 scores: {m1_scores}\n'
        f'Model 1 labels: {m1_labels}\n'
        f'Model 2 scores: {m2_scores}\n'
        f'Model 2 labels: {m2_labels}\n'
    )
    fig_score_dist = plt.figure(figsize=figsize)
    fig_score_dist.suptitle(
        f'Model 1 vs Model 2 raw CAPICE score distributions\n'
        f'Model 1 scores: {m1_scores}\n'
        f'Model 1 labels: {m1_labels}\n'
        f'Model 2 scores: {m2_scores}\n'
        f'Model 2 labels: {m2_labels}\n'
    )
    fig_score_diff = plt.figure(figsize=figsize)
    fig_score_diff.suptitle(
        f'Model 1 vs Model 2 absolute score difference to the true label\n'
        f'Model 1 scores: {m1_scores}\n'
        f'Model 1 labels: {m1_labels}\n'
        f'Model 2 scores: {m2_scores}\n'
        f'Model 2 labels: {m2_labels}\n'
        f'(M1B = Model 1 Benign, M1P = Model 1 Pathogenic, M2B = Model 2 Benign, M2P = Model 2 '
        f'Pathogenic)\n'
    )
    print('Plots prepared.\n')

    print('Generating global plots.')
    fpr_m1, tpr_m1, _ = roc_curve(m1[BINARIZED_LABEL], m1[SCORE])
    auc_m1 = round(auc(fpr_m1, tpr_m1), 4)
    fpr_m2, tpr_m2, _ = roc_curve(m2[BINARIZED_LABEL], m2[SCORE])
    auc_m2 = round(auc(fpr_m2, tpr_m2), 4)

    # Plotting ROCs
    ax_roc = fig_roc.add_subplot(1, 1, 1)
    ax_roc.plot(fpr_m1, tpr_m1, color='red', label=f'Model 1 (AUC={auc_m1})')
    ax_roc.plot(fpr_m2, tpr_m2, color='blue', label=f'Model 2 (AUC={auc_m2})')
    ax_roc.plot([0, 1], [0, 1], color='black', linestyle='--')
    ax_roc.set_xlim([0.0, 1.0])
    ax_roc.set_ylim([0.0, 1.0])
    ax_roc.set_xlabel('False Positive Rate')
    ax_roc.set_ylabel('True Positive Rate')
    ax_roc.legend(loc='lower right')

    # Plotting AUCs
    ax_auc = fig_auc.add_subplot(nrows, ncols, index)
    ax_auc.bar(1, auc_m1, color='red', label=f'Model 1: {auc_m1}\n'
                                             f'n: {m1.shape[0]}')
    ax_auc.bar(2, auc_m2, color='blue', label=f'Model 2: {auc_m2}\n'
                                              f'n: {m2.shape[0]}')
    ax_auc.set_title('Global')
    ax_auc.set_xticks([1, 2], ['Model 1', 'Model 2'])
    ax_auc.set_xlim(0.0, 3.0)
    ax_auc.set_ylim(0.0, 1.0)
    ax_auc.legend(loc='lower right')

    # Plotting raw scores
    ax_scores_dist = fig_score_dist.add_subplot(nrows, ncols, index)
    ax_scores_dist.boxplot(
        [
            m1[SCORE],
            m2[SCORE]
        ], labels=['Model 1', 'Model 2']
    )
    ax_scores_dist.set_title('Global')

    # Plotting score differences
    ax_scores_diff = fig_score_diff.add_subplot(nrows, ncols, index)
    ax_scores_diff.boxplot(
        [
            m1[m1[BINARIZED_LABEL] == 0]['score_diff'],
            m1[m1[BINARIZED_LABEL] == 1]['score_diff'],
            m2[m2[BINARIZED_LABEL] == 0]['score_diff'],
            m2[m2[BINARIZED_LABEL] == 1]['score_diff'],
        ], labels=['M1B', 'M1P', 'M2B', 'M2P']
    )

    index += 1

    print('Global plots generated.')

    if processed_consequences is not None:
        print('Generating per consequence plots.')
        for consequence in processed_consequences:
            subset_m1 = m1[m1['Consequence'].str.contains(consequence)]
            subset_m2 = m2[m2['Consequence'].str.contains(consequence)]

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

            # Plotting AUCs
            ax_auc = fig_auc.add_subplot(nrows, ncols, index)
            ax_auc.bar(1, auc_m1, color='red', label=f'Model 1: {auc_m1} (n={subset_m1.shape[0]})')
            ax_auc.bar(2, auc_m2, color='blue', label=f'Model 2: {auc_m2} (n={subset_m2.shape[0]})')
            ax_auc.set_title(f'{consequence}')
            ax_auc.set_xticks([1, 2], ['Model 1', 'Model 2'])
            ax_auc.set_xlim(0.0, 3.0)
            ax_auc.set_ylim(0.0, 1.0)
            ax_auc.legend(loc='lower right')

            # Plotting raw score distributions
            ax_scores_dist = fig_score_dist.add_subplot(nrows, ncols, index)
            ax_scores_dist.boxplot(
                [
                    subset_m1[SCORE],
                    subset_m2[SCORE]
                ], labels=['Model 1', 'Model 2']
            )
            ax_scores_dist.set_title(f'{consequence}')

            # Plotting the score differences to the true label
            ax_scores_diff = fig_score_diff.add_subplot(nrows, ncols, index)
            ax_scores_diff.boxplot(
                [
                    subset_m1[subset_m1[BINARIZED_LABEL] == 0]['score_diff'],
                    subset_m1[subset_m1[BINARIZED_LABEL] == 1]['score_diff'],
                    subset_m2[subset_m2[BINARIZED_LABEL] == 0]['score_diff'],
                    subset_m2[subset_m2[BINARIZED_LABEL] == 1]['score_diff']
                ], labels=['M1B', 'M1P', 'M2B', 'M2P']
            )
            ax_scores_diff.set_title(f'{consequence}')
            index += 1

    print(f'Plotting done! Exporting to: {output}')

    fig_roc.savefig(os.path.join(output, 'roc.png'))
    fig_auc.savefig(os.path.join(output, 'auc.png'))
    fig_score_dist.savefig(os.path.join(output, 'score_distributions.png'))
    fig_score_diff.savefig(os.path.join(output, 'score_differences.png'))


if __name__ == '__main__':
    main()
