import os
import gzip
from enum import Enum
from pathlib import Path
from abc import abstractmethod, ABCMeta
from argparse import ArgumentParser

import pandas as pd

from molgenis.capice_resources.core.exporter import Exporter
from molgenis.capice_resources.core.validator import InputValidator, DataValidator
from molgenis.capice_resources.core.command_line_interface import CommandLineInterface


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

    def parse_and_validate_cli(self) -> dict[str, str | object]:
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
    def _create_module_specific_arguments(parser: ArgumentParser) -> ArgumentParser:
        """
        For each of the modules to fill in according to groups "Required arguments" and
        "Optional arguments".
        """
        return parser

    @abstractmethod
    def _validate_module_specific_arguments(
            self,
            parser: CommandLineInterface
    ) -> dict[str, str | object]:
        """
        Function to house all calls to input cli validators.

        Expects a return statement containing:
            [key]: argument key
            [value]: argument value

        To combine multiple command line arguments: z = {**x, **y} where x and y are also dict.
        """
        return {}

    def _read_pandas_tsv(
            self,
            path: os.PathLike[str] | str | Path,
            required_columns: list[str]
    ) -> pd.DataFrame:
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
            pd.read_csv(path, sep='\t', low_memory=False, na_values=GlobalEnums.NA_VALUES.value),
            required_columns
        )

    def _read_vcf_file(self, path: os.PathLike | Path) -> pd.DataFrame:
        """
        Utilitary function to read a (gzipped) VCF file

        Args:
            path:
                Path to the to be read (gzipped) VCF file.

        Returns:
            pandas.DataFrame:
                Loaded VCF data as pandas Dataframe.

        Raises:
            IndexError:
                IndexError is raised when there are no rows in the data.
            KeyError:
                KeyError is raised when #CHROM, POS, REF, ALT or INFO is not found in the
                header of the VCF file.
        """
        if str(path).endswith('.gz'):
            fh = gzip.open(path, 'rt')
        else:
            fh = open(path, 'rt')
        skiprows = 0
        for line in fh:
            if line.strip().startswith("##"):
                skiprows += 1
            else:
                break
        fh.close()
        return self.data_validator.validate_pandas_dataframe(
            pd.read_csv(
                path,
                sep='\t',
                low_memory=False,
                na_values=GlobalEnums.NA_VALUES.value,
                skiprows=skiprows
            ),
            [
                GlobalEnums.VCF_CHROM.value,
                GlobalEnums.POS.value,
                GlobalEnums.REF.value,
                GlobalEnums.ALT.value,
                GlobalEnums.INFO.value
            ]
        )

    @abstractmethod
    def run_module(self, arguments: dict[str, str | object]) -> dict:
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
    TSV_EXTENSIONS = ('.tsv.gz', '.tsv')
    SYMBOL = 'SYMBOL'
    CHROM = 'CHROM'
    VCF_CHROM = '#CHROM'
    POS = 'POS'
    REF = 'REF'
    ALT = 'ALT'
    INFO = 'INFO'
    BINARIZED_LABEL = 'binarized_label'
    SCORE = 'score'
    DATASET_SOURCE = 'dataset_source'
    CONSTRAINED_LAYOUT = {'w_pad': 0.2, 'h_pad': 0.2}
    SAMPLE_WEIGHT = 'sample_weight'
    TRAIN_TEST = 'train_test'
    VALIDATION = 'validation'
    ID = 'ID'
    AF_BINS = [0, 1e-6, 1e-5, 0.0001, 0.001, 0.01, 1]  # Starting at < 0.0001%, up to bin 100%
    GNOMAD_AF = 'gnomAD_AF'
    CONSEQUENCE = 'Consequence'
    IMPUTED = 'is_imputed'
    NA_VALUES = '.'


def add_dataset_source(frame: pd.DataFrame, name: str) -> None:
    """
    Function to add a dataset source to a dataset.
    Created it here as creating it in utilities would create a circular import loop.

    Args:
        frame:
            The dataframe to which apply the dataset source to.
        name:
            The name of the dataset source that needs to be applied.

    """
    frame[GlobalEnums.DATASET_SOURCE.value] = name
