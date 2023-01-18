import os
import unittest
from unittest.mock import patch

import pandas as pd
from matplotlib import pyplot as plt

from molgenis.capice_resources.core import GlobalEnums as Genums
from molgenis.capice_resources.threshold_calculator import ThresholdEnums
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
            ThresholdEnums.THRESHOLDS.value + '.tsv.gz',
            os.listdir(self.output_directory)
        )
        self.assertIn(
            ThresholdEnums.THRESHOLDS.value + '.png',
            os.listdir(self.output_directory)
        )
        expected = pd.read_csv(
            os.path.join(get_testing_resources_dir(), 'threshold_calculator', 'thresholds.tsv.gz'),
            sep=Genums.TSV_SEPARATOR.value
        )
        observed = pd.read_csv(
            os.path.join(self.output_directory, ThresholdEnums.THRESHOLDS.value + '.tsv.gz'),
            sep=Genums.TSV_SEPARATOR.value
        )
        pd.testing.assert_frame_equal(observed, expected)


if __name__ == '__main__':
    unittest.main()
