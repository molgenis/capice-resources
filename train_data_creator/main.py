#!/usr/bin/env python3

import gc

from train_data_creator.src.main.exporter import Exporter
from train_data_creator.src.main.split_datasets import SplitDatasets
from train_data_creator.src.main.sample_weighter import SampleWeighter
from train_data_creator.src.main.data_preprocessor import VKGL, ClinVar
from train_data_creator.src.main.consensus_check import ConsensusChecker
from train_data_creator.src.main.utilities import correct_order_vcf_notation
from train_data_creator.src.main.command_line_parser import CommandLineParser
from train_data_creator.src.main.duplicate_processor import DuplicateProcessor
from train_data_creator.src.main.validators.input_validator import InputValidator


def main():
    # Parse command line
    print('Parsing command line arguments.')
    clp = CommandLineParser()
    input_vkgl = clp.get_argument('input_vkgl')
    input_clinvar = clp.get_argument('input_clinvar')
    output = clp.get_argument('output')

    # Validate
    print('Validating input arguments.')
    validator = InputValidator()
    validator.validate_vkgl(input_vkgl)
    validator.validate_clinvar(input_clinvar)
    output = validator.validate_output(output)
    print('Input arguments valid.\n')

    # Parse
    print('Parsing VKGL.')
    vkgl = VKGL().parse(input_vkgl)
    print('Parsing ClinVar.')
    clinvar = ClinVar().parse(input_clinvar)
    print('Datafiles parsed.\n')

    # Combine
    print('Combining ClinVar and VKGL')
    data = vkgl.append(clinvar, ignore_index=True)
    print('ClinVar and VKGL combined.\n')

    # Freeing up memory
    del vkgl, clinvar
    gc.collect()

    # Checking for mismatching concensi
    ConsensusChecker().check_consensus_clinvar_vgkl_match(data)

    # Dropping duplicates
    DuplicateProcessor().process(data)

    # Applying sample weight
    SampleWeighter().apply_sample_weight(data)

    # Deviding into train-test and validation
    train_test, validation = SplitDatasets().split(data)

    # Freeing up memory
    del data
    gc.collect()

    # Exporting
    exporter = Exporter(output)
    exporter.export_validation_dataset(correct_order_vcf_notation(validation))
    exporter.export_train_test_dataset(train_test)


if __name__ == '__main__':
    main()
