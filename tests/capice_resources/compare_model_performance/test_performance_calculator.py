import unittest

import pandas as pd

from molgenis.capice_resources.core import ColumnEnums
from molgenis.capice_resources.compare_model_performance.performance_calculator import \
    PerformanceCalculator


class TestPerformanceCalculator(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dataset = pd.DataFrame(  # type: ignore
            {
                ColumnEnums.BINARIZED_LABEL.value: [1, 1, 0, 0],
                ColumnEnums.SCORE.value: [0.9, 0.1, 0.9, 0.1]
            }
        )
        cls.calculator = PerformanceCalculator()  # type: ignore

    def test_calculate_auc(self):
        """
        Perhaps a test specific to sklearn.metrics.roc_auc_score, but with correctly set column
        names.
        Test for incorrect column names is not required, as "binarized_label" and "score" are set
        in GlobalEnums and thus the same for all modules.
        """
        self.assertEqual(0.5, self.calculator.calculate_auc(self.dataset))

    def test_calculate_roc(self):
        """
        Perhaps a test specific to sklearn.metrics.roc_curve "FPR" and "TPR" outputs, combined
        with the call to "calculate_auc", set with correct column names.
        """
        observed = self.calculator.calculate_roc(self.dataset)
        self.assertTrue(isinstance(observed, tuple))
        self.assertListEqual(list(observed[0]), [0.0, 0.5, 1.0])
        self.assertListEqual(list(observed[1]), [0.0, 0.5, 1.0])
        self.assertEqual(observed[2], 0.5)


if __name__ == '__main__':
    unittest.main()
