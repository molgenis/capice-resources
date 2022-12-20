import os
from pathlib import Path
from collections.abc import Iterable

import pandas as pd


class InputValidator:
    def validate_icli_file(self, path: dict[str, os.PathLike], extension: tuple[str] | str) -> dict[
        str, Path
    ]:
        """
        Validator for an Input Command Line Interface (icli). Specific to files.

        Args:
            path:
                Argument containing the pathlike string to the input file.
            extension:
                Required extension that the file should have

        Returns:
            Path:
                pathlib.Path().absolute() instance of input argument "path"

        Raises:
            FileNotFoundError:
                FileNotFoundError is raised when "path" is not a file.
            IOError:
                IOError is raised when "path" does not have the right "extension".
        """
        path_key = str(path.keys())
        path = Path(str(path.values())).absolute()
        self._validate_file(path, extension)
        return {path_key: path}

    @staticmethod
    def _validate_file(path: Path, extension: tuple[str]):
        if not os.path.isfile(path):
            raise FileNotFoundError(f'Input path: {path} does not exist!')

        if not str(path).endswith(extension):
            raise IOError(
                f'Input {path} does not match the correct extension: '
                f'{", ".join(extension)}'
            )

    def validate_ocli_directory(
            self,
            path: os.PathLike,
            extension: tuple[str] | None = None,
            force: bool = False
    ):
        path = Path(path).absolute()
        if extension is not None:
            self._validate_output_file(path, extension, force)
        if not os.path.exists(path):
            os.makedirs(path)

    @staticmethod
    def _validate_output_file(path: Path, extension: tuple[str] | None, force: bool):
        if not str(path).endswith(extension):
            raise IOError(f'Output {path} does not end with required extension: {extension}')
        if os.path.isfile(path):
            if not force:
                raise FileExistsError(f'Output {path} already exists and force is not enabled!')


class DataValidator:
    def validate_pandas_dataframe(
            self,
            dataframe: pd.DataFrame,
            required_columns: Iterable
    ) -> pd.DataFrame:
        self._validate_minimal_samples_present(dataframe)
        self._validate_columns_present(dataframe, required_columns)
        return dataframe

    @staticmethod
    def _validate_minimal_samples_present(dataframe: pd.DataFrame) -> None:
        if dataframe.shape[0] <= 0:
            raise IndexError(f'Given dataframe does not contain samples')

    @staticmethod
    def _validate_columns_present(dataframe: pd.DataFrame, columns: Iterable):
        missing = []
        for column in columns:
            if column not in dataframe.columns:
                missing.append(column)
        if len(missing) > 0:
            raise KeyError(f'Missing required columns: {",".join(missing)}')
