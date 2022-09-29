#!/usr/bin/env python3

import pandas as pd

from validator import Validator
from calculator import ThresholdCalculator
from command_line_parser import CommandLineParser


def main():
    clp = CommandLineParser()
    validator = Validator()
    path_validation_raw = validator.validate_input_path(clp.get_argument('validation'))
    path_validation_score = validator.validate_input_path(clp.get_argument('score_validation'))
    ds_validation_raw = pd.read_csv(path_validation_raw, sep='\t', low_memory=False)
    ds_validation_score = pd.read_csv(path_validation_score, sep='\t', low_memory=False)
    validator.validate_sample_size_match(ds_validation_raw, ds_validation_score)
    calculator = ThresholdCalculator(ds_validation_raw, ds_validation_score)
    calculator.calculate_threshold()


if __name__ == '__main__':
    main()
