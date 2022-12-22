import os
from pathlib import Path
from collections.abc import Iterable

import pandas as pd

from molgenis.capice_resources.utilities import extract_key_value_dict_cli


class InputValidator:
    def validate_icli_file(
            self,
            path: dict[str, os.PathLike | None],
            extension: tuple[str] | str,
            can_be_optional: bool = False
    ) -> dict[str, Path]:
        """
        Validator for an Input Command Line Interface (icli). Specific to files.

        Args:
            path:
                Argument containing the pathlike string to the input file.
            extension:
                Required extension that the file should have
            can_be_optional:
                Optional boolean if the Input CLI can be default "None" or not. Default: False.

        Returns:
            Path:
                pathlib.Path().absolute() instance of input argument "path"

        Raises:
            FileNotFoundError:
                FileNotFoundError is raised when "path" is not a file.
            IOError:
                IOError is raised when "path" does not have the right "extension".

                IOError is also raised when a non-optional argument is encountered as None.
        """
        path_key, path = extract_key_value_dict_cli(path)
        if path is not None:
            path = Path(path)
        self._validate_file(path, extension, can_be_optional)
        return {path_key: path}

    @staticmethod
    def _validate_file(path: Path | None, extension: tuple[str], can_be_optional: bool =
    False):
        """
        First check if the path is not None, since we can encounter optional arguments.
        Since if path is not None in an optional argument, we can validate the argument.
        But if we encounter a None path, we want to check if the argument is optional or not.
        If it is not optional, but still None, then raise error. (should not happen, argparse
        should stop it before this validator, but still good to check).
        """
        if path is not None:
            if not os.path.isfile(path):
                raise FileNotFoundError(f'Input path: {path} does not exist!')
            if not str(path).endswith(extension):
                raise IOError(
                    f'Input {path} does not match the correct extension: '
                    f'{", ".join(extension)}'
                )
        else:
            if not can_be_optional:
                raise IOError('Encountered a None argument for a non-optional flag.')

    def validate_ocli_directory(
            self,
            path: dict[str, os.PathLike],
            extension: tuple[str] | None = None,
            force: bool = False
    ):
        """
        Validator for specifically the output argument.

        Args:
            path:
                Dictionary of the argument parser output "output" flag.
            extension:
                Optional argument that, if given, checks if the output flag meets the required
                supplied extension.
            force:
                Optional argument that can be enabled together with extension. Raises error (see
                errors) if file already exists.

        Returns:
            dict:
                Dictionary of the output argument key and a pathlib.Path object of the output
                argument value.

        Raises:
            IOError:
                IOError is raised when the output path does not contain the required extension.
            FileExistsError:
                FileExistsError is raised when the output file already exists and the force flag
                is set to False.
            OSError:
                OSError is raised when the output directory can not be made.
        """
        path_key, path = extract_key_value_dict_cli(path)
        # Parent path is to prevent the making of output.tsv.gz directory instead of putting
        # output.tsv.gz in the output directory.
        if extension is not None:
            self._validate_output_file(path, extension, force)
            parent_path = path.parent
        else:
            parent_path = path
        if not os.path.exists(parent_path):
            os.makedirs(parent_path)
        return {path_key: path}

    @staticmethod
    def _validate_output_file(path: Path, extension: tuple[str] | None, force: bool):
        if not str(path).endswith(extension):
            raise IOError(f'Output {path} does not end with required extension: {extension}')
        if os.path.isfile(path) and not force:
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