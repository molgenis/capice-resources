#!/usr/bin/env python3

import os
import math
import pickle
import argparse
import warnings

import numpy as np
import pandas as pd
import xgboost as xgb
from matplotlib import pyplot as plt
from sklearn.metrics import roc_auc_score

# Must be equal to `train_data_creator/src/main/exporter.py` & files in `utility_scripts`
ID_SEPARATOR = '!'

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
            prog='Compare Build 37 and Build 38 models',
            description='Compares the performance of a GRCh37 with a GRCh38 build model of the '
                        'same iteration.'
        )
        required = parser.add_argument_group('Required arguments')

        required.add_argument(
            '--build_37_predicted',
            type=str,
            required=True,
            help='Input location of the GRCh37 CAPICE predicted output TSV. '
                 'Has to be a (gzipped) TSV!'
        )

        required.add_argument(
            '--build_37_vep',
            type=str,
            required=True,
            help='Input location of the GRCh37 VEP output TSV. '
                 'This TSV should be the TSV you put in CAPICE for prediction. '
                 'Has to be a (gzipped) TSV!'
        )

        required.add_argument(
            '--build_37_model',
            type=str,
            required=True,
            help='Input location of the GRCh37 model. Has to be .pickle.dat format!'
        )

        required.add_argument(
            '--build_38_predicted',
            type=str,
            required=True,
            help='Input location of the GRCh38 CAPICE predicted output TSV. '
                 'Has to be a (gzipped) TSV!'
        )

        required.add_argument(
            '--build_38_vep',
            type=str,
            required=True,
            help='Input location of the GRCh38 VEP output TSV. '
                 'This TSV should be the TSV you put in CAPICE for prediction. '
                 'Has to be a (gzipped) TSV!'
        )

        required.add_argument(
            '--build_38_model',
            type=str,
            required=True,
            help='Input location of the GRCh38 model. Has to be .pickle.dat format!'
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
    def validate_is_pickled_model(self, path):
        self._validate_file_extension(path, '.pickle.dat')

    def validate_is_gzipped_tsv(self, path):
        self._validate_file_extension(path, ('.tsv', '.tsv.gz'))

    @staticmethod
    def _validate_file_extension(path, extension):
        if not path.endswith(extension):
            raise IncorrectFileError(f'Input path {path} does not meet the required extension: '
                                     f'{extension}')

    @staticmethod
    def validate_is_xgbclassifier(model):
        if not isinstance(model, xgb.XGBClassifier):
            raise DataError('Supplied model is not of an XGBClassifier class!')

    @staticmethod
    def validate_model_versions_match(build_37_model, build_38_model):
        if not build_37_model.CAPICE_version == build_38_model.CAPICE_version:
            raise FileMismatchError(
                'Supplied build 37 and 38 models do not originate from the same CAPICE version!'
            )

    @staticmethod
    def validate_id_column_present(loaded_vep_dataset):
        if '%ID' not in loaded_vep_dataset.columns:
            raise IncorrectFileError('The ID column has to be present within the VEP dataset!')

    @staticmethod
    def validate_output_argument(output):
        if not os.path.isdir(output):
            warnings.warn(f'Output path {output} does not exist! Creating...')
            try:
                os.makedirs(output)
            except Exception as e:
                print(f'Error encoutered creating output path: {e}')
                exit(1)


def main():
    print('Obtaining CLA')
    cla = CommandLineParser()
    b37_predicted = cla.get_argument('build_37_predicted')
    b37_vep = cla.get_argument('build_37_vep')
    b37_model = cla.get_argument('build_37_model')
    b38_predicted = cla.get_argument('build_38_predicted')
    b38_vep = cla.get_argument('build_38_vep')
    b38_model = cla.get_argument('build_38_model')
    output = cla.get_argument('output')
    print('Validating CLA')
    validator = Validator()
    validator.validate_is_gzipped_tsv(b37_predicted)
    validator.validate_is_gzipped_tsv(b37_vep)
    validator.validate_is_gzipped_tsv(b38_predicted)
    validator.validate_is_gzipped_tsv(b38_vep)
    validator.validate_is_pickled_model(b37_model)
    validator.validate_is_pickled_model(b38_model)
    validator.validate_output_argument(output)
    with open(b37_model, 'rb') as build_37_model:
        model_37 = pickle.load(build_37_model)
    with open(b38_model, 'rb') as build_38_model:
        model_38 = pickle.load(build_38_model)
    validator.validate_is_xgbclassifier(model_37)
    validator.validate_is_xgbclassifier(model_38)
    validator.validate_model_versions_match(model_37, model_38)
    print('Validation complete.\n')

    print('Reading in data.')
    b_37_prediction_data = pd.read_csv(b37_predicted, sep='\t', na_values='.')
    b_37_vep_data = pd.read_csv(b37_vep, sep='\t', na_values='.')
    validator.validate_id_column_present(b_37_vep_data)
    if b_37_prediction_data.shape[0] != b_37_vep_data.shape[0]:
        raise FileMismatchError('Build 37 prediction and VEP files do not match in sample size!')
    b_37_merged = pd.concat([b_37_prediction_data, b_37_vep_data], axis=1)
    b_38_prediction_data = pd.read_csv(b38_predicted, sep='\t', na_values='.')
    b_38_vep_data = pd.read_csv(b38_vep, sep='\t', na_values='.')
    validator.validate_id_column_present(b_38_vep_data)
    if b_38_prediction_data.shape[0] != b_38_vep_data.shape[0]:
        raise FileMismatchError('Build 38 prediction and VEP files do not match in sample size!')
    b_38_merged = pd.concat([b_38_prediction_data, b_38_vep_data], axis=1)
    print('Data read.\n')

    print('Calculating stats')
    b_37_merged['binarized_label'] = b_37_merged['%ID'].str.split(ID_SEPARATOR, expand=True)[
        5].astype(float)
    b_37_merged['score_diff'] = abs(b_37_merged['score'] - b_37_merged['binarized_label'])
    b_38_merged['binarized_label'] = b_38_merged['%ID'].str.split(ID_SEPARATOR, expand=True)[
        5].astype(float)
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
