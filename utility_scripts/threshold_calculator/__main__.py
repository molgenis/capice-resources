#!/usr/bin/env python3

import pandas as pd

from validator import Validator
from plotter import ThresholdPlotter
from exporter import ThresholdExporter
from calculator import ThresholdCalculator
from command_line_parser import CommandLineParser
from enums import RequiredValidationColumns, RequiredScoreColumns


def main():
    clp = CommandLineParser()
    validator = Validator()
    path_validation_raw = validator.validate_input_path(clp.get_argument('validation'))
    path_validation_score = validator.validate_input_path(clp.get_argument('score_validation'))
    path_output = validator.validate_output_argument(clp.get_argument('output'))
    ds_validation_raw = validator.validate_columns_dataset(
        pd.read_csv(
            path_validation_raw,
            sep='\t',
            low_memory=False
        ),
        RequiredValidationColumns.list()
    )
    ds_validation_score = validator.validate_columns_dataset(
        pd.read_csv(
            path_validation_score,
            sep='\t',
            low_memory=False
        ),
        RequiredScoreColumns.list()
    )
    validator.validate_sample_size_match(ds_validation_raw, ds_validation_score)
    dataset = pd.concat([ds_validation_raw, ds_validation_score], axis=1)
    result = ThresholdCalculator().calculate_threshold(dataset)
    exporter = ThresholdExporter(path_output)
    exporter.export_thresholds(result)
    plotter = ThresholdPlotter(result)
    figure = plotter.plot_threshold(dataset)
    exporter.export_plot(figure)


if __name__ == '__main__':
    main()
