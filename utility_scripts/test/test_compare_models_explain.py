import unittest

import pandas as pd
import utility_scripts.compare_models_explain as explain


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
        actual_output = explain.normalize_column(self.valid_input, column_name='gain')

        pd.testing.assert_frame_equal(expected_output, actual_output)

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
        actual_output = explain.add_column_ranking(self.valid_input, column_name='weight')

        pd.testing.assert_frame_equal(expected_output, actual_output)

    def test_table_merge(self):
        expected_output = pd.DataFrame(data={
            'feature': ['phyloP', 'SIFTval', 'PolyPhenVal', 'Grantham'],
            'gain_e1': [197.3686981201172, 39.576637268066406, 38.426273345947266,
                        9.386235237121582],
            'total_gain_e1': [79934.3203125, 6728.0283203125, 9068.6005859375, 1436.093994140625],
            'weight_e1': [405.0, 170.0, 236.0, 153.0],
            'cover_e1': [1705.604736328125, 958.0835571289062, 1129.3902587890625,
                         1309.001220703125],
            'total_cover_e1': [690769.9375, 162874.203125, 266536.09375, 200277.1875],
            'gain_e2': [197.3686981201172, 39.576637268066406, 38.426273345947266,
                        9.386235237121582],
            'total_gain_e2': [79934.3203125, 6728.0283203125, 9068.6005859375, 1436.093994140625],
            'weight_e2': [405.0, 170.0, 236.0, 153.0],
            'cover_e2': [1705.604736328125, 958.0835571289062, 1129.3902587890625,
                         1309.001220703125],
            'total_cover_e2': [690769.9375, 162874.203125, 266536.09375, 200277.1875]
        })
        actual_output = explain.join_tables(self.valid_input, self.valid_input)

        pd.testing.assert_frame_equal(expected_output, actual_output)

    def test_reorder_table(self):
        input_table = pd.DataFrame(data={
            'feature': ['phyloP', 'SIFTval', 'PolyPhenVal', 'Grantham'],
            'gain_e1': [197.3686981201172, 39.576637268066406, 38.426273345947266,
                        9.386235237121582],
            'gain_rank_e1': [1, 2, 3, 4],
            'total_gain_e1': [79934.3203125, 6728.0283203125, 9068.6005859375, 1436.093994140625],
            'weight_e1': [405.0, 170.0, 236.0, 153.0],
            'weight_rank_e1': [1, 3, 2, 4],
            'cover_e1': [1705.604736328125, 958.0835571289062, 1129.3902587890625,
                         1309.001220703125],
            'total_cover_e1': [690769.9375, 162874.203125, 266536.09375, 200277.1875],
            'gain_e2': [197.3686981201172, 39.576637268066406, 38.426273345947266,
                        9.386235237121582],
            'gain_rank_e2': [1, 2, 3, 4],
            'total_gain_e2': [79934.3203125, 6728.0283203125, 9068.6005859375, 1436.093994140625],
            'weight_e2': [405.0, 170.0, 236.0, 153.0],
            'weight_rank_e2': [1, 3, 2, 4],
            'cover_e2': [1705.604736328125, 958.0835571289062, 1129.3902587890625,
                         1309.001220703125],
            'total_cover_e2': [690769.9375, 162874.203125, 266536.09375, 200277.1875]
        })

        expected_output = pd.DataFrame(data={
            'feature': ['phyloP', 'SIFTval', 'PolyPhenVal', 'Grantham'],
            'gain_rank_e1': [1, 2, 3, 4],
            'gain_rank_e2': [1, 2, 3, 4],
            'weight_rank_e1': [1, 3, 2, 4],
            'weight_rank_e2': [1, 3, 2, 4],
            'gain_e1': [197.3686981201172, 39.576637268066406, 38.426273345947266,
                        9.386235237121582],
            'total_gain_e1': [79934.3203125, 6728.0283203125, 9068.6005859375, 1436.093994140625],
            'weight_e1': [405.0, 170.0, 236.0, 153.0],
            'cover_e1': [1705.604736328125, 958.0835571289062, 1129.3902587890625,
                         1309.001220703125],
            'total_cover_e1': [690769.9375, 162874.203125, 266536.09375, 200277.1875],
            'gain_e2': [197.3686981201172, 39.576637268066406, 38.426273345947266,
                        9.386235237121582],
            'total_gain_e2': [79934.3203125, 6728.0283203125, 9068.6005859375, 1436.093994140625],
            'weight_e2': [405.0, 170.0, 236.0, 153.0],
            'cover_e2': [1705.604736328125, 958.0835571289062, 1129.3902587890625,
                         1309.001220703125],
            'total_cover_e2': [690769.9375, 162874.203125, 266536.09375, 200277.1875]
        })
        actual_output = explain.reorder_columns(input_table)

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

        actual_output = explain.process_table(self.valid_input)

        pd.testing.assert_frame_equal(expected_output, actual_output)
