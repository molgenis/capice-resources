import unittest

import pandas as pd
from molgenis.capice_resources.compare_model_features.ranker import Ranker
from molgenis.capice_resources.compare_model_features.orderer import Orderer
from molgenis.capice_resources.compare_model_features.normalizer import Normalizer
from molgenis.capice_resources.compare_model_features.__main__ import CompareModelFeatures


class TestCompareModelsExplain(unittest.TestCase):
    def setUp(self):
        self.valid_input = pd.DataFrame(data={
            'feature': ['phyloP', 'SIFTval', 'PolyPhenVal', 'Grantham'],
            'gain': [197.3686981201172, 39.576637268066406, 38.426273345947266, 9.386235237121582],
            'total_gain': [79934.3203125, 6728.0283203125, 9068.6005859375, 1436.093994140625],
            'weight': [405.0, 170.0, 236.0, 153.0],
            'cover': [1705.604736328125, 958.0835571289062, 1129.3902587890625, 1309.001220703125],
            'total_cover': [690769.9375, 162874.203125, 266536.09375, 200277.1875]
        })

    def test_normalize_column(self):
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

    def test_add_ranking_column(self):
        expected_output = pd.DataFrame(data={
            'feature': ['phyloP', 'SIFTval', 'PolyPhenVal', 'Grantham'],
            'gain': [197.3686981201172, 39.576637268066406, 38.426273345947266, 9.386235237121582],
            'total_gain': [79934.3203125, 6728.0283203125, 9068.6005859375, 1436.093994140625],
            'weight': [405.0, 170.0, 236.0, 153.0],
            'weight_rank': [1, 3, 2, 4],
            'cover': [1705.604736328125, 958.0835571289062, 1129.3902587890625, 1309.001220703125],
            'total_cover': [690769.9375, 162874.203125, 266536.09375, 200277.1875]
        })
        Ranker().add_rank(self.valid_input, column_name='weight')

        pd.testing.assert_frame_equal(expected_output, self.valid_input)

    def test_table_merge(self):
        expected_output = pd.DataFrame(data={
            'feature': ['phyloP', 'SIFTval', 'PolyPhenVal', 'Grantham'],
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
        actual_output = CompareModelFeatures()._merge_explains(self.valid_input, self.valid_input)

        pd.testing.assert_frame_equal(expected_output, actual_output)

    def test_reorder_table(self):
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

    def test_process_table(self):
        expected_output = pd.DataFrame(data={
            'feature': ['phyloP', 'SIFTval', 'PolyPhenVal', 'Grantham'],
            'gain': [197.3686981201172, 39.576637268066406, 38.426273345947266, 9.386235237121582],
            'gain_normalized': [1.4797369, -0.3707318, -0.3842225, -0.7247826],
            'gain_normalized_rank': [1, 2, 3, 4],
            'total_gain': [79934.3203125, 6728.0283203125, 9068.6005859375, 1436.093994140625],
            'weight': [405.0, 170.0, 236.0, 153.0],
            'cover': [1705.604736328125, 958.0835571289062, 1129.3902587890625, 1309.001220703125],
            'total_cover': [690769.9375, 162874.203125, 266536.09375, 200277.1875]
        })

        CompareModelFeatures()._process_explain(self.valid_input)

        pd.testing.assert_frame_equal(expected_output, self.valid_input)