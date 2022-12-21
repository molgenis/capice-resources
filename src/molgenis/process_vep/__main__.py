#!/usr/bin/env python3

import json
import os
from pathlib import Path
from argparse import ArgumentParser

import pandas as pd

from molgenis.core import Module, GlobalEnums
from molgenis.utilities import merge_dataset_rows
from molgenis.process_vep.vep_processer import VEPProcesser
from molgenis.process_vep.progress_printer import ProgressPrinter
from molgenis.process_vep import VEPFileEnum, CGDEnum, VEPProcessingEnum


class ProcessVEP(Module):
    def __init__(self):
        super(ProcessVEP, self).__init__(
            program='Process VEP TSV',
            description='Processes an VEP output TSV (after running it through BCFTools). '
                        'Removes duplicates, variants that end up on mismatching genes and '
                        'variants that got corrupted on the binarized label or sample weight.'
        )

    @staticmethod
    def _create_module_specific_arguments(parser: ArgumentParser):
        required = parser.add_argument_group('Required arguments')
        optional = parser.add_argument_group('Optional arguments')
        required.add_argument(
            '-t',
            '--train-test',
            type=str,
            required=True,
            help='Input location of train-test VEP TSV'
        )
        required.add_argument(
            '-v',
            '--validation',
            type=str,
            required=True,
            help='Input location of the validation VEP TSV'
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
        return parser

    def _validate_module_specific_arguments(self, parser):
        train_test = self.input_validator.validate_icli_file(
            parser.get_argument('train_test'),
            ('.tsv.gz', '.tsv')
        )
        validation = self.input_validator.validate_icli_file(
            parser.get_argument('validation'),
            ('.tsv.gz', '.tsv')
        )
        train_features = self.input_validator.validate_icli_file(
            parser.get_argument('features'),
            '.json'
        )
        genes_argument = self.input_validator.validate_icli_file(
            parser.get_argument('genes'),
            ('.tsv.gz', '.tsv', '.txt', '.txt.gz')
        )
        output_argument = self.input_validator.validate_ocli_directory(
            parser.get_argument('output')
        )
        assembly_flag = parser.get_argument('assembly')
        return {
            **train_test,
            **validation,
            **train_features,
            **genes_argument,
            **output_argument,
            **assembly_flag
        }

    def run_module(self, arguments: dict[str, object]):
        train_test = self._read_vep_data(arguments['train_test'])
        validation = self._read_vep_data(arguments['validation'])
        output = arguments['output']
        train_test[VEPProcessingEnum.SOURCE.value] = VEPProcessingEnum.TRAIN_TEST.value
        validation[VEPProcessingEnum.SOURCE.value] = VEPProcessingEnum.VALIDATION.value
        merged_datasets = merge_dataset_rows(train_test, validation)
        train_features = self._read_train_features(arguments['features'])
        cgd = self._read_cgd_data(arguments['genes'])
        build38 = arguments['assembly']
        self._process_vep(
            merged_datasets,
            train_features,
            cgd,
            build38  # type: ignore
        )
        train_test, validation = self._split_data(merged_datasets)
        return {
            VEPProcessingEnum.TRAIN_TEST.value: train_test,
            VEPProcessingEnum.VALIDATION.value: validation,
            GlobalEnums.OUTPUT.value: output
        }

    @staticmethod
    def _read_train_features(train_features_argument):
        with open(train_features_argument, 'rt') as fh:
            features = list(json.load(fh).keys())
        return features

    def _read_vep_data(self, vep_file_argument):
        return self._read_pandas_tsv(vep_file_argument, VEPFileEnum.list())

    def _read_cgd_data(self, cgd_file_argument):
        data = self._read_pandas_tsv(cgd_file_argument, CGDEnum.list())
        genes = self._correct_cgd_data(data)
        return genes

    @staticmethod
    def _correct_cgd_data(cgd_data: pd.DataFrame) -> list[str]:
        cgd_data.drop(index=cgd_data[cgd_data['#GENE'] == 'TENM1'].index, inplace=True)
        return list(cgd_data[cgd_data['INHERITANCE'].str.contains('AR')]['#GENE'].values)

    def _process_vep(
            self,
            data: pd.DataFrame,
            train_features: list[str],
            cgd: list[str],
            build38: bool
    ):
        progress_printer = ProgressPrinter()
        progress_printer.set_initial_size(data)

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
        print('Extracting binarized_label and sample_weight')
        data[VEPProcessingEnum.BINARIZED_LABEL.value] = data[VEPFileEnum.ID.value].str.split(
            GlobalEnums.SEPARATOR.value, expand=True)[5].astype(float)
        data[VEPProcessingEnum.SAMPLE_WEIGHT.value] = data[VEPFileEnum.ID.value].str.split(
            GlobalEnums.SEPARATOR.value, expand=True)[6].astype(float)

    @staticmethod
    def _split_data(merged_data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        train_test = merged_data.loc[
            merged_data[
                merged_data[VEPProcessingEnum.SOURCE.value] == VEPProcessingEnum.TRAIN_TEST.value
            ].index, :
        ]
        train_test.reset_index(drop=True, inplace=True)
        validation = merged_data.loc[
            merged_data[
                merged_data[VEPProcessingEnum.SOURCE.value] == VEPProcessingEnum.VALIDATION.value
            ].index, :
        ]
        validation.reset_index(drop=True, inplace=True)
        return train_test, validation

    def export(self, output: dict[object, pd.DataFrame | Path | os.PathLike]):
        self._export_train_test(
            output[VEPProcessingEnum.TRAIN_TEST.value],
            output[GlobalEnums.OUTPUT.value]
        )
        self._export_validation(
            output[VEPProcessingEnum.VALIDATION.value],
            output[GlobalEnums.OUTPUT.value]
        )

    def _export_train_test(self, train_test: pd.DataFrame, output_path: os.PathLike | Path):
        self.exporter.export_pandas_file(os.path.join(output_path, 'train_test.tsv.gz'), train_test)

    def _export_validation(self, validation: pd.DataFrame, output_path: os.PathLike | Path):
        self.exporter.export_pandas_file(os.path.join(output_path, 'validation.tsv.gz'), validation)


def main():
    ProcessVEP().run()


if __name__ == '__main__':
    main()
