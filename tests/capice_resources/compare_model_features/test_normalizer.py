import unittest

import pandas as pd

from tests.capice_resources.compare_model_features import valid_input
from molgenis.capice_resources.compare_model_features.normalizer import Normalizer


class TestNormalizer(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_input = valid_input()

    def test_normalize_column(self):
        """
        Very sensitive test to see if the Z score normalizer performs as expected on "gain".
        """
        expected_output = pd.DataFrame(data={
            'feature': ['phyloP', 'SIFTval', 'PolyPhenVal', 'Grantham'],
            'gain': [197.3686981201172, 39.576637268066406, 38.426273345947266, 9.386235237121582],
            'gain_normalized': [1.4797369, -0.3707318, -0.3842225, -0.7247826],
            'total_gain': [79934.3203125, 6728.0283203125, 9068.6005859375, 1436.093994140625],
            'weight': [405.0, 170.0, 236.0, 153.0],
            'cover': [1705.604736328125, 958.0835571289062, 1129.3902587890625, 1309.001220703125],
            'total_cover': [690769.9375, 162874.203125, 266536.09375, 200277.1875]
        })
        Normalizer().normalize_column(self.valid_input, column_name='gain')

        pd.testing.assert_frame_equal(expected_output, self.valid_input)


if __name__ == '__main__':
    unittest.main()
