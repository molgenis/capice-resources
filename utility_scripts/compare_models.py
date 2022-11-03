#!/usr/bin/env python3

import os
import math
import argparse
import warnings

import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from matplotlib import patches as mpatches
from sklearn.metrics import roc_auc_score, roc_curve

ID_SEPARATOR = '!'
MERGE_COLUMNS_LABELS = ['CHROM', 'POS', 'REF', 'ALT', 'SYMBOL']
MERGE_COLUMNS_SCORES = ['chr', 'pos', 'ref', 'alt', 'gene_name']
USE_COLUMNS = ['Consequence', 'score', 'binarized_label', 'gnomAD_AF']
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

    def validate_af_column_present(self, label_dataset: pd.DataFrame, model_number: int):
        self._validate_column_present('gnomAD_AF', label_dataset, 'label', model_number)

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
                print(f'Error encountered creating output path: {e}')
                exit(1)

    @staticmethod
    def validate_score_files_length(m1, m2, per_consequence):
        if m1.shape[0] != m2.shape[0]:
            warnings.warn('The score files contain a different number of variants.')
        if per_consequence:
            unequal_variants_consequence = []
            for consequence in split_consequences(m1['Consequence']):
                m1_consequence = m1[m1['Consequence'].str.contains(consequence)]
                m2_consequence = m2[m2['Consequence'].str.contains(consequence)]
                if m1_consequence.shape[0] != m2_consequence.shape[0]:
                    unequal_variants_consequence.append(consequence)
            if len(unequal_variants_consequence) > 0:
                unequal_variants_consequence_string = ', '.join(unequal_variants_consequence)
                warnings.warn(f'The score files contain a different number of variants for the '
                              f'consequences: {unequal_variants_consequence_string}')


def split_consequences(consequences: pd.Series):
    splitted_consequences = consequences.str.split('&', expand=True)
    return pd.Series(splitted_consequences.values.ravel()).dropna().sort_values(
        ignore_index=True).unique()


def prepare_data_file(validator, scores, labels, model_number, force_merge):
    scores_model = pd.read_csv(scores, sep='\t', na_values='.')
    validator.validate_score_column_present(scores_model, model_number)
    labels_model = pd.read_csv(labels, sep='\t', na_values='.')
    validator.validate_bl_column_present(labels_model, model_number)
    validator.validate_af_column_present(labels_model, model_number)
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


def add_imputed_af(merged_dataset):
    merged_dataset['is_imputed'] = False
    merged_dataset.loc[merged_dataset['gnomAD_AF'].isnull(), 'is_imputed'] = True


def add_model_identifier(dataset, model_number):
    dataset['model'] = model_number


def calculate_auc(dataset: pd.DataFrame):
    return round(roc_auc_score(y_true=dataset[BINARIZED_LABEL], y_score=dataset[SCORE]), 4)


def calculate_roc(dataset: pd.DataFrame):
    fpr, tpr, _ = roc_curve(y_true=dataset[BINARIZED_LABEL], y_score=dataset[SCORE])
    return fpr, tpr, calculate_auc(dataset)


class Plotter:
    def __init__(self, process_consequences):
        self.process_consequences = process_consequences
        self.index = 1
        self.fig_auc = plt.figure()
        self.fig_roc = plt.figure()
        self.fig_afb = plt.figure()
        self.fig_score_dist = plt.figure()
        self.fig_score_diff = plt.figure()
        self.consequences = []
        self.n_rows = 1
        self.n_cols = 1

    @staticmethod
    def _set_figure_size(process_consequences):
        if process_consequences:
            return 20, 40
        else:
            return 10, 15

    def prepare_plots(self, model_1_score_path, model_1_label_path, model_2_score_path,
                      model_2_label_path):
        print('Preparing plot figures.')
        figsize = self._set_figure_size(self.process_consequences)
        constrained_layout = {'w_pad': 0.2, 'h_pad': 0.2}
        print('Preparing plots.')
        self.fig_auc = plt.figure(figsize=figsize)
        self.fig_auc.suptitle(
            f'Model 1 vs Model 2 Area Under Receiver Operator Curve\n'
            f'Model 1 scores: {model_1_score_path}\n'
            f'Model 1 labels: {model_1_label_path}\n'
            f'Model 2 scores: {model_2_score_path}\n'
            f'Model 2 labels: {model_2_label_path}\n'
        )
        self.fig_auc.set_constrained_layout(constrained_layout)
        self.fig_roc = plt.figure(figsize=(10, 15))
        self.fig_roc.suptitle(
            f'Model 1 vs Model 2 Receiver Operator Curves\n'
            f'Model 1 scores: {model_1_score_path}\n'
            f'Model 1 labels: {model_1_label_path}\n'
            f'Model 2 scores: {model_2_score_path}\n'
            f'Model 2 labels: {model_2_label_path}\n'
        )
        self.fig_roc.set_constrained_layout(constrained_layout)
        self.fig_afb = plt.figure(figsize=(11, 11))
        self.fig_afb.suptitle(
            f'Model 1 vs Model 2 Allele Frequency bins performance comparison\n'
            f'Model 1 scores: {model_1_score_path}\n'
            f'Model 1 labels: {model_1_label_path}\n'
            f'Model 2 scores: {model_2_score_path}\n'
            f'Model 2 labels: {model_2_label_path}\n'
        )
        self.fig_afb.set_constrained_layout(constrained_layout)
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
        self.fig_score_dist.set_constrained_layout(constrained_layout)
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
        self.fig_score_diff.set_constrained_layout(constrained_layout)
        print('Plot figures prepared.\n')

    def prepare_subplots(self, merged_model_1_data):
        if self.process_consequences:
            print(
                'Creating required amount of rows and columns according to present Consequences.\n'
            )
            self.consequences = split_consequences(merged_model_1_data['Consequence'])
            self.n_cols = 3
            self.n_rows = math.ceil((len(self.consequences) / self.n_cols + 1))
        else:
            print('Creating single plot per figure.\n')

    def plot(self, merged_model_1_data, merged_model_2_data):
        m1_samples = merged_model_1_data.shape[0]
        m2_samples = merged_model_2_data.shape[0]

        print('Plotting global ROC, AUC, AF Bins, Score distributions and Score differences.')
        self._plot_roc_auc_afbins(merged_model_1_data, m1_samples, merged_model_2_data, m2_samples)
        self._plot_score_dist(merged_model_1_data, m1_samples, merged_model_2_data, m2_samples,
                              'Global')
        self._plot_score_diff(merged_model_1_data, m1_samples, merged_model_2_data, m2_samples,
                              'Global')
        print('Plotting globally done.\n')
        if self.process_consequences:
            print('Plotting per consequence.')
            self.index += 1
            self._plot_consequences(merged_model_1_data, merged_model_2_data)
            print('Plotting per consequence done.\n')

    def _plot_roc_auc_afbins(self, model_1_data, model_1_samples, model_2_data, model_2_samples):
        fpr_m1, tpr_m1, auc_m1 = calculate_roc(model_1_data)
        fpr_m2, tpr_m2, auc_m2 = calculate_roc(model_2_data)
        self._plot_roc(fpr_m1, tpr_m1, auc_m1, fpr_m2, tpr_m2, auc_m2)
        self._plot_auc(auc_m1, model_1_samples, auc_m2, model_2_samples, 'Global')
        self._plot_af_bins(model_1_data, model_2_data)

    @staticmethod
    def _subset_consequence(dataset, consequence):
        return dataset[dataset['Consequence'].str.contains(consequence)]

    def _plot_consequences(self, merged_model_1_data, merged_model_2_data):
        for consequence in self.consequences:
            subset_m1 = self._subset_consequence(merged_model_1_data, consequence)
            m1_samples = subset_m1.shape[0]
            subset_m2 = self._subset_consequence(merged_model_2_data, consequence)
            m2_samples = subset_m2.shape[0]
            try:
                auc_m1 = calculate_auc(subset_m1)
                auc_m2 = calculate_auc(subset_m2)
            except ValueError:
                auc_m1 = np.NaN
                auc_m2 = np.NaN

            self._plot_auc(auc_m1, m1_samples, auc_m2, m2_samples, consequence)
            self._plot_score_dist(subset_m1, m1_samples, subset_m2, m2_samples, consequence)
            self._plot_score_diff(subset_m1, m1_samples, subset_m2, m2_samples, consequence)
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

    @staticmethod
    def _create_af_bins_plotlabels(bin_label, model_1_size: int, model_1_auc: float,
                                   model_2_size: int,
                                   model_2_auc: float):
        """
        Creates a label specifically for the allele frequency bins

        Returns single string:
            If sample sizes match:
                {bin_label}
                Model 1: {auc}
                Model 2: {auc}
                {sample_size}
                {\n}

            If not:
                {bin_label}
                Model 1: {auc} (n: {sample_size})
                Model 2: {auc} (n: {sample_size})
                {\n}
        """
        if model_1_size == model_2_size:
            return f'{bin_label}\nModel 1: {model_1_auc}\nModel 2: {model_2_auc}\nn: {model_1_size}'
        else:
            return f'{bin_label}\nModel 1: {model_1_auc} (n: {model_1_size})\n' \
                   f'Model 2: {model_2_auc} (n: {model_2_size})'

    @staticmethod
    def _subset_af_bin(dataset, upper_bound, lower_bound, last_iter=False):
        if last_iter:
            return dataset[(dataset['gnomAD_AF'] >= lower_bound) & (dataset['gnomAD_AF'] <= upper_bound)]
        else:
            return dataset[(dataset['gnomAD_AF'] >= lower_bound) & (dataset['gnomAD_AF'] < upper_bound)]

    def _plot_bin(self, ax, x_index, label, auc_m1, m1_ss, auc_m2, m2_ss):
        width = 0.3
        ax.bar(
            x_index - width,
            auc_m1,
            width,
            align='edge',
            color='red'
        )
        ax.bar(
            x_index,
            auc_m2,
            width,
            align='edge',
            color='blue'
        )
        ax.plot(
            np.NaN,
            np.NaN,
            color='none',
            label=self._create_af_bins_plotlabels(
                label,
                m1_ss,
                auc_m1,
                m2_ss,
                auc_m2
            )
        )

    def _plot_af_bins(self, model_1_data, model_2_data):
        ax_afb = self.fig_afb.add_subplot(1, 1, 1)
        bin_labels = []

        # Plotting the NaN AF values as if they were singletons
        try:
            f_auc_m1 = calculate_auc(model_1_data[model_1_data['is_imputed']])
            f_auc_m2 = calculate_auc(model_2_data[model_2_data['is_imputed']])
        except ValueError:
            print('Could not calculate an AUC for possible singleton variants.')
            f_auc_m1 = np.NaN
            f_auc_m2 = np.NaN
        bin_labels.append('"0"')

        self._plot_bin(
            ax_afb,
            0,
            '"0"',
            f_auc_m1,
            model_1_data[model_1_data['is_imputed']].shape[0],
            f_auc_m2,
            model_2_data[model_2_data['is_imputed']].shape[0]
        )

        bins = [0, 1e-6, 1e-5, 0.0001, 0.001, 0.01, 1]  # Starting at < 0.0001%, up to bin
        # Sadly bins*100 doesn't work for 1e-6, cause of rounding errors
        bins_labels = [0, 1e-4, 1e-3, 0.01, 0.1, 1, 100]
        for i in range(1, len(bins)):
            last_iter = False
            upper_bound = bins[i]
            if upper_bound == bins[-1]:
                last_iter = True
            lower_bound = bins[i - 1]
            subset_m1 = self._subset_af_bin(model_1_data, upper_bound, lower_bound, last_iter)
            subset_m2 = self._subset_af_bin(model_2_data, upper_bound, lower_bound, last_iter)
            try:
                auc_m1 = calculate_auc(subset_m1)
                auc_m2 = calculate_auc(subset_m2)
            except ValueError:
                print(
                    f'Could not calculate AUC for allele frequency bin: '
                    f'{lower_bound}-{upper_bound}'
                )
                auc_m1 = np.NaN
                auc_m2 = np.NaN
            if last_iter:
                bin_label = f'{bins_labels[i - 1]} <= x <= {bins_labels[i]}%'
            else:
                bin_label = f'{bins_labels[i - 1]} <= x < {bins_labels[i]}%'
            bin_labels.append(bin_label)

            self._plot_bin(
                ax_afb,
                i,
                bin_label,
                auc_m1,
                subset_m1.shape[0],
                auc_m2,
                subset_m2.shape[0]
            )
        ax_afb.plot(
            np.NaN,
            np.NaN,
            color='red',
            label='= Model 1'
        )
        ax_afb.plot(
            np.NaN,
            np.NaN,
            color='blue',
            label='= Model 2'
        )
        ax_afb.set_xticks(list(range(0, len(bins))), bin_labels, rotation=45)
        ax_afb.set_xlabel('Allele frequency Bin')
        ax_afb.set_ylabel('AUC')
        ax_afb.set_ylim(0.0, 1.0)
        ax_afb.set_xlim(-0.5, len(bins) - 0.5)
        ax_afb.legend(loc='upper left', bbox_to_anchor=(1.0, 1.01), labelspacing=2)

    @staticmethod
    def _create_auc_label(model_1_auc, model_1_ss, model_2_auc, model_2_ss):
        """
        Creates the label for specifically AUC (sub)plots

        Returns tuple of 3:
        - Label for model 1. If element 3 returns None, contains sample size as well.
        - Label for model 2. If element 3 returns None, contains sample size as well.
        - Label for legend title (if sample sizes match). Returns None (matplotlib legend title default) if sample
        sizes do not match.
        """
        if model_1_ss == model_2_ss:
            return f'Model 1: {model_1_auc}', f'Model 2: {model_2_auc}', f'n: {model_1_ss}'
        else:
            return f'Model 1: {model_1_auc}\nn: {model_1_ss}', \
                   f'Model 2: {model_2_auc}\nn: {model_2_ss}', \
                   None

    def _plot_auc(self, auc_model_1, model_1_n_samples, auc_model_2, model_2_n_samples, title):
        # Plotting AUCs
        ax_auc = self.fig_auc.add_subplot(self.n_rows, self.n_cols, self.index)
        labels = self._create_auc_label(
            auc_model_1, model_1_n_samples, auc_model_2, model_2_n_samples
        )

        ax_auc.bar(1, auc_model_1, color='red', label=labels[0])
        ax_auc.bar(2, auc_model_2, color='blue', label=labels[1])

        if math.isnan(auc_model_1):
            ax_auc.text(
                1.5, 0.5, "Not available",
                fontsize='x-large',
                horizontalalignment='center',
                verticalalignment='center'
            )

        ax_auc.set_title(title)
        ax_auc.set_xticks([1, 2], ['Model 1', 'Model 2'])
        ax_auc.set_xlim(0.0, 3.0)
        ax_auc.set_ylim(0.0, 1.0)
        ax_auc.legend(loc='upper left', bbox_to_anchor=(1.0, 1.02), title=labels[2])

    def _plot_score_dist(self, model_1_data, model_1_n_samples, model_2_data, model_2_n_samples, title):
        self._create_boxplot_for_column(self.fig_score_dist, SCORE, model_1_data,
                                        model_1_n_samples,
                                        model_2_data, model_2_n_samples, title)

    def _plot_score_diff(self, model_1_data, model_1_n_samples, model_2_data, model_2_n_samples, title):
        self._create_boxplot_for_column(self.fig_score_diff, 'score_diff', model_1_data,
                                        model_1_n_samples, model_2_data, model_2_n_samples, title)

    @staticmethod
    def _create_boxplot_label(model_1_data, model_1_ss, model_2_data, model_2_ss):
        n_benign_m1 = model_1_data[model_1_data[BINARIZED_LABEL] == 0].shape[0]
        n_patho_m1 = model_1_data[model_1_data[BINARIZED_LABEL] == 1].shape[0]
        n_benign_m2 = model_2_data[model_2_data[BINARIZED_LABEL] == 0].shape[0]
        n_patho_m2 = model_2_data[model_2_data[BINARIZED_LABEL] == 1].shape[0]
        return f'Model 1:\nT: {model_1_ss}\nB: {n_benign_m1}\nP: {n_patho_m1}', \
               f'Model 2:\nT: {model_2_ss}\nB: {n_benign_m2}\nP: {n_patho_m2}'

    def _create_boxplot_for_column(self, plot_figure, column_to_plot, model_1_data,
                                   model_1_n_samples, model_2_data, model_2_n_samples, title):
        ax = plot_figure.add_subplot(self.n_rows, self.n_cols, self.index)
        sns.violinplot(
            data=pd.concat([model_1_data, model_2_data]),
            x=BINARIZED_LABEL,
            y=column_to_plot,
            hue='model',
            ax=ax,
            split=True,
            palette={'model_1': 'red', 'model_2': 'blue'},
            legend=False
        )
        labels = self._create_boxplot_label(model_1_data, model_1_n_samples, model_2_data, model_2_n_samples)
        red_patch = mpatches.Patch(color='red', label=labels[0])
        blue_patch = mpatches.Patch(color='blue', label=labels[1])
        ax.set_ylim(0.0, 1.0)
        ax.set_title(title)
        ax.legend(
            handles=[red_patch, blue_patch],
            loc='upper left',
            bbox_to_anchor=(1.0, 1.02),
            labelspacing=2
        )

    def export(self, output):
        print(f'Exporting figures to: {output}')
        self.fig_roc.savefig(os.path.join(output, 'roc.png'))
        self.fig_auc.savefig(os.path.join(output, 'auc.png'))
        self.fig_afb.savefig(os.path.join(output, 'allele_frequency.png'))
        self.fig_score_dist.savefig(os.path.join(output, 'score_distributions.png'))
        self.fig_score_diff.savefig(os.path.join(output, 'score_differences.png'))
        print('Export done.')


def main():
    # Processing and validating CLA
    validator = Validator()
    m1_scores_path, m1_labels_path, m2_scores_path, m2_labels_path, force_merge, \
    output_path = process_cla(validator)

    # Reading in data and validating data
    m1, m1_cons = prepare_data_file(validator, m1_scores_path, m1_labels_path, 1, force_merge)
    m2, m2_cons = prepare_data_file(validator, m2_scores_path, m2_labels_path, 2, force_merge)

    # Turning processing of consequences on or off based on presence of Consequence column
    process_consequences = True
    if not m1_cons or not m2_cons:
        warnings.warn('Encountered missing Consequence column. Disabling per-consequence '
                      'performance metrics.')
        process_consequences = False

    # Validate if score files have the same number of variants (per consequence)
    validator.validate_score_files_length(m1, m2, process_consequences)

    # Calculating score differences
    calculate_score_difference(m1)
    calculate_score_difference(m2)

    # Adding column containing the imputed AF
    add_imputed_af(m1)
    add_imputed_af(m2)

    # Adding model identifier to the dataset for violin plots
    add_model_identifier(m1, 'model_1')
    add_model_identifier(m2, 'model_2')

    # Plotting
    plotter = Plotter(process_consequences)
    plotter.prepare_plots(os.path.basename(m1_scores_path),
                          os.path.basename(m1_labels_path),
                          os.path.basename(m2_scores_path),
                          os.path.basename(m2_labels_path))
    plotter.prepare_subplots(m1)
    plotter.plot(m1, m2)
    plotter.export(output_path)


if __name__ == '__main__':
    main()
