import os
import typing
import warnings
from pathlib import Path

import pandas as pd

from utility_scripts.threshold_calculator.errors import NotTSVError, FileMismatchError


class Validator:
    def validate_input_path(self, path):
        self._validate_file_exist(path)
        self._validate_is_gzip_tsv(path)
        return path

    @staticmethod
    def _validate_file_exist(path):
        if not os.path.isfile(path):
            raise FileNotFoundError("No such file or directory: ", path)

    @staticmethod
    def _validate_is_gzip_tsv(path):
        if not path.endswith('.tsv.gz'):
            raise NotTSVError("Argument given does not have a gzipped TSV extension: ", path)

    @staticmethod
    def validate_sample_size_match(dataset1: pd.DataFrame, dataset2: pd.DataFrame):
        if dataset1.shape[0] != dataset2.shape[0]:
            raise FileMismatchError("The 2 different datasets do not match in size!")

    def validate_output_argument(self, path):
        path = Path(path).absolute()
        self._validate_output_directory_exist(path)
        return path

    @staticmethod
    def _validate_output_directory_exist(path):
        if not os.path.isdir(path):
            warnings.warn('Output directory does not exist, attempting to create.')
            os.makedirs(path)

    @staticmethod
    def validate_columns_dataset(dataset: pd.DataFrame, required_columns: typing.Iterable, filename: str):
        missing_columns = []
        for column in required_columns:
            if column not in dataset.columns:
                missing_columns.append(column)
        if len(missing_columns) > 0:
            raise KeyError(f'Required column(s) {", ".join(missing_columns)} missing from {filename}!')
        return dataset
