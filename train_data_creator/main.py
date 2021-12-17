#!/usr/bin/env python3

import gc

from src.main.exporter import Exporter
from src.main.split_datasets import SplitDatasets
from src.main.sample_weighter import SampleWeighter
from src.main.data_preprocessor import VKGL, ClinVar
from src.main.utilities import correct_order_vcf_notation
from src.main.command_line_parser import CommandLineParser
from src.main.duplicate_processor import DuplicateProcessor
from src.main.validators.input_validator import InputValidator


def main():
    # Parse command line
    print('Parsing command line arguments.')
    clp = CommandLineParser()
    input_vkgl = clp.get_argument('input_vkgl')[0]
    input_clinvar = clp.get_argument('input_clinvar')[0]
    output = clp.get_argument('output')[0]
    # Validate
    print('Validating input arguments.')
    validator = InputValidator()
    validator.validate_vkgl(input_vkgl)
    validator.validate_clinvar(input_clinvar)
    validator.validate_output(output)
    # Parse
    print('Parsing VKGL.')
    vkgl = VKGL().parse(input_vkgl)
    print('Parsing ClinVar.')
    clinvar = ClinVar().parse(input_clinvar)

    # Combine
    print('Combining ClinVar and VKGL')
    data = vkgl.append(clinvar, ignore_index=True)

    # Freeing up memory
    del vkgl, clinvar
    gc.collect()

    # Dropping duplicates
    data = DuplicateProcessor().process(data)

    # Applying sample weight
    data = SampleWeighter().apply_sample_weight(data)

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
