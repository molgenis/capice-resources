import os
import unittest
from unittest.mock import patch

import pandas as pd
from matplotlib import pyplot as plt

from tests.capice_resources.testing_utilities import get_testing_resources_dir, \
    check_and_remove_directory
from molgenis.capice_resources.threshold_calculator.__main__ import ThresholdCalculator


class TestCalculator(unittest.TestCase):
    output_directory = os.path.join(get_testing_resources_dir(), 'threshold_calculator', 'output')

    @classmethod
    def tearDownClass(cls) -> None:
        for file in os.listdir(cls.output_directory):
            check_and_remove_directory(os.path.join(cls.output_directory, file))

    def tearDown(self) -> None:
        """
        plt.close('all') is required, as matplotlib keeps all figures loaded. With the amount of
        matplotlib related tests in capice-resources, matplotlib does throw an warning that too
        many figures are loaded unless this call is made.
        """
        plt.close('all')

    @patch(
        'sys.argv',
        [
            __file__,
            '-v', os.path.join(get_testing_resources_dir(), 'labels.tsv.gz'),
            '-s', os.path.join(get_testing_resources_dir(), 'scores.tsv.gz'),
            '-o', output_directory
        ]
    )
    def test_component_calculator(self):
        """
        Expanded component test of threshold-calculator, since the statistics and metrics within
        this module are complex, only a single test exists.

        Does test if all files are output properly and if the output tsv is as expected.
        """
        ThresholdCalculator().run()
        self.assertIn(
            'thresholds.tsv.gz',
            os.listdir(self.output_directory)
        )
        self.assertIn(
            'thresholds.png',
            os.listdir(self.output_directory)
        )
        expected = pd.read_csv(
            os.path.join(get_testing_resources_dir(), 'threshold_calculator', 'thresholds.tsv.gz'),
            sep='\t'
        )
        observed = pd.read_csv(
            os.path.join(self.output_directory, 'thresholds.tsv.gz'),
            sep='\t'
        )
        pd.testing.assert_frame_equal(observed, expected)

    @patch(
        'sys.argv',
        [
            __file__,
            '-v', os.path.join(get_testing_resources_dir(), 'labels.tsv.gz'),
            '-s', os.path.join(get_testing_resources_dir(), 'scores.tsv.gz'),
            '-o', output_directory
        ]
    )
    def test_plotter_correct_size_dpi(self):
        module = ThresholdCalculator()
        args = module.parse_and_validate_cli()
        plot = module.run_module(args)['figure']
        self.assertEqual(100, plot.dpi)
        self.assertTupleEqual((0, 1), plot.axes[0].get_ylim())


if __name__ == '__main__':
    unittest.main()
