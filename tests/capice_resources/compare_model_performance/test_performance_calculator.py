import unittest
import math

import numpy as np
import pandas as pd

from molgenis.capice_resources.compare_model_performance.performance_calculator import \
    PerformanceCalculator


class TestPerformanceCalculator(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dataset = pd.DataFrame(  # type: ignore
            {
                'binarized_label': [1, 1, 0, 0],
                'score': [0.9, 0.1, 0.9, 0.1]
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
        self._validate_correct_roc_auc_values(observed)

    def test_calculate_roc_auc_values_ignore_true(self):
        """
        Tests if correct ROC and AUC values are returned if "ignore_zero_sample_error" is set to
        True.
        """
        calculator = PerformanceCalculator(True)
        observed = calculator.calculate_roc(self.dataset)
        self._validate_correct_roc_auc_values(observed)

    def _validate_correct_roc_auc_values(self, observed):
        """
        Utility function te reduce code duplication checking for correct ROC and AUC values.
        """
        self.assertTrue(isinstance(observed, tuple))
        self.assertListEqual(list(observed[0]), [0.0, 0.5, 1.0])
        self.assertListEqual(list(observed[1]), [0.0, 0.5, 1.0])
        self.assertEqual(observed[2], 0.5)

    def test_calculate_roc_empty_input_error_ignore_false(self):
        """
        Tests if ValueError is correctly raised when calculate ROC is supplied with an empty series.
        """
        testcase = pd.DataFrame(columns=self.dataset.columns)
        with self.assertRaises(ValueError) as e:
            self.calculator.calculate_roc(testcase)
        self.assertEqual(
            str(e.exception),
            "y_true takes value in {} and pos_label is not specified: "
            "either make y_true take value in {0, 1} or {-1, 1} or "
            "pass pos_label explicitly."
        )

    def test_calculate_roc_alternative_raise(self):
        """
        Tests if an alternative raise to the caught ValueError will still be raised properly.
        """
        calculator = PerformanceCalculator(True)
        test_case = pd.DataFrame(
            {
                'binarized_label': [np.nan, 0, 1],
                'score': [0.01, 0.05, 0.99]
            }
        )
        with self.assertWarns(RuntimeWarning)as w, self.assertRaises(ValueError) as e:
            calculator.calculate_roc(test_case)
        self.assertEqual(
            str(e.exception),
            'Input y_true contains NaN.'
        )
        self.assertEqual(
            str(w.warning),
            'invalid value encountered in cast'
        )

    def test_calculate_auc_empty_input_error_ignore_false(self):
        testcase = pd.DataFrame(columns=self.dataset.columns)
        with self.assertRaises(ValueError) as e:
            self.calculator.calculate_auc(testcase)
        self.assertEqual(
            str(e.exception),
            "Found array with 0 sample(s) (shape=(0,)) "
            "while a minimum of 1 is required."
        )

    def test_calculate_roc_empty_input_nan_ignore_true(self):
        """
        Tests if all output values of calculate_roc are NaN when supplied with an empty input
        and ignore_zero_sample_error is set to True.
        """
        testcase = pd.DataFrame(columns=self.dataset.columns)
        calculator = PerformanceCalculator(True)
        observed = calculator.calculate_roc(testcase)
        for value in observed:
            self.assertTrue(math.isnan(value))

    def test_calculate_auc_empty_input_nan_ignore_true(self):
        """
        Tests if the output of calculate_auc is NaN when supplied with an empty input and
        ignore_zero_sample_error is set to True.
        """
        testcase = pd.DataFrame(columns=self.dataset.columns)
        calculator = PerformanceCalculator(True)
        observed = calculator.calculate_auc(testcase)
        self.assertTrue(math.isnan(observed))


if __name__ == '__main__':
    unittest.main()
