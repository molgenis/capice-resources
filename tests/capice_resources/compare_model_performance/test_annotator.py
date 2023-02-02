import unittest

import pandas as pd

from molgenis.capice_resources.compare_model_performance.annotator import Annotator


class TestAnnotator(unittest.TestCase):
    def setUp(self) -> None:
        self.annotator = Annotator()
        self.dataset = pd.DataFrame(
            {
                'score': [0.9, 0.8, 0.7, 0.6],
                'binarized_label': [1, 0, 1, 0],
                'gnomAD_AF': [0.9, None, None, 0.0]
            }
        )

    def test_add_score_difference(self):
        """
        Tests if SCORE_DIFF column gets added and if the scores match to expectation.

        Rounded because of rounding errors.
        """
        self.annotator.add_score_difference(self.dataset)
        self.assertIn('score_diff', self.dataset.columns)
        self.assertListEqual(
            list(self.dataset['score_diff'].values.round(1)),
            [0.1, 0.8, 0.3, 0.6]
        )

    def test_add_and_process_impute_af(self):
        """
        Test to see if the IMPUTED tag is correctly applied to all nan samples.
        """
        self.annotator.add_and_process_impute_af(self.dataset)
        self.assertIn('is_imputed', self.dataset.columns)
        self.assertListEqual(
            list(self.dataset['is_imputed'].values),
            [False, True, True, False]
        )


if __name__ == '__main__':
    unittest.main()
