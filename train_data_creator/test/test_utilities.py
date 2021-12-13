import unittest

import pandas as pd

from src.main.utilities import correct_order_vcf_notation, equalize_class, apply_binarized_label


class TestUtilities(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dataset = pd.DataFrame(
            {
                '#CHROM': ['1', '2', '3', '4', '6', '7', '5', '8', '9'],
                'POS': [100, 200, 300, 600, 700, 400, 500, 800, 900],
                'REF': ['A', 'A', 'G', 'C', 'A', 'A', 'G', 'C', 'T'],
                'ALT': ['T', 'T', 'C', 'G', 'T', 'T', 'C', 'G', 'A'],
                'source': [
                    'VKGL', 'VKGL', 'ClinVar', 'VKGL', 'VKGL', 'ClinVar', 'ClinVar', 'ClinVar',
                    'ClinVar'
                ],
                'review': [2, 2, 1, 2, 2, 2, 3, 2, 1],
                'binarized_label': [1.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0.0, 1.0, 0.0]
            }
        )
        cls.class_dataset = pd.DataFrame(
            {
                'class': ['(Likely) Benign', 'LB', 'foo', 'Pathogenic']
             }
        )
        cls.equalize_dict = {'(Likely) Benign': 'LB', 'Pathogenic': 'P'}

    def test_order(self):
        observed = correct_order_vcf_notation(self.dataset)
        expected = pd.DataFrame(
            {
                '#CHROM': ['1', '2', '3', '4', '5', '6', '7', '8', '9'],
                'POS': [100, 200, 300, 600, 500, 700, 400, 800, 900],
                'REF': ['A', 'A', 'G', 'C', 'G', 'A', 'A', 'C', 'T'],
                'ALT': ['T', 'T', 'C', 'G', 'C', 'T', 'T', 'G', 'A'],
                'source': [
                    'VKGL', 'VKGL', 'ClinVar', 'VKGL', 'ClinVar', 'VKGL', 'ClinVar', 'ClinVar',
                    'ClinVar'
                ],
                'review': [2, 2, 1, 2, 3, 2, 2, 2, 1],
                'binarized_label': [1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0]
            }
        )
        pd.testing.assert_frame_equal(observed, expected)

    def test_equalize(self):
        observed = equalize_class(
            self.class_dataset, equalize_dict=self.equalize_dict
        )
        expected = pd.DataFrame(
            {
                'class': ['LB', 'P']
            }
        )
        pd.testing.assert_frame_equal(
            observed.reset_index(drop=True), expected.reset_index(drop=True)
        )

    def test_apply_binarized_label(self):
        copy_class_dataset = self.class_dataset.copy(deep=True)
        equalized = equalize_class(copy_class_dataset, self.equalize_dict)
        observed = apply_binarized_label(equalized)
        expected = pd.DataFrame(
            {
                'class': ['LB', 'P'],
                'binarized_label': [0.0, 1.0]
            }
        )
        pd.testing.assert_frame_equal(
            observed.reset_index(drop=True), expected.reset_index(drop=True)
        )


if __name__ == '__main__':
    unittest.main()
