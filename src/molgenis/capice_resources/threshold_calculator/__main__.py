import os

import pandas as pd

from molgenis.capice_resources.core import Module
from molgenis.capice_resources.core import GlobalEnums as Genums
from molgenis.capice_resources.threshold_calculator import ThresholdEnums as Menums
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
            '--output',
            type=str,
            required=True,
            help='Output directory where the output plot and thresholds TSV should be placed.'
        )

        return parser

    def _validate_module_specific_arguments(self, parser):
        validation = self.input_validator.validate_icli_file(
            parser.get_argument('validation'),
            Genums.TSV_EXTENSIONS.value
        )
        score = self.input_validator.validate_icli_file(
            parser.get_argument('score'),
            Genums.TSV_EXTENSIONS.value
        )
        output = self.input_validator.validate_ocli_directory(
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
            [Genums.BINARIZED_LABEL.value]
        )
        score = self._read_pandas_tsv(
            arguments['score'],
            [Genums.SCORE.value]
        )
        merge = pd.concat([validation, score], axis=1)
        thresholds = Calculator().calculate_threshold(merge)
        plotter = ThresholdPlotter(thresholds)
        figure = plotter.plot_threshold(merge)
        return {
            Genums.OUTPUT.value: arguments['output'],
            Menums.THRESHOLDS.value: thresholds,
            Menums.FIGURE.value: figure
        }

    def export(self, output):
        self.exporter.export_pandas_file(
            output[Genums.OUTPUT.value],
            output[Menums.THRESHOLDS.value]
        )
        output[Menums.FIGURE.value].savefig(  # type: ignore
            os.path.join(  # type: ignore
                output[Genums.OUTPUT.value],
                Menums.THRESHOLDS.value + '.png'
            )
        )


def main():
    ThresholdCalculator().run()


if __name__ == '__main__':
    main()
