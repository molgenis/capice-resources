import unittest

import pandas as pd

from molgenis.capice_resources.core import GlobalEnums as Genums
from molgenis.capice_resources.train_data_creator import TrainDataCreatorEnums as Menums
from molgenis.capice_resources.train_data_creator.consensus_checker import ConsensusChecker


class TestConsensusChecker(unittest.TestCase):
    def setUp(self) -> None:
        self.consensus_checker = ConsensusChecker()
        self.variants_passed = pd.DataFrame(
            {
                Genums.VCF_CHROM.value: [1, 1, 1, 1, 1, 1],
                Genums.POS.value: [300, 400, 500, 600, 700, 700],
                Genums.REF.value: ['A', 'A', 'A', 'A', 'G', 'G'],
                Genums.ALT.value: ['T', 'T', 'T', 'T', 'C', 'C'],
                Menums.GENE.value: ['foo', 'foo', 'foo', 'foo', 'bar', 'bar'],
                Menums.CLASS.value: ['LP', 'LP', 'LP', 'LP', 'LB', 'LB'],
                Menums.REVIEW.value: [2, 3, 2, 3, 2, 2],
                Genums.DATASET_SOURCE.value: ['CLINVAR', 'VKGL', 'CLINVAR', 'VKGL', 'CLINVAR', 'VKGL'],
                Genums.BINARIZED_LABEL.value: [1.0, 1.0, 0.0, 1.0, 0.0, 0.0],
            }
        )

    def test_3_mismatch(self):
        dataset = pd.DataFrame(
            {
                Genums.VCF_CHROM.value: [
                    1, 1, 1, 1, 2, 2
                ],
                Genums.POS.value: [
                    100, 100, 200, 200, 200, 200
                ],
                Genums.REF.value: [
                    'A', 'A', 'G', 'G', 'C', 'C'
                ],
                Genums.ALT.value: [
                    'T', 'T', 'C', 'C', 'G', 'G'
                ],
                Menums.GENE.value: [
                    'foo', 'foo', 'bar', 'bar', 'baz', 'baz'
                ],
                Menums.CLASS.value: [
                    'LP', 'LB', 'LB', 'LP', 'LP', 'LB'
                ],
                Menums.REVIEW.value: [
                    2, 3, 2, 3, 2, 3
                ],
                Genums.DATASET_SOURCE.value: [
                    'CLINVAR', 'VKGL', 'CLINVAR', 'VKGL', 'CLINVAR', 'VKGL'
                ],
                Genums.BINARIZED_LABEL.value: [
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
            self.consensus_checker.check_consensus_clinvar_vkgl_match(
                input_dataset)
        self.assertEqual(
            'Removed 3 variant(s) due to mismatch in consensus',
            str(cm.warning)
        )
        pd.testing.assert_frame_equal(input_dataset, self.variants_passed)

    def test_no_mismatch(self):
        copy_variants_passed = self.variants_passed.copy(deep=True)
        self.consensus_checker.check_consensus_clinvar_vkgl_match(copy_variants_passed)
        pd.testing.assert_frame_equal(copy_variants_passed, self.variants_passed)


if __name__ == '__main__':
    unittest.main()
