import unittest

import pandas as pd
from train_data_creator.src.main.consensus_check import ConsensusChecker


class TestConsensusCheck(unittest.TestCase):
    def setUp(self) -> None:
        self.consensus_checker = ConsensusChecker()
        self.variants_passed = pd.DataFrame(
            {
                '#CHROM': [1, 1, 1, 1, 1, 1],
                'POS': [300, 400, 500, 600, 700, 700],
                'REF': ['A', 'A', 'A', 'A', 'G', 'G'],
                'ALT': ['T', 'T', 'T', 'T', 'C', 'C'],
                'gene': ['foo', 'foo', 'foo', 'foo', 'bar', 'bar'],
                'class': ['LP', 'LP', 'LP', 'LP', 'LB', 'LB'],
                'review': [2, 3, 2, 3, 2, 2],
                'source': ['ClinVar', 'VKGL', 'ClinVar', 'VKGL', 'ClinVar', 'VKGL'],
                'binarized_label': [1.0, 1.0, 0.0, 1.0, 0.0, 0.0],
            }
        )

    def test_3_mismatch(self):
        dataset = pd.DataFrame(
            {
                '#CHROM': [
                    1, 1, 1, 1, 2, 2
                ],
                'POS': [
                    100, 100, 200, 200, 200, 200
                ],
                'REF': [
                    'A', 'A', 'G', 'G', 'C', 'C'
                ],
                'ALT': [
                    'T', 'T', 'C', 'C', 'G', 'G'
                ],
                'gene': [
                    'foo', 'foo', 'bar', 'bar', 'baz', 'baz'
                ],
                'class': [
                    'LP', 'LB', 'LB', 'LP', 'LP', 'LB'
                ],
                'review': [
                    2, 3, 2, 3, 2, 3
                ],
                'source': [
                    'ClinVar', 'VKGL', 'ClinVar', 'VKGL', 'ClinVar', 'VKGL'
                ],
                'binarized_label': [
                    1.0, 0.0, 0.0, 1.0, 1.0, 0.0
                ]
            }
        )
        input_dataset = pd.concat(
            [
                dataset,
                self.variants_passed
            ], axis=0, copy=False, ignore_index=True
        )
        with self.assertWarns(UserWarning) as cm:
            self.consensus_checker.check_consensus_clinvar_vgkl_match(
                input_dataset)
        self.assertEqual(
            'There are 3 variants with mismatching consensus between ClinVar and VKGL',
            str(cm.warning)
        )
        pd.testing.assert_frame_equal(input_dataset.reset_index(drop=True), self.variants_passed)

    def test_no_mismatch(self):
        copy_variants_passed = self.variants_passed.copy(deep=True)
        self.consensus_checker.check_consensus_clinvar_vgkl_match(copy_variants_passed)
        pd.testing.assert_frame_equal(copy_variants_passed, self.variants_passed)


if __name__ == '__main__':
    unittest.main()
