import os
import unittest

import pandas as pd
from matplotlib.pyplot import Figure

from molgenis.capice_resources.core import GlobalEnums
from molgenis.capice_resources.threshold_calculator import ThresholdEnums
from tests.capice_resources.test_utilities import get_testing_resources_dir
from molgenis.capice_resources.threshold_calculator.__main__ import ThresholdCalculator


class TestCalculator(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.calculator = ThresholdCalculator()

    def test_component_calculator(self):
        input_scores = {
            'score': os.path.join(
                get_testing_resources_dir(),
                'threshold_calculator', 'scores.tsv.gz'
            )
        }
        input_labels = {
            'validation': os.path.join(
                get_testing_resources_dir(),
                'threshold_calculator', 'labels.tsv.gz'
            )
        }
        output = {
            GlobalEnums.OUTPUT.value: 'fake'
        }
        observed = self.calculator.run_module({**input_scores, **input_labels, **output})
        self.assertTrue(isinstance(observed[ThresholdEnums.FIGURE.value], Figure))
        expected = pd.read_csv(
            os.path.join(get_testing_resources_dir(), 'threshold_calculator', 'thresholds.tsv.gz'),
            sep='\t'
        )
        pd.testing.assert_frame_equal(observed[ThresholdEnums.THRESHOLDS.value], expected)


if __name__ == '__main__':
    unittest.main()
