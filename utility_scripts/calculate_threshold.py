#!/usr/bin/env python3

import os
import argparse

import numpy as np
import pandas as pd
from sklearn.metrics import recall_score


class NotTSVError(OSError):
    pass


class FileMismatchError(Exception):
    pass


class CommandLineParser:
    def __init__(self):
        parser = self._create_argument_parser()
        self.arguments = parser.parse_args()

    def _create_argument_parser(self):
        parser = argparse.ArgumentParser(
            prog='Calculate thresholds',
            description='Calculate thresholds based on Li et al. (2020), which is'
                        'based on a recall score between 94 to 96%.'
        )
        required = parser.add_argument_group('Required arguments')

        required.add_argument(
            '--validation',
            type=str,
            action='store',
            required=True,
            help='Input location of the initial validation dataset.'
        )

        required.add_argument(
            '--score_validation',
            type=str,
            action='store',
            required=True,
            help=''
        )
        return parser

    def get_argument(self, argument_key):
        value = None
        if argument_key in self.arguments:
            value = getattr(self.arguments, argument_key)
        return value


class Validator:
    @staticmethod
    def validate_file_exist(path):
        if not os.path.isfile(path):
            raise FileNotFoundError(2, "No such file or directory: ", path)

    @staticmethod
    def validate_is_gzip_tsv(path):
        if not path.endswith('.tsv.gz'):
            raise NotTSVError(2, "Argument given does not have a gzipped TSV extension: ", path)

    @staticmethod
    def validate_sample_size_match(dataset1: pd.DataFrame, dataset2: pd.DataFrame):
        if dataset1.shape[0] != dataset2.shape[0]:
            raise FileMismatchError(2, "The 2 different datasets do not match in size!")


def validate_cla(validator, cla):
    validator.validate_file_exist(cla)
    validator.validate_is_gzip_tsv(cla)


def main():
    clp = CommandLineParser()
    validator = Validator()
    path_validation_raw = clp.get_argument('validation')
    validate_cla(validator, path_validation_raw)
    path_validation_score = clp.get_argument('score_validation')
    validate_cla(validator, path_validation_score)
    ds_validation_raw = pd.read_csv(path_validation_raw, sep='\t', low_memory=False)
    ds_validation_score = pd.read_csv(path_validation_score, sep='\t', low_memory=False)
    validator.validate_sample_size_match(ds_validation_raw, ds_validation_score)
    calculator = ThresholdCalculator(ds_validation_raw, ds_validation_score)
    calculator.calculate_threshold()


class ThresholdCalculator:
    def __init__(self, labels, scores):
        self.data = self._combine_datasets(labels, scores)

    @staticmethod
    def _combine_datasets(dataset1, dataset2):
        return pd.concat([dataset1, dataset2], axis=1)

    def calculate_threshold(self):
        self.reset_threshold()
        for i in np.arange(0, 1, 0.01):
            self.data.loc[self.data['score'] >= i, 'calculated_threshold'] = 1
            recall = recall_score(y_true=self.data['binarized_label'], y_pred=self.data['calculated_threshold'])
            if 0.94 <= recall <= 0.96:
                print(f'Threshold calculated, final threshold: {i}')
                print(f'At recall score: {recall}')
                break
            self.reset_threshold()

    def reset_threshold(self):
        self.data['calculated_threshold'] = 0


if __name__ == '__main__':
    main()

