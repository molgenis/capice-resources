import unittest

import numpy as np
import pandas as pd

from molgenis.capice_resources.core import GlobalEnums

from molgenis.capice_resources.compare_model_performance.performance_calculator import \
    PerformanceCalculator


class TestPerformanceCalculator(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dataset = pd.DataFrame(
            {
                GlobalEnums.BINARIZED_LABEL.value: [1, 1, 0, 0],
                GlobalEnums.SCORE.value: [0.9, 0.1, 0.9, 0.1]
            }
        )
        cls.calculator = PerformanceCalculator()

    def test_calculate_auc(self):
        self.assertEqual(0.5, self.calculator.calculate_auc(self.dataset))

    def test_calculate_roc(self):
        observed = self.calculator.calculate_roc(self.dataset)
        self.assertTrue(isinstance(observed, tuple))
        self.assertListEqual(list(observed[0]), [0.0 , 0.5, 1.0])
        self.assertListEqual(list(observed[1]), [0.0 , 0.5, 1.0])
        self.assertEqual(observed[2], 0.5)


if __name__ == '__main__':
    unittest.main()
