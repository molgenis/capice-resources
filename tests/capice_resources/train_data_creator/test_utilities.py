import unittest

import pandas as pd

from molgenis.capice_resources.train_data_creator.utilities import correct_order_vcf_notation, \
    apply_binarized_label


class TestUtilities(unittest.TestCase):
    def test_correct_order_vcf_notation(self):
        """
        Tests a complex order of CHROM and POS to the correct VCF notation.
        """
        test_set = pd.DataFrame(
            {
                '#CHROM': ['chr1', 'MT', 'chr3', 'chr3', 'chr5', 'chrY', 'chrX'],
                'POS': [100, 200, 300, 500, 400, 1000, 12000]
            }
        )
        correct_order_vcf_notation(test_set)
        expected = pd.DataFrame(
            {
                '#CHROM': ['chr1', 'MT', 'chr3', 'chr3', 'chr5', 'chrY', 'chrX'],
                'POS': [100, 400, 500, 300, 12000, 1000, 200]
            }
        )
        pd.testing.assert_frame_equal(test_set, expected)

    def test_apply_binarized_label(self):
        """
        Tests that LB and B get the correct binarized label of "0" and LP and P get the correct
        binarized label of "1". Also checks that unknown labels are removed.
        """
        test_case = pd.DataFrame(
            {
                'class': [
                    'LB', 'P', 'foobar', 'LP', 'B', 'VUS'
                ]
            }
        )
        apply_binarized_label(test_case)
        self.assertIn('binarized_label', test_case.columns)
        self.assertListEqual(
            list(test_case['binarized_label'].values),
            [0, 1, 1, 0]
        )


if __name__ == '__main__':
    unittest.main()
