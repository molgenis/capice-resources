import os
from enum import Enum
from pathlib import Path
from abc import abstractmethod, ABCMeta
from argparse import ArgumentParser

import pandas as pd

from molgenis.core.exporter import Exporter
from molgenis.core.validator import InputValidator, DataValidator
from molgenis.core.command_line_interface import CommandLineInterface


class Module(metaclass=ABCMeta):
    """
    Main module of all CAPICE-RESOURCES modules.

    Houses a couple of globally important functions, validators and the exporter.
    """
    def __init__(self, program: str, description: str):
        """
        Initializing of each of the modules. Includes loading the validators and exporter.
        Also sets the program name and description for the argument parser.

        Args:
            program:
                Very short string of the name of the CAPICE-RESOURCES module.
            description:
                Somewhat short sting of what the module does.
        """
        self.input_validator = InputValidator()
        self.data_validator = DataValidator()
        self.program = program
        self.description = description
        self.exporter = Exporter()

    def run(self) -> None:
        """
        Main run function of each module.

        Consists of creating, parsing and validating the Command Line Interface.
        Then
        Running the module itself.
        Then
        Exporting the results.
        """
        args = self.parse_and_validate_cli()
        output = self.run_module(args)
        self.export(output)

    def parse_and_validate_cli(self) -> dict[str, object]:
        """
        Main function to initialize the command line parser with the program and description
        defined in the init.

        Then

        Makes the call to abstract method for each of the modules to fill in itself.

        Then

        Parses said command line arguments.

        Then

        Validates command line arguments according to abstract method.

        Returns:
            dict:
                A dictionary containing the CLI argument as key and the value it obtained as value.
        """
        cli = CommandLineInterface()
        parser = cli.create_initial(self.program, self.description)
        full_parser = self._create_module_specific_arguments(parser)
        cli.parse_args(full_parser)
        valid_arguments = self._validate_module_specific_arguments(cli)
        return valid_arguments

    @staticmethod
    @abstractmethod
    def _create_module_specific_arguments(parser: ArgumentParser):
        """
        For each of the modules to fill in according to groups "Required arguments" and
        "Optional arguments".
        """
        return parser

    @abstractmethod
    def _validate_module_specific_arguments(self, parser: CommandLineInterface):
        """
        Function to house all calls to input cli validators.

        Expects a return statement containing:
            [key]: argument key
            [value]: argument value

        To combine multiple command line arguments: z = {**x, **y} where x and y are also dict.
        """
        return {}

    def _read_pandas_tsv(self, path: os.PathLike | Path, required_columns: list):
        """
        Utilitarian function to read and immediately validate a pandas.read_csv call according
        to the path and required_columns.

        Args:
            path:
                Path-like object that points to the data.
            required_columns:
                List containing all the columns that this data should have.

        Returns:
            pandas.DataFrame:
                Loaded pandas dataframe.

        Raises:
            IndexError:
                IndexError is raised when there are no rows in the data.
            KeyError:
                KeyError is raised when 1 or more columns from required_columns are
                missing from the data.
        """
        return self.data_validator.validate_pandas_dataframe(
            pd.read_csv(path, sep='\t', low_memory=False, na_values='.'),
            required_columns
        )

    @staticmethod
    @abstractmethod
    def run_module(arguments: dict[str, object]) -> dict[object, object]:
        """
        Function to house all that is required in terms of arguments, variables and calls to
        other functions to make a module function properly.

        Args:
            arguments:
                Dictionary containing all input argument keys and their values.
        Returns:
            dict:
                A dictionary containing all output objects that can be used in export.
                Can be a dataframe, string, dict or other object.
        """
        return {}

    @abstractmethod
    def export(self, output: dict[object, object]) -> None:
        """
        Final destination of each module. Can be divided up into multiple export functions.

        Args:
            output:
                Dictionary obtained from run_module()
        """
        pass


class ExtendedEnum(Enum):
    """
    Extension of the standard Enum python library to return a list of all values the class houses
    once ExtendedEnum.list() is called.
    """
    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class GlobalEnums(ExtendedEnum):
    """
    Enums to use for all modules.
    """
    SEPARATOR = '!'
    OUTPUT = 'output'
