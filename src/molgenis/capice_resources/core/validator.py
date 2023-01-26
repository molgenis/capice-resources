import os
from pathlib import Path
from collections.abc import Iterable

import pandas as pd


class InputValidator:
    @staticmethod
    def _extract_key_value_dict_cli(cli_dict: dict[str, str | None]) -> tuple[str, str | None]:
        """
        Function to extract the CLI argument key and its value from an CLI dictionary

        Args:
            cli_dict:
                The dictionary containing the (key) argument key and (value) its command line value.

        Returns:
            tuple:
                Tuple containing [0] the argument key (str) and [1] its value (str or None).
        """
        # Done with list(path.keys())[0] so that the path_key is stored as string instead of
        # dict_keys()
        key = list(cli_dict.keys())[0]
        # Check for None in case we meet an optional argument
        if cli_dict[key] is not None:
            value = str(cli_dict[key])
        else:
            value = None
        return key, value

    def validate_icli_file(
            self,
            path: dict[str, os.PathLike[str] | None | str],
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
        path_key, path_value = self._extract_key_value_dict_cli(path)
        if path_value is not None:
            path_value = Path(path_value).absolute()
        self._validate_file(path_value, extension, can_be_optional)
        return {path_key: path_value}

    def _validate_file(
            self,
            path: Path | None,
            extension: tuple[str] | str,
            can_be_optional: bool = False
    ) -> None:
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
        self._validate_path_is_none(path, can_be_optional)

    def validate_ocli_directory(
            self,
            path: dict[str, str | os.PathLike[str]],
            extension: tuple[str] | None = None,
            force: bool = False
    ) -> dict[str, Path]:
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
                IOError is also raised when the value of path is None.
            FileExistsError:
                FileExistsError is raised when the output file already exists and the force flag
                is set to False.
            OSError:
                OSError is raised when the output directory can not be made.
        """
        path_key, path_value = self._extract_key_value_dict_cli(path)
        self._validate_path_is_none(path_value, False)
        path_value = Path(path_value)
        # Parent path is to prevent the making of output.tsv.gz directory instead of putting
        # output.tsv.gz in the output directory.
        if extension is not None:
            self._validate_output_file(path_value, extension, force)
            self._check_path_exists(path_value.parent)
        else:
            self._check_path_exists(path_value)
        return {path_key: path_value}

    @staticmethod
    def _check_path_exists(directory: str | os.PathLike[str] | Path) -> None:
        """
        Small function to reduce duplication of code to check if a director exists. If not, make it.

        Args:
            directory:
                Path that should be checked if it exists or not. Makes directory if not exists.

        """
        if not os.path.exists(directory):
            os.makedirs(directory)

    @staticmethod
    def _validate_path_is_none(path: os.PathLike[str] | str | None, can_be_optional: bool) -> None:
        """
        Staticmethod to check if path is None, raise IOError when can_be_optional is False.

        Args:
            path:
                Pathlike object or None that should be checked.
            can_be_optional:
                Boolean: True if the flag can be optional and False if the flag should always be
                given from the CLI.

        Raises:
            IOError:
                IOError is raised when path is None and can_be_optional is set to False.
        """
        if path is None and not can_be_optional:
            raise IOError('Encountered None argument in non-optional flag.')

    @staticmethod
    def _validate_output_file(path: Path, extension: tuple[str], force: bool):
        if not str(path).endswith(extension):
            raise IOError(
                f'Output {path} does not end with required extension: {", ".join(extension)}'
            )
        if os.path.isfile(path) and not force:
            raise FileExistsError(f'Output {path} already exists and force is not enabled!')


class DataValidator:
    def validate_pandas_dataframe(
            self,
            dataframe: pd.DataFrame,
            required_columns: Iterable
    ) -> pd.DataFrame:
        """
        Validator for loaded pandas dataframes.

        Args:
            dataframe:
                pandas.DataFrame object over which "required_columns" should be checked.
                Also checks if at least 1 sample is present within dataframe.
            required_columns:
                Iterable object that contains all the columns dataframe should at the very least
                have. First collects all missing columns, then raises an error.

        Returns:
            dataframe:
                The input dataframe.

        Raises:
            IndexError:
                IndexError is raised when the input dataframe does not contain any samples.
            KeyError:
                KeyError is raised when one or more missing columns are detected.
        """
        self._validate_minimal_samples_present(dataframe)
        self._validate_columns_present(dataframe, required_columns)
        return dataframe

    @staticmethod
    def _validate_minimal_samples_present(dataframe: pd.DataFrame) -> None:
        """
        Function to check if at least 1 sample is present.

        Args:
            dataframe:
                The dataframe that should be checked for at least 1 sample.

        Raises:
            IndexError:
                IndexError is raised when the input dataframe does not contain any samples.
        """
        if dataframe.shape[0] <= 0:
            raise IndexError('Given dataframe does not contain samples')

    @staticmethod
    def _validate_columns_present(dataframe: pd.DataFrame, columns: Iterable):
        """
        Function to check if all columns are present within dataframe.

        Args:
            dataframe:
                The dataframe that should be checked for all columns.
            columns:
                Iterable of all the columns that should be checked for within dataframe. First
                collects all missing columns, then raises an error.

        Raises:
            KeyError:
                KeyError is raised when one or more missing columns are detected.
        """
        missing = []
        for column in columns:
            if column not in dataframe.columns:
                missing.append(column)
        if len(missing) > 0:
            raise KeyError(f'Missing required columns: {", ".join(missing)}')
