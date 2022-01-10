#!/usr/bin/env python3

import pickle

import pandas as pd

from src.main.global_auc import GlobalAUC
from src.main.consequence_auc import ConsequenceAUC
from src.main.command_line_parser import CommandLineParser
from src.main.validators.data_validator import DataValidator
from src.main.validators.input_validator import InputValidator

def main():
    print('Parsing command line.')
    clp = CommandLineParser()
    input_old_model = clp.get_argument('input_old_model_data')
    input_new_model = clp.get_argument('input_new_model_data')
    output = clp.get_argument('output')

    print('Validating input arguments.')
    validator = InputValidator()
    validator.validate_data(input_old_model)
    validator.validate_data(input_new_model)
    validator.validate_output(output)
    print('Arguments passed.')

    print('Loading data.')
    old_data = pd.read_csv(input_old_model, sep='\t')
    new_data = pd.read_csv(input_new_model, sep='\t')

    print('Validating data.')
    validator = DataValidator()
    validator.validate_capice_data(old_data)
    validator.validate_capice_data(new_data)

    print('Plotting results.')
    module = GlobalAUC(input_old_model, input_new_model, output)
    module.compare(old_data, new_data)
    module = ConsequenceAUC(input_old_model, input_new_model, output)
    module.compare(old_data, new_data)


if __name__ == '__main__':
    main()
