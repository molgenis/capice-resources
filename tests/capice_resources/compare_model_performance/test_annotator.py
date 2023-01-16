import unittest

import pandas as pd

from molgenis.capice_resources.core import GlobalEnums
from molgenis.capice_resources.compare_model_performance import CompareModelPerformanceEnums as \
    Menums
from molgenis.capice_resources.compare_model_performance.annotator import Annotator


class TestCMPAnnotator(unittest.TestCase):
    def setUp(self) -> None:
        self.annotator = Annotator()
        self.dataset = pd.DataFrame(
            {
                GlobalEnums.SCORE.value: [0.9, 0.8, 0.7, 0.6],
                GlobalEnums.BINARIZED_LABEL.value: [1, 0, 1, 0],
                GlobalEnums.GNOMAD_AF.value: [0.9, None, None, 0.0]
            }
        )

    def test_add_score_difference(self):
        """
        Tests if SCORE_DIFF column gets added and if the scores match to expectation.

        Rounded because of rounding errors.
        """
        self.annotator.add_score_difference(self.dataset)
        self.assertIn(Menums.SCORE_DIFF.value, self.dataset.columns)
        self.assertListEqual(
            list(self.dataset[Menums.SCORE_DIFF.value].values.round(1)),
            [0.1, 0.8, 0.3, 0.6]
        )

    def test_add_and_process_impute_af(self):
        self.annotator.add_and_process_impute_af(self.dataset)
        self.assertIn(Menums.IMPUTED.value, self.dataset.columns)
        self.assertListEqual(
            list(self.dataset[Menums.IMPUTED.value].values),
            [False, True, True, False]
        )

    def test_add_model_identifier(self):
        self.annotator.add_model_identifier(self.dataset, 'testing_purposes')
        self.assertIn(Menums.MODEL_IDENTIFIER.value, self.dataset.columns)
        self.assertEqual(
            self.dataset[Menums.MODEL_IDENTIFIER.value].unique(), 'testing_purposes'
        )


if __name__ == '__main__':
    unittest.main()
