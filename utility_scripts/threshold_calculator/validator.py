import os

import pandas as pd

from errors import NotTSVError, FileMismatchError


class Validator:
    def validate_input_path(self, path):
        self._validate_file_exist(path)
        self._validate_is_gzip_tsv(path)
        return path

    @staticmethod
    def _validate_file_exist(path):
        if not os.path.isfile(path):
            raise FileNotFoundError(2, "No such file or directory: ", path)

    @staticmethod
    def _validate_is_gzip_tsv(path):
        if not path.endswith('.tsv.gz'):
            raise NotTSVError(2, "Argument given does not have a gzipped TSV extension: ", path)

    @staticmethod
    def validate_sample_size_match(dataset1: pd.DataFrame, dataset2: pd.DataFrame):
        if dataset1.shape[0] != dataset2.shape[0]:
            raise FileMismatchError(2, "The 2 different datasets do not match in size!")
