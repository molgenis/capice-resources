#!/usr/bin/env python3

import os
import math
import typing
import argparse
import warnings

import numpy as np
import pandas as pd
import xgboost as xgb
from matplotlib import pyplot as plt
from sklearn.metrics import roc_auc_score

ID_SEPARATOR = '!'
MERGE_COLUMNS = ['CHROM', 'POS', 'REF', 'ALT', 'SYMBOL']
USE_COLUMNS = ['Consequence', 'score' , 'binarized_label']



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
                        'Please note that model 1 is leading for the per-consequence performance measurements. '
                        'If the size of the label file does not match the size of the scores file, an attempt will be '
                        'made to map the labels to the scores through the use of the columns: '
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
                 'Column `Consequence` is required to be present in either the score file or the label file (or both). '
                 'Has to contain the `score` and column and must be supplied in either TSV or gzipped TSV format! '
                 'Leading for per-consequence performance metrics.'
        )

        required.add_argument(
            '-l1',
            '--label_file_model_1',
            type=str,
            required=True,
            help='Input location of the file containing the labels for the model 1 score file. '
                 'Column `Consequence` is required to be present in either the score file or the label file (or both). '
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
                 'Column `Consequence` is required to be present in either the score file or the label file (or both). '
                 'Has to contain the `score` column and must be supplied in either TSV or gzipped TSV format!'
        )

        required.add_argument(
            '-l2',
            '--label_file_model_2',
            type=str,
            required=True,
            help='Input location of the file containing the labels for model 2. '
                 'Column `Consequence` is required to be present in either the score file or the label file (or both). '
                 'Has to contain the `binarized_label` column and must be supplied in either TSV or gzipped TSV format!'
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
        self._validate_column_present('score', score_dataset, 'score', model_number)

    def validate_bl_column_present(self, label_dataset: pd.DataFrame, model_number: int):
        self._validate_column_present('binarized_label', label_dataset, 'label', model_number)

    def validate_consequence_column_present(self, scores_dataset, labels_dataset, model_number):
        if not 'Consequence' in scores_dataset.columns and not 'Consequence' in labels_dataset.columns:
            raise IncorrectFileError(
                f'Required column Consequence not found in scores or labels dataset for model {model_number}'
            )

    @staticmethod
    def validate_merge_columns_present(model_dataset: pd.DataFrame, model_number: int):
        for col in MERGE_COLUMNS:
            if col not in model_dataset.columns:
                raise FileMismatchError(
                    f'Attempt to merge model {model_number} scores and labels failed, column: {col} is missing.'
                )

    @staticmethod
    def _validate_column_present(column: str, dataset: pd.DataFrame, type_file: str, model_number: int):
        if column not in dataset.columns:
            raise IncorrectFileError(f'The {type_file} file of model {model_number} does not contain {column}!')

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
    original_columns_sm1 = scores_model_1.columns
    scores_model_1.columns = correct_column_names(scores_model_1.columns)
    validator.validate_score_column_present(scores_model_1, 1)
    labels_model_1 = pd.read_csv(m1_labels, sep='\t', na_values='.')
    original_columns_lm1 = labels_model_1.columns
    labels_model_1.columns = correct_column_names(labels_model_1.columns)
    validator.validate_bl_column_present(labels_model_1, 1)
    validator.validate_consequence_column_present(scores_model_1, labels_model_1, 1)
    if scores_model_1.shape[0] != labels_model_1.shape[0]:
        warnings.warn('Shapes for the different files for model 1 mismatch, attempting to merge.')
        validator.validate_merge_columns_present(scores_model_1, 1)
        validator.validate_merge_columns_present(labels_model_1, 1)
        scores_model_1['merge_column'] = scores_model_1[MERGE_COLUMNS].astype(str).agg(ID_SEPARATOR.join, axis=1)
        labels_model_1['merge_column'] = labels_model_1[MERGE_COLUMNS].astype(str).agg(ID_SEPARATOR.join, axis=1)
        m1 = scores_model_1.merge(labels_model_1, on='merge_column', how='left')
    else:
        m1 = pd.concat([scores_model_1, labels_model_1], axis=1)
    m1.drop(columns=m1.columns.difference(USE_COLUMNS), inplace=True)
    scores_model_2 = pd.read_csv(m2_scores, sep='\t', na_values='.')
    original_columns_sm2 = scores_model_2.columns
    scores_model_2.columns = correct_column_names(scores_model_2.columns)
    validator.validate_score_column_present(scores_model_2, 2)
    labels_model_2 = pd.read_csv(m2_labels, sep='\t', na_values='.')
    original_columns_lm2 = labels_model_2.columns
    labels_model_2.columns = correct_column_names(labels_model_2)
    validator.validate_bl_column_present(labels_model_2)
    validator.validate_consequence_column_present(scores_model_2, labels_model_2, 2)
    if scores_model_2.shape[0] != labels_model_2.shape[0]:
        warnings.warn('Shapes for the different files for model 2 mismatch, attempting to merge.')
        validator.validate_merge_columns_present(scores_model_2, 2)
        validator.validate_merge_columns_present(labels_model_2, 2)
        scores_model_2['merge_column'] = scores_model_2[MERGE_COLUMNS].astype(str).agg(ID_SEPARATOR.join, axis=1)
        labels_model_2['merge_column'] = labels_model_2[MERGE_COLUMNS].astype(str).agg(ID_SEPARATOR.join, axis=1)
        m2 = scores_model_2.merge(labels_model_2, on='merge_column', how='left')
    else:
        m2 = pd.concat([scores_model_2, labels_model_2], axis=1)
    m2.drop(columns=m2.columns.difference(USE_COLUMNS))
    print('Data read.\n')

    print('Calculating stats')
    b_37_merged['binarized_label'] = b_37_merged['%ID'].str.split('_', expand=True)[5].astype(float)
    b_37_merged['score_diff'] = abs(b_37_merged['score'] - b_37_merged['binarized_label'])
    b_38_merged['binarized_label'] = b_38_merged['%ID'].str.split('_', expand=True)[5].astype(float)
    b_38_merged['score_diff'] = abs(b_38_merged['score'] - b_38_merged['binarized_label'])
    print('Stats calculated.\n')

    print('Processing the consequences. ')
    processed_cons = [
        'is_regulatory_region_variant',
        'is_regulatory_region_ablation',
        'is_regulatory_region_amplification',
        'is_missense_variant',
        'is_intron_variant',
        'is_upstream_gene_variant',
        'is_downstream_gene_variant',
        'is_synonymous_variant',
        'is_TF_binding_site_variant',
        'is_splice_donor_variant',
        'is_coding_sequence_variant',
        'is_splice_region_variant',
        'is_stop_gained',
        'is_splice_acceptor_variant',
        'is_frameshift_variant',
        'is_3_prime_UTR_variant',
        'is_inframe_insertion',
        'is_inframe_deletion',
        'is_5_prime_UTR_variant',
        'is_start_lost',
        'is_non_coding_transcript_exon_variant',
        'is_non_coding_transcript_variant',
        'is_TFBS_ablation',
        'is_TFBS_amplification',
        'is_protein_altering_variant',
        'is_stop_lost',
        'is_stop_retained_variant',
        'is_transcript_ablation',
        'is_intergenic_variant',
        'is_start_retained_variant',
        'is_transcript_amplification',
        'is_incomplete_terminal_codon_variant',
        'is_mature_miRNA_variant',
        'is_NMD_transcript_variant',
        'is_feature_elongation',
        'is_feature_truncation'
    ]
    splitted_consequences_37 = b_37_merged['%Consequence'].str.split('&', expand=True)
    splitted_consequences_38 = b_38_merged['%Consequence'].str.split('&', expand=True)
    processed_consequences = []
    for con in processed_cons:
        current_consequence = con.split('is_')[1]
        b_37_merged[con] = np.where(
            np.isin(splitted_consequences_37, current_consequence).any(axis=1), 1, 0
        )
        b_38_merged[con] = np.where(
            np.isin(splitted_consequences_38, current_consequence).any(axis=1), 1, 0
        )
        if not (b_37_merged[con] == 0).all() and not (b_38_merged[con] == 0).all():
            processed_consequences.append(con)
        else:
            print(f'Could not process {con}')

    print('Consequences processing done.')

    print('Preparing plots.')
    ncols = 4
    nrows = math.ceil((len(processed_consequences) / ncols) + 1)
    index = 1
    fig_auc = plt.figure(figsize=(20, 40))
    fig_auc.suptitle(
        f'Build 37 model vs build 38 model score distributions.')
    fig_box = plt.figure(figsize=(20, 40))
    fig_box.suptitle(
        f'Build 37 model vs build 38 model score closeness (difference to true label)')
    print('Plots prepared.\n')

    print('Calculating AUCs.')
    auc_37_global = round(roc_auc_score(
        y_true=b_37_merged['binarized_label'], y_score=b_37_merged['score']
    ), 4)
    auc_38_global = round(roc_auc_score(
        y_true=b_38_merged['binarized_label'], y_score=b_38_merged['score']
    ), 4)
    ax_auc = fig_auc.add_subplot(nrows, ncols, index)
    ax_auc.bar(1, auc_37_global, color='red', label=f'37: {auc_37_global}\n'
                                                    f'n: {b_37_merged.shape[0]}')
    ax_auc.bar(2, auc_38_global, color='blue', label=f'38: {auc_38_global}\n'
                                                     f'n: {b_38_merged.shape[0]}')
    ax_auc.set_title('Global')
    ax_auc.set_xticks([1, 2], ['37', '38'])
    ax_auc.set_xlim(0.0, 3.0)
    ax_auc.set_ylim(0.0, 1.0)
    ax_auc.legend(loc='lower right')

    ax_box = fig_box.add_subplot(nrows, ncols, index)
    ax_box.boxplot(
        [
            b_37_merged[b_37_merged['binarized_label'] == 0]['score_diff'],
            b_38_merged[b_38_merged['binarized_label'] == 0]['score_diff'],
            b_37_merged[b_37_merged['binarized_label'] == 1]['score_diff'],
            b_38_merged[b_38_merged['binarized_label'] == 1]['score_diff']
        ], labels=['B_37', 'B_38', 'P_37', 'P_38']
    )
    ax_box.set_title('Global')

    index += 1

    for consequence in processed_consequences:
        subset_37 = b_37_merged[b_37_merged[consequence] == 1]
        subset_38 = b_38_merged[b_38_merged[consequence] == 1]

        try:
            auc_37 = round(roc_auc_score(subset_37['binarized_label'], subset_37['score']), 4)
        except ValueError:
            print(f'Could not calculate AUC for 37 build for consequence: {consequence}')
            continue

        try:
            auc_38 = round(roc_auc_score(subset_38['binarized_label'], subset_38['score']), 4)
        except ValueError:
            print(f'Could not calculate AUC for 38 build for consequence: {consequence}')
            continue

        ax_auc = fig_auc.add_subplot(nrows, ncols, index)
        ax_auc.bar(1, auc_37, color='red', label=f'37: {auc_37} (n={subset_37.shape[0]})')
        ax_auc.bar(2, auc_38, color='blue', label=f'38: {auc_38} (n={subset_38.shape[0]})')
        ax_auc.set_title(f'{consequence}')
        ax_auc.set_xticks([1, 2], ['Old', 'New'])
        ax_auc.set_xlim(0.0, 3.0)
        ax_auc.set_ylim(0.0, 1.0)
        ax_auc.legend(loc='lower right')

        ax_box = fig_box.add_subplot(nrows, ncols, index)
        ax_box.boxplot(
            [
                subset_37[subset_37['binarized_label'] == 0]['score_diff'],
                subset_38[subset_38['binarized_label'] == 0]['score_diff'],
                subset_37[subset_37['binarized_label'] == 1]['score_diff'],
                subset_38[subset_38['binarized_label'] == 1]['score_diff']
            ], labels=['B_37', 'B_38', 'P_37', 'P_38']
        )
        ax_box.set_title(f'{consequence}')
        index += 1

    fig_box.savefig(os.path.join(output, 'box.png'))
    fig_auc.savefig(os.path.join(output, 'auc.png'))


if __name__ == '__main__':
    main()
