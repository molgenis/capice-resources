import json
import os

import pandas as pd

from molgenis.capice_resources.core import Module, TSVFileEnums, ColumnEnums, \
    DatasetIdentifierEnums, VCFEnums
from molgenis.capice_resources.utilities import merge_dataset_rows, add_dataset_source
from molgenis.capice_resources.process_vep.vep_processer import VEPProcesser
from molgenis.capice_resources.process_vep.progress_printer import ProgressPrinter
from molgenis.capice_resources.process_vep import ProcessVEPEnums
from molgenis.capice_resources.process_vep import CGDColumnEnums


class ProcessVEP(Module):
    def __init__(self):
        super(ProcessVEP, self).__init__(
            program='Process VEP TSV',
            description='Processes an VEP output TSV (after running it through BCFTools). '
                        'Removes duplicates, variants that end up on mismatching genes and '
                        'variants that got corrupted on the binarized label or sample weight.'
        )

    @staticmethod
    def _create_module_specific_arguments(parser):
        required = parser.add_argument_group('Required arguments')
        optional = parser.add_argument_group('Optional arguments')
        required.add_argument(
            '-t',
            '--train-test',
            type=str,
            required=True,
            help='Input location of train-test VEP TSV'
        )
        optional.add_argument(
            '-v',
            '--validation',
            type=str,
            default=None,
            help='Input location of the validation VEP TSV (optional).'
                 'When not supplied: will not perform duplicate checking between train-test and '
                 'validation.'
        )
        required.add_argument(
            '-f',
            '--features',
            type=str,
            required=True,
            help='The train features json that is (going to be) used in CAPICE training'
        )
        required.add_argument(
            '-o',
            '--output',
            type=str,
            required=True,
            help='Output path (without file names)'
        )
        required.add_argument(
            '-g',
            '--genes',
            type=str,
            required=True,
            help='File containing all Autosomal Recessive genes, each gene on a newline. '
                 'Available at: https://research.nhgri.nih.gov/CGD/download/txt/CGD.txt.gz'
        )
        optional.add_argument(
            '-a',
            '--assembly',
            action='store_true',
            help='Flag to enable GRCh38 mode.'
        )
        optional.add_argument(
            '-r',
            '--train-test-previous-iteration',
            type=str,
            help='VEP annotated train-test file of the model of the previous iteration model to '
                 'perform comparison to. '
                 'If supplied, "validation_filtered.tsv.gz" will also be exported to -o / --output.'
        )
        return parser

    def _validate_module_specific_arguments(self, parser):
        train_test = self.input_validator.validate_input_command_line_interface_file(
            parser.get_argument('train_test'),
            TSVFileEnums.TSV_EXTENSIONS.value
        )
        validation = self.input_validator.validate_input_command_line_interface_file(
            parser.get_argument('validation'),
            TSVFileEnums.TSV_EXTENSIONS.value,
            can_be_optional=True
        )
        train_features = self.input_validator.validate_input_command_line_interface_file(
            parser.get_argument('features'),
            '.json'
        )
        genes_argument = self.input_validator.validate_input_command_line_interface_file(
            parser.get_argument('genes'),
            ('.tsv.gz', '.tsv', '.txt', '.txt.gz')
        )
        output_argument = self.input_validator.validate_output_command_line_interface_path(
            parser.get_argument('output')
        )
        pi_data_argument = self.input_validator.validate_input_command_line_interface_file(
            parser.get_argument('train_test_previous_iteration'),
            TSVFileEnums.TSV_EXTENSIONS.value,
            can_be_optional=True
        )
        assembly_flag = parser.get_argument('assembly')
        return {
            **train_test,
            **validation,
            **train_features,
            **genes_argument,
            **output_argument,
            **assembly_flag,
            **pi_data_argument
        }

    def run_module(self, arguments):
        train_test = self._read_vep_data(arguments['train_test'])
        add_dataset_source(train_test, DatasetIdentifierEnums.TRAIN_TEST.value)
        output = arguments['output']
        merged_datasets = self.merge_datasets(train_test, arguments['validation'])
        train_features = self._read_train_features(arguments['features'])
        cgd = self._read_cgd_data(arguments['genes'])
        build38 = arguments['assembly']
        previous_iteration = arguments['train_test_previous_iteration']
        if previous_iteration is not None:
            previous_iteration_dataset = self._read_pandas_tsv(
                previous_iteration,
                ['CHROM', 'POS', 'REF', 'ALT', 'Gene', 'SYMBOL_SOURCE']
            )
        else:
            previous_iteration_dataset = None
        self._process_vep(
            merged_datasets,
            train_features,
            cgd,
            build38
        )
        train_test, validation = self._split_data(merged_datasets)
        validation_filtered = self._process_previous_iteration(
            validation,
            previous_iteration_dataset
        )
        return {
            DatasetIdentifierEnums.TRAIN_TEST.value: train_test,
            DatasetIdentifierEnums.VALIDATION.value: validation,
            DatasetIdentifierEnums.VALIDATION_FILTERED.value: validation_filtered,
            DatasetIdentifierEnums.OUTPUT.value: output
        }

    def merge_datasets(
            self,
            train_test: pd.DataFrame,
            validation: os.PathLike[str] | None = None
    ) -> pd.DataFrame:
        """
        Function to obtain the train_test dataframe and the CLI validation argument to create
        the merged dataset. Checks if validation is None, and if False,
        reads in the validation dataset, adds the source identifier and merges with train-test.
        If True, just returns the train_test as "merged".

        Args:
            train_test:
                pandas.DataFrame object of the train-test dataset.
            validation:
                Optional pathlike object of the validation cli argument.

        Returns:
            dataframe:
                Merged dataframe between train_test and validation (if validation is not None,
                if validation is None just returns train_test).
                Does set the dataset identifier for validation.
        """
        merged_dataset = train_test
        if validation is not None:
            validation = self._read_vep_data(validation)
            add_dataset_source(validation, DatasetIdentifierEnums.VALIDATION.value)
            merged_dataset = merge_dataset_rows(train_test, validation)
        return merged_dataset

    @staticmethod
    def _process_previous_iteration(
            validation_dataset: pd.DataFrame,
            previous_iteration_dataset: pd.DataFrame | None
    ) -> pd.DataFrame | None:
        """
        Method to generate the validation_filtered file

        Args:
            validation_dataset:
                Pandas DataFrame object of the (semi) final validation dataset that is in need of
                being filtered on the train-test of the previous iteration model, for an unbiased
                comparison plots.
            previous_iteration_dataset:
                (Optional) Pandas DataFrame object of the VEP annotated dataset used to make the
                previous iteration model to compare the new iteration model to.

        Returns:
            validation_filtered:
                Pandas DataFrame object of the input validation_dataset filtered on
                previous_iteration_dataset, if the argument is not None. If the
                previous_iteration_dataset is None, output will also be None.
        """
        if previous_iteration_dataset is None:
            return None
        else:
            validation_dataset[
                ColumnEnums.DATASET_SOURCE.value
            ] = DatasetIdentifierEnums.VALIDATION.value
            validation_dataset[
                ColumnEnums.PROCESSING_COLUMN.value
            ] = validation_dataset[
                ['CHROM', 'POS', 'REF', 'ALT', 'Gene', 'SYMBOL_SOURCE']
            ].astype(str).agg('!'.join, axis=1)
            previous_iteration_dataset[
                ColumnEnums.DATASET_SOURCE.value
            ] = DatasetIdentifierEnums.TRAIN_TEST.value
            previous_iteration_dataset[
                ColumnEnums.PROCESSING_COLUMN.value
            ] = previous_iteration_dataset[
                ['CHROM', 'POS', 'REF', 'ALT', 'Gene', 'SYMBOL_SOURCE']
            ].astype(str).agg('!'.join, axis=1)
            merge = merge_dataset_rows(validation_dataset, previous_iteration_dataset)
            merge.drop_duplicates(
                subset=ColumnEnums.PROCESSING_COLUMN.value,
                inplace=True,
                keep=False
            )
            validation_filtered = merge.loc[
                merge[
                    merge[
                        ColumnEnums.DATASET_SOURCE.value
                    ] == DatasetIdentifierEnums.VALIDATION.value].index,
                :
            ].reset_index(drop=True)
            validation_filtered.drop(
                columns=[ColumnEnums.PROCESSING_COLUMN.value, ColumnEnums.DATASET_SOURCE.value],
                inplace=True
            )
            return validation_filtered

    @staticmethod
    def _read_train_features(train_features_argument: os.PathLike[str]) -> list[str]:
        """
        Method to load in the train features.

        Args:
            train_features_argument:
                Pathlike object directing to the train_features json that is going to be used in
                `capice train`.
        Returns:
            list:
                List object of all train_features present within the train_features json.
        """
        with open(train_features_argument, 'rt') as fh:
            features = list(json.load(fh).keys())
        return features

    def _read_vep_data(self, vep_file_argument: os.PathLike[str]) -> pd.DataFrame:
        """
        Small function to reduce duplication reading in the train-test and validation files.

        Args:
            vep_file_argument:
                Pathlike object directing to the VEP file location.
        Returns:
            dataframe:
                Loaded in pandas.DataFrame of the specified vep_file_argument, checked for the
                presence of the GnomAD homozygosity counts column.
        """
        return self._read_pandas_tsv(vep_file_argument, [ProcessVEPEnums.GNOMAD_HN.value])

    def _read_cgd_data(self, cgd_file_argument: os.PathLike[str]) -> list[str]:
        """
        OO function to read in the CGD data and call the correction method.

        Args:
            cgd_file_argument:
                Pathlike object directing to the CGD gene (gzipped) txt/tsv file.
        Returns:
            list:
                List of all Autosomal Recessive (AR) containing genes, with TENM1 filtered out
                since that gene can not ever be AR (it lies on the X chromosome, outside of PAR
                region).
        """
        data = self._read_pandas_tsv(
            cgd_file_argument,
            [
                CGDColumnEnums.GENE.value,
                CGDColumnEnums.INHERITANCE.value
            ]
        )
        genes = self._correct_cgd_data(data)
        return genes

    @staticmethod
    def _correct_cgd_data(cgd_data: pd.DataFrame) -> list[str]:
        """
        Small utilitarian function to filter out TENM1 and return all genes that have been
        observed AR in any way from the CGD gene list.

        Args:
            cgd_data:
                Pandas dataframe of the loaded CGD (gzipped) txt or tsv.
        Returns:
            list:
                List of all Autosomal Recessive (AR) containing genes, with TENM1 filtered out
                since that gene can not ever be AR (it lies on the X chromosome, outside of PAR
                region).
        """
        cgd_data.drop(
            index=cgd_data[cgd_data[CGDColumnEnums.GENE.value] == 'TENM1'].index, inplace=True
        )
        return list(cgd_data[cgd_data[CGDColumnEnums.INHERITANCE.value].str.contains('AR')][
                        CGDColumnEnums.GENE.value].values)

    def _process_vep(
            self,
            data: pd.DataFrame,
            train_features: list[str],
            cgd: list[str],
            build38: bool
    ):
        """
        Object Orientated function to call each of the processors that correct the processed VEP
        data.

        Args:
            data:
                Merged pandas.DataFrame between train-test and validation that should be
                processed upon.
                Please note that this method is performed inplace.
            train_features:
                List of all the train_features that are going to be used in capice train.
            cgd:
                List of all the CGD AR containing genes.
            build38:
                Boolean if the VEP files are created for build 38 or not.

        """
        progress_printer = ProgressPrinter(data)

        processer = VEPProcesser()
        processer.drop_duplicate_entries(data)
        progress_printer.new_shape(data)

        processer.drop_duplicates(data, train_features)
        progress_printer.new_shape(data)

        processer.drop_genes_empty(data)
        progress_printer.new_shape(data)

        if build38:
            processer.process_grch38(data)
            progress_printer.new_shape(data)

        processer.drop_mismatching_genes(data)
        progress_printer.new_shape(data)

        processer.drop_heterozygous_variants_in_ar_genes(data, cgd)
        progress_printer.new_shape(data)

        self.extract_label_and_weight(data)
        processer.drop_variants_incorrect_label_or_weight(data)
        progress_printer.new_shape(data)
        progress_printer.print_final_shape()

    @staticmethod
    def extract_label_and_weight(data: pd.DataFrame):
        """
        Method to extract the binarized_label and sample_weight from the ID column.

        Args:
            data:
                Merged pandas.DataFrame between train-test and validation, that contains the ID
                column. Will add the binarized_label and sample_weight columns to data.
                Performed inplace.

        """
        print('Extracting binarized_label and sample_weight')
        data[ColumnEnums.BINARIZED_LABEL.value] = data[VCFEnums.ID.value].str.split(
            VCFEnums.ID_SEPARATOR.value, expand=True)[5].astype(float)
        data[ColumnEnums.SAMPLE_WEIGHT.value] = data[VCFEnums.ID.value].str.split(
            VCFEnums.ID_SEPARATOR.value, expand=True)[6].astype(float)

    @staticmethod
    def _split_data(
            merged_data: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame | None]:
        """
        Method to split the merged train-test and validation back to the 2 separate datasets.
        Self checks if validation is present within the dataset or not.

        Args:
            merged_data:
                Merged pandas.DataFrame between train-test and (optionally) validation.

        Returns:
            tuple:
                Tuple containing [0] the train-test dataframe and [1] the validation dataframe (
                if validation is present in merged_data, else None).
        """
        train_test = merged_data.loc[
                     merged_data[
                         merged_data[
                             ColumnEnums.DATASET_SOURCE.value
                         ] == DatasetIdentifierEnums.TRAIN_TEST.value
                         ].index, :
                     ]
        train_test.reset_index(drop=True, inplace=True)
        train_test.drop(columns=ColumnEnums.DATASET_SOURCE.value, inplace=True)
        if (
                DatasetIdentifierEnums.VALIDATION.value
                in
                merged_data[ColumnEnums.DATASET_SOURCE.value].values
        ):
            validation = merged_data.loc[
                         merged_data[
                             merged_data[
                                 ColumnEnums.DATASET_SOURCE.value
                             ] == DatasetIdentifierEnums.VALIDATION.value
                             ].index, :
                         ]
            validation.reset_index(drop=True, inplace=True)
            validation.drop(columns=ColumnEnums.DATASET_SOURCE.value, inplace=True)
        else:
            validation = None
        return train_test, validation

    def export(self, output: dict[str, str | pd.DataFrame | os.PathLike[str]]) -> None:
        """
        Main exporting function to call the separate exporters for train-test and validation.

        Args:
            output:
                The dictionary containing the CLI output flag and its value, train-test and its
                train-test dataframe and validation and its validation dataframe.

        """
        output_path = output[DatasetIdentifierEnums.OUTPUT.value]
        self.exporter.export_pandas_file(
            path=os.path.join(output_path, 'train_test.tsv.gz'),
            pandas_object=output[DatasetIdentifierEnums.TRAIN_TEST.value]
        )
        if output[DatasetIdentifierEnums.VALIDATION.value] is not None:
            self.exporter.export_pandas_file(
                path=os.path.join(output_path, 'validation.tsv.gz'),
                pandas_object=output[DatasetIdentifierEnums.VALIDATION.value]
            )
        if output[DatasetIdentifierEnums.VALIDATION_FILTERED.value] is not None:
            self.exporter.export_pandas_file(
                path=os.path.join(output_path, 'validation_filtered.tsv.gz'),
                pandas_object=output[DatasetIdentifierEnums.VALIDATION_FILTERED.value]
            )


def main():
    ProcessVEP().run()


if __name__ == '__main__':
    main()
