import unittest

import pandas as pd

from molgenis.capice_resources.compare_model_features.orderer import Orderer


class TestOrderer(unittest.TestCase):
    def test_reorder_table(self):
        """
        Test to see if the columns of a merged explanation between model 1 and model 2 are
        properly reordered. Also, that the ordering of indexes are done properly.
        """
        input_table = pd.DataFrame(data={
            'feature': ['phyloP', 'SIFTval', 'PolyPhenVal', 'Grantham'],
            'gain_model1': [197.3686981201172, 39.576637268066406, 38.426273345947266,
                            9.386235237121582],
            'gain_rank_model1': [1, 2, 3, 4],
            'total_gain_model1': [79934.3203125, 6728.0283203125, 9068.6005859375,
                                  1436.093994140625],
            'weight_model1': [405.0, 170.0, 236.0, 153.0],
            'weight_rank_model1': [1, 3, 2, 4],
            'cover_model1': [1705.604736328125, 958.0835571289062, 1129.3902587890625,
                             1309.001220703125],
            'total_cover_model1': [690769.9375, 162874.203125, 266536.09375, 200277.1875],
            'gain_model2': [197.3686981201172, 39.576637268066406, 38.426273345947266,
                            9.386235237121582],
            'gain_rank_model2': [1, 2, 3, 4],
            'total_gain_model2': [79934.3203125, 6728.0283203125, 9068.6005859375,
                                  1436.093994140625],
            'weight_model2': [405.0, 170.0, 236.0, 153.0],
            'weight_rank_model2': [1, 3, 2, 4],
            'cover_model2': [1705.604736328125, 958.0835571289062, 1129.3902587890625,
                             1309.001220703125],
            'total_cover_model2': [690769.9375, 162874.203125, 266536.09375, 200277.1875]
        })

        expected_output = pd.DataFrame(data={
            'feature': ['phyloP', 'SIFTval', 'PolyPhenVal', 'Grantham'],
            'gain_rank_model1': [1, 2, 3, 4],
            'gain_rank_model2': [1, 2, 3, 4],
            'weight_rank_model1': [1, 3, 2, 4],
            'weight_rank_model2': [1, 3, 2, 4],
            'gain_model1': [197.3686981201172, 39.576637268066406, 38.426273345947266,
                            9.386235237121582],
            'total_gain_model1': [79934.3203125, 6728.0283203125, 9068.6005859375,
                                  1436.093994140625],
            'weight_model1': [405.0, 170.0, 236.0, 153.0],
            'cover_model1': [1705.604736328125, 958.0835571289062, 1129.3902587890625,
                             1309.001220703125],
            'total_cover_model1': [690769.9375, 162874.203125, 266536.09375, 200277.1875],
            'gain_model2': [197.3686981201172, 39.576637268066406, 38.426273345947266,
                            9.386235237121582],
            'total_gain_model2': [79934.3203125, 6728.0283203125, 9068.6005859375,
                                  1436.093994140625],
            'weight_model2': [405.0, 170.0, 236.0, 153.0],
            'cover_model2': [1705.604736328125, 958.0835571289062, 1129.3902587890625,
                             1309.001220703125],
            'total_cover_model2': [690769.9375, 162874.203125, 266536.09375, 200277.1875]
        })
        actual_output = Orderer().order(input_table)

        pd.testing.assert_frame_equal(expected_output, actual_output)


if __name__ == '__main__':
    unittest.main()
