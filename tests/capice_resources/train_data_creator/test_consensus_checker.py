import unittest

import pandas as pd

from molgenis.capice_resources.train_data_creator.consensus_checker import ConsensusChecker


class TestConsensusChecker(unittest.TestCase):
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
                'dataset_source': ['CLINVAR', 'VKGL', 'CLINVAR', 'VKGL', 'CLINVAR', 'VKGL'],
                'binarized_label': [1.0, 1.0, 0.0, 1.0, 0.0, 0.0],
            }
        )

    def test_3_mismatch(self):
        """
        Tests if 6 variants are filtered out that are the same between ClinVar and VKGL,
        but have a different classification label. Shows up as 3, since it are 3 "unique" variants.
        """
        dataset = pd.DataFrame(
            {
                '#CHROM': [1, 1, 1, 1, 2, 2],
                'POS': [100, 100, 200, 200, 200, 200],
                'REF': ['A', 'A', 'G', 'G', 'C', 'C'],
                'ALT': ['T', 'T', 'C', 'C', 'G', 'G'],
                'gene': ['foo', 'foo', 'bar', 'bar', 'baz', 'baz'],
                'class': ['LP', 'LB', 'LB', 'LP', 'LP', 'LB'],
                'review': [2, 3, 2, 3, 2, 3],
                'dataset_source': ['CLINVAR', 'VKGL', 'CLINVAR', 'VKGL', 'CLINVAR', 'VKGL'],
                'binarized_label': [1.0, 0.0, 0.0, 1.0, 1.0, 0.0]
            }
        )
        input_dataset = pd.concat(
            [
                dataset,
                self.variants_passed
            ], axis=0, copy=False, ignore_index=True
        )
        with self.assertWarns(UserWarning) as cm:
            self.consensus_checker.check_consensus_clinvar_vkgl_match(
                input_dataset)
        self.assertEqual(
            'Removed 3 variant(s) due to mismatch in consensus',
            str(cm.warning)
        )
        pd.testing.assert_frame_equal(input_dataset, self.variants_passed)

    def test_no_mismatch(self):
        """
        Tests the situation when the consensus checker encounters a situation where no variants
        have to be filtered out due to mismatching label.
        """
        copy_variants_passed = self.variants_passed.copy(deep=True)
        self.consensus_checker.check_consensus_clinvar_vkgl_match(copy_variants_passed)
        pd.testing.assert_frame_equal(copy_variants_passed, self.variants_passed)

    def test_mixed_dtypes_consensus_mismatch(self):
        """
        Tests that if 2 frames of different dtypes are appended, containing consensus mismatch,
        still gets processed properly.
        """
        clinvar_frame = pd.DataFrame(
            {
                '#CHROM': [1, 1],
                'POS': [100, 200],
                'REF': ['C', 'T'],
                'ALT': ['G', 'A'],
                'gene': ['foo', 'bar'],
                'dataset_source': ['CLINVAR', 'CLINVAR'],
                'binarized_label': [1.0, 0.0],
                'unique_id': ['uid1', 'uid2']
            }
        )
        vkgl_frame = pd.DataFrame(
            {
                '#CHROM': [1, 'X'],
                'POS': [100, 200],
                'REF': ['C', 'T'],
                'ALT': ['G', 'A'],
                'gene': ['foo', 'baz'],
                'dataset_source': ['VKGL', 'VKGL'],
                'binarized_label': [0.0, 0.0],
                'unique_id': ['uid3', 'uid4']
            }
        )
        test_case = pd.concat([clinvar_frame, vkgl_frame], axis=0, ignore_index=True)
        with self.assertWarns(UserWarning) as cm:
            self.consensus_checker.check_consensus_clinvar_vkgl_match(
                test_case)
        self.assertEqual(
            'Removed 1 variant(s) due to mismatch in consensus',
            str(cm.warning)
        )
        self.assertNotIn('uid1', test_case['unique_id'].values)
        self.assertNotIn('uid3', test_case['unique_id'].values)


if __name__ == '__main__':
    unittest.main()
