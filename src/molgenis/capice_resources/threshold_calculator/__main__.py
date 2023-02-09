import os

import pandas as pd

from molgenis.capice_resources.core import Module, TSVFileEnums, ColumnEnums, DatasetIdentifierEnums
from molgenis.capice_resources.threshold_calculator import ThresholdEnums
from molgenis.capice_resources.threshold_calculator.calculator import Calculator
from molgenis.capice_resources.threshold_calculator.plotter import ThresholdPlotter


class ThresholdCalculator(Module):
    def __init__(self):
        super(ThresholdCalculator, self).__init__(
            program='Calculate thresholds',
            description='Calculate thresholds based on Li et al. (2020), which is'
                        'based on a recall score between 94 to 96%.'
        )

    @staticmethod
    def _create_module_specific_arguments(parser):
        required = parser.add_argument_group('Required arguments')

        required.add_argument(
            '-v',
            '--validation',
            type=str,
            required=True,
            help='Input location of the initial validation dataset.'
        )

        required.add_argument(
            '-s',
            '--score',
            type=str,
            required=True,
            help='Input location of the scores dataset.'
        )

        required.add_argument(
            '-o',
            '--output',
            type=str,
            required=True,
            help='Output directory where the output plot and thresholds TSV should be placed.'
        )

        return parser

    def _validate_module_specific_arguments(self, parser):
        validation = self.input_validator.validate_input_command_line_interface_file(
            parser.get_argument('validation'),
            TSVFileEnums.TSV_EXTENSIONS.value
        )
        score = self.input_validator.validate_input_command_line_interface_file(
            parser.get_argument('score'),
            TSVFileEnums.TSV_EXTENSIONS.value
        )
        output = self.input_validator.validate_output_command_line_interface_path(
            parser.get_argument('output')
        )
        return {
            **validation,
            **score,
            **output
        }

    def run_module(self, arguments):
        validation = self._read_pandas_tsv(
            arguments['validation'],
            [ColumnEnums.BINARIZED_LABEL.value]
        )
        score = self._read_pandas_tsv(
            arguments['score'],
            [ColumnEnums.SCORE.value]
        )
        merge = pd.concat([validation, score], axis=1)
        thresholds = Calculator().calculate_threshold(merge)
        plotter = ThresholdPlotter(thresholds)
        figure = plotter.plot_threshold(merge)
        return {
            DatasetIdentifierEnums.OUTPUT.value: arguments['output'],
            ThresholdEnums.THRESHOLDS.value: thresholds,
            ThresholdEnums.FIGURE.value: figure
        }

    def export(self, output):
        self.exporter.export_pandas_file(
            os.path.join(  # type: ignore
                output[DatasetIdentifierEnums.OUTPUT.value],
                ThresholdEnums.THRESHOLDS.value + '.tsv.gz'
            ),
            output[ThresholdEnums.THRESHOLDS.value]
        )
        output[ThresholdEnums.FIGURE.value].savefig(  # type: ignore
            os.path.join(  # type: ignore
                output[DatasetIdentifierEnums.OUTPUT.value],
                ThresholdEnums.THRESHOLDS.value + '.png'
            )
        )


def main():
    ThresholdCalculator().run()


if __name__ == '__main__':
    main()
