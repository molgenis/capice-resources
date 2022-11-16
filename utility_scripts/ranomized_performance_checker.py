#!/usr/bin/env python3

import os
import math
import pickle
import warnings
import argparse
import numpy as np
import pandas as pd
import xgboost as xgb
from pathlib import Path
from matplotlib import cm
from matplotlib import pyplot as plt
from sklearn.metrics import roc_curve, roc_auc_score


class Validator:
    def validate_models_scores_argument(self, path: os.PathLike) -> os.PathLike:
        path = Path(path).absolute()
        self._validate_path_exist(path, makedirs=False)
        self._validate_models_scores_has_files(path)
        return path

    @staticmethod
    def _validate_models_scores_has_files(path):
        has_models = False
        has_scores = False
        depth_checked = False
        for (root, dirs, files) in os.walk(path):
            if has_scores and has_models:
                break
            for file in files:
                if file.endswith('.pickle.dat'):
                    has_models = True
                    if not depth_checked:
                        if not os.path.isfile(os.path.join(root, file)):
                            raise FileNotFoundError(
                                'Supplied input argument max depth is too large! (maximum allowed: 1)'
                            )
                        depth_checked = True
                    if has_scores:
                        break
                if file.endswith('.tsv.gz'):
                    has_scores = True
                    if not depth_checked:
                        if not os.path.isfile(os.path.join(root, file)):
                            raise FileNotFoundError(
                                'Supplied input argument max depth is too large! (maximum allowed: 1)'
                            )
                        depth_checked = True
                    if has_models:
                        break
        if not has_scores or not has_models:
            raise FileNotFoundError('Input directory does not contain both score and model files!')

    def validate_validation_argument(self, path: os.PathLike) -> os.PathLike:
        path = Path(path).absolute()
        self._validate_file_exits(path)
        return path

    @staticmethod
    def _validate_file_exits(path):
        if not os.path.isfile(path):
            raise FileNotFoundError('Input validation file does not exists!')

    def validate_output_argument(self, path: os.PathLike) -> os.PathLike:
        path = Path(path).absolute()
        self._validate_path_exist(path)
        return path

    @staticmethod
    def _validate_path_exist(path, makedirs=True):
        if not os.path.isdir(path):
            if makedirs:
                warnings.warn(f'Path {path} does not exist! Attempting to create.')
                os.makedirs(path)
            else:
                raise OSError(f'Path {path} does not exist!')


class CommandLineParser:
    def __init__(self):
        parser = self._create_argument_parser()
        self.arguments = parser.parse_args()

    @staticmethod
    def _create_argument_parser():
        parser = argparse.ArgumentParser(
            prog='Test randomized performance',
            description='Testing script to take 10 models and 10 score files and '
                        'tests the performance of these 10 models.'
        )

        required = parser.add_argument_group('Required arguments')

        required.add_argument(
            '-i',
            '--input',
            type=str,
            required=True,
            help='Input directory where all model and score files are. '
                 'Expects models to be called xxx.pickle.dat and score files to be called xxx.tsv.gz.\n'
                 'DO NOT PLACE ANY OTHER TSV.GZ FILES IN THIS DIRECTORY.'
        )

        required.add_argument(
            '-v',
            '--validation',
            type=str,
            required=True,
            help='Full path of the validation file used to create all score files.'
        )

        required.add_argument(
            '-o',
            '--output',
            type=str,
            required=True,
            help='Output path + filename'
        )
        return parser

    def get_argument(self, argument_key):
        value = None
        if argument_key in self.arguments:
            value = getattr(self.arguments, argument_key)
        return value


def parse_input_argument(input_path: os.PathLike) -> (list[os.PathLike], list[os.PathLike]):
    models = []
    scores = []
    for (root, dirs, files) in os.walk(input_path):
        for file in files:
            if file.endswith('.pickle.dat'):
                models.append(Path(os.path.join(root, file)))
            elif file.endswith('.tsv.gz'):
                scores.append(Path(os.path.join(root, file)))
    return models, scores


def read_models(model_paths: list[os.PathLike]) -> list[xgb.XGBClassifier]:
    models = []
    for file in model_paths:
        with open(file, 'rb') as fh:
            models.append(pickle.load(fh))
    return models


def read_scores(score_paths: list[os.PathLike]) -> list[pd.DataFrame]:
    scores = []
    for file in score_paths:
        scores.append(pd.read_csv(file, sep='\t', low_memory=False, usecols=['score']))
    return scores


def obtain_models_stats(models: list[xgb.XGBClassifier]) -> dict[str, pd.DataFrame]:
    importance_types = ['gain', 'total_gain', 'weight', 'cover', 'total_cover']
    importances_dict = {}
    score_columns = []
    for it in importance_types:
        for i, model in enumerate(models):
            score_string = f'score_{i}'
            if score_string not in score_columns:
                score_columns.append(score_string)
            importances = model.get_booster().get_score(importance_type=it)
            ip = pd.DataFrame(
                    data=[importances.keys(), importances.values()],
                    index=['feature', score_string]
                ).T
            ip.sort_values(by=score_string, ascending=False, inplace=True, ignore_index=True)
            if it == 'gain':
                ip[f'rank_{i}'] = ip.index + 1
            if i == 0:
                importances_dict[it] = ip
            else:
                importances_dict[it] = importances_dict[it].merge(ip, on='feature', how='inner')
    # Sorting and normalizing
    for it in importance_types:
        importances_dict[it]['sorting'] = importances_dict[it][score_columns].mean(axis=1)
        importances_dict[it].sort_values(by='sorting', ascending=False, ignore_index=True, inplace=True)
        importances_dict[it].drop(columns='sorting', inplace=True)
    return importances_dict


def merge_model_files(scores: list[pd.DataFrame], validation: pd.DataFrame) -> pd.DataFrame:
    for i, score in enumerate(scores, start=1):
        validation[f'model_{i}'] = score['score']
    return validation


class Plotter:
    def __init__(self, output_path):
        self.output_path = output_path
        self.mf_indexes = {}
        self.fip = plt.figure(figsize=(40, 40))
        self.mp_roc = plt.figure(figsize=(11, 11))
        self.mp_auc = plt.figure(figsize=(20, 40))
        self.models_colormap = {}
        self.mp_models = []
        self.mp_ncols = 3
        self.mp_nrows = 0
        self.index = 1
        self._set_constrained_layout()

    def _set_constrained_layout(self):
        for figure in [self.fip, self.mp_roc, self.mp_auc]:
            figure.set_constrained_layout({'w_pad': 0.2, 'h_pad': 0.2})

    def plot_model_importances(self, model_stats: dict[str, pd.DataFrame]):
        importance_types = list(model_stats.keys())
        for i, it in enumerate(importance_types, start=1):
            ax = self.fip.add_subplot(len(importance_types) + 1, 1, i)
            data = model_stats[it]
            if i == 1:
                for feature_number, feature in enumerate(data['feature'].values):
                    self.mf_indexes[feature] = feature_number
            data['x_ticks'] = data['feature'].map(self.mf_indexes)
            data.sort_values(by='x_ticks', inplace=True)
            score_columns = []
            for column in data.columns:
                if column.startswith('score_'):
                    score_columns.append(column)
            normalization_mean = data[score_columns].mean()
            normalization_std = data[score_columns].std()
            data_mean = (
                    (data[score_columns] - normalization_mean) / normalization_std
            ).mean(axis=1)
            data_std = (
                    (data[score_columns] - normalization_mean) / normalization_std
            ).std(axis=1)
            data_xticks = data['x_ticks']
            self._plot_scatter_with_errorbar(ax, data_xticks, it, data_mean, data_std)
        ax = self.fip.add_subplot(len(importance_types) + 1, 1, i+1)
        rank_columns = []
        for col in model_stats['gain']:
            if col.startswith('rank_'):
                rank_columns.append(col)
        data = model_stats['gain']
        data_mean = data[rank_columns].mean(axis=1)
        data_std = data[rank_columns].std(axis=1)
        data_xticks = data['x_ticks']
        self._plot_scatter_with_errorbar(ax, data_xticks, 'rank', data_mean, data_std)

    def _plot_scatter_with_errorbar(self, ax, xticks, title, data_mean, data_std):
        ax.set_title(title)
        ax.set_ylabel(title)
        ax.set_xlabel('feature')
        ax.set_xticks(xticks)
        ax.set_xticklabels(self.mf_indexes.keys(), rotation=45, ha='right', minor=False)
        ax.scatter(xticks, data_mean)
        ax.errorbar(xticks, data_mean, data_std, linestyle='None')
        ax.ticklabel_format(axis='y', useOffset=False, style='plain')

    @staticmethod
    def _plot_scatter_with_errorbar_model_performances(ax, consequence, mean, std, counts_benign,
                                                       counts_pathogenic):
        ax.set_title(consequence)
        ax.set_ylabel('AUC')
        ax.scatter(0, mean, label=f'Mean: {mean:.4f}+-{std:.4f}\n'
                                  f'n_benig: {counts_benign}\n'
                                  f'n_patho: {counts_pathogenic}')
        ax.errorbar(0, mean, std, linestyle='None')
        ax.legend(loc='upper left', bbox_to_anchor=(1.0, 1.0))
        ax.set_ylim((0.0, 1.0))
        ax.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)

    def plot_model_performances(self, merged_model_scores: pd.DataFrame):
        self._determine_n_models(merged_model_scores)
        self._set_models_colormap()
        self._plot_roc(merged_model_scores)
        means, stds, counts_b, counts_p = self._determine_consequences_performances(
            merged_model_scores)
        for i, consequence in enumerate(means.keys(), start=1):
            ax = self.mp_auc.add_subplot(self.mp_nrows, self.mp_ncols, i)
            self._plot_scatter_with_errorbar_model_performances(
                ax,
                consequence,
                means[consequence],
                stds[consequence],
                counts_b[consequence],
                counts_p[consequence]
            )

    def _determine_consequences_performances(self, merged_model_scores):
        consequences = pd.Series(
            merged_model_scores['Consequence'].str.split('&', expand=True).values.ravel()
        ).dropna().sort_values(ignore_index=True).unique()
        self.mp_nrows = math.ceil(len(consequences) / self.mp_ncols)
        intermediate_aucs = []
        output_means = {}
        output_stds = {}
        output_count_b = {}
        output_count_p = {}
        for consequence in consequences:
            subset = merged_model_scores[
                merged_model_scores['Consequence'].str.contains(consequence)
            ]
            for model in self.mp_models:
                try:
                    auc = roc_auc_score(
                        y_true=subset['binarized_label'], y_score=subset[model]
                    )
                except ValueError:
                    auc = np.nan
                intermediate_aucs.append(auc)
            array = np.array(intermediate_aucs)
            output_means[consequence] = array.mean()
            output_stds[consequence] = array.std()
            output_count_b[consequence] = subset[subset['binarized_label'] == 0].shape[0]
            output_count_p[consequence] = subset[subset['binarized_label'] == 1].shape[0]
            intermediate_aucs = []
        return output_means, output_stds, output_count_b, output_count_p

    def _determine_n_models(self, model_score_data):
        for col in model_score_data.columns:
            if col.startswith('model') and col not in self.models_colormap.keys():
                self.mp_models.append(col)

    def _set_models_colormap(self):
        cmap = cm.get_cmap('viridis', len(self.mp_models))
        for model, color in zip(self.mp_models, cmap.colors):
            self.models_colormap[model] = color

    def _plot_roc(self, model_score_data):
        ax = self.mp_roc.add_subplot(1, 1, 1)
        for model in self.mp_models:
            y_true = model_score_data['binarized_label']
            y_score = model_score_data[model]
            fpr, tpr, _ = roc_curve(y_true=y_true, y_score=y_score)
            auc = roc_auc_score(y_true=y_true, y_score=y_score)
            ax.plot(fpr, tpr, color=self.models_colormap[model], label=f'{model}: {auc:.4f}')
        ax.set_title('Receiver Operator Curve')
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.0])
        ax.set_xlabel('False Positive Rate')
        ax.set_ylabel('True Positive Rate')
        ax.legend(loc='upper left', bbox_to_anchor=(1.0, 1.01))

    def export(self):
        self.fip.savefig(os.path.join(self.output_path, 'model_features.png'))
        self.mp_roc.savefig(os.path.join(self.output_path, 'model_roc.png'))
        self.mp_auc.savefig(os.path.join(self.output_path, 'model_auc.png'))


def main():
    clp = CommandLineParser()
    validator = Validator()
    input_directory = validator.validate_models_scores_argument(clp.get_argument('input'))
    input_validation = validator.validate_validation_argument(clp.get_argument('validation'))
    output_path = validator.validate_output_argument(clp.get_argument('output'))
    plotter = Plotter(output_path)
    model_paths, score_paths = parse_input_argument(input_directory)
    models = read_models(model_paths)
    model_stats = obtain_models_stats(models)
    plotter.plot_model_importances(model_stats)
    del model_paths, models, model_stats
    scores = read_scores(score_paths)
    validation = pd.read_csv(
        input_validation, sep='\t', low_memory=False, usecols=['binarized_label', 'Consequence']
    )
    merged = merge_model_files(scores, validation)
    plotter.plot_model_performances(merged)
    plotter.export()


if __name__ == '__main__':
    main()
