import unittest

import pandas as pd

from molgenis.capice_resources.core import GlobalEnums as Genums
from molgenis.capice_resources.train_data_creator import TrainDataCreatorEnums as Menums
from molgenis.capice_resources.train_data_creator.utilities import correct_order_vcf_notation, \
    apply_binarized_label


class TestUtilities(unittest.TestCase):
    def test_correct_order_vcf_notation(self):
        test_set = pd.DataFrame(
            {
                Genums.VCF_CHROM.value: [1, 'MT', 5, 3, 3, 'Y', 'X'],
                Genums.POS.value: [100, 200, 300, 500, 400, 1000, 12000]
            }
        )
        correct_order_vcf_notation(test_set)
        expected = pd.DataFrame(
            {
                Genums.VCF_CHROM.value: [1, 3, 3, 5, 'X', 'Y', 'MT'],
                Genums.POS.value: [100, 400, 500, 300, 12000, 1000, 200]
            }
        )
        pd.testing.assert_frame_equal(test_set, expected)

    def test_apply_binarized_label(self):
        test_case = pd.DataFrame(
            {
                Menums.CLASS.value: [
                    'LB', 'P', 'foobar', 'LP', 'B', 'VUS'
                ]
            }
        )
        apply_binarized_label(test_case)
        self.assertIn(Genums.BINARIZED_LABEL.value, test_case.columns)
        self.assertListEqual(
            list(test_case[Genums.BINARIZED_LABEL.value].values),
            [0, 1, 1, 0]
        )


if __name__ == '__main__':
    unittest.main()
