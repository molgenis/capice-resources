import os
import unittest
from unittest.mock import patch

import pandas as pd

from tests.capice_resources.compare_model_features import valid_input
from tests.capice_resources.testing_utilities import check_and_remove_directory, \
    get_testing_resources_dir
from molgenis.capice_resources.compare_model_features.__main__ import CompareModelFeatures


class TestCompareModelsExplain(unittest.TestCase):
    output_path = os.path.join(
        get_testing_resources_dir(),
        'compare_model_features',
        'output',
        'output.tsv.gz'
    )

    def setUp(self) -> None:
        self.valid_input = valid_input()

    @classmethod
    def tearDownClass(cls) -> None:
        check_and_remove_directory(cls.output_path)

    def test_table_merge(self):
        """
        Test to see if 2 fully processed (normalized, ranked, ordered) are merged properly,
        assigning the correct suffix to the models.
        """
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

    def test_process_table(self):
        """
        Component test that checks if normalizer and ranker are correctly applied within
        _process_explain().
        """
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

    @patch(
        'sys.argv',
        [
            __file__,
            '-a',
            os.path.join(get_testing_resources_dir(), 'compare_model_features', 'example.tsv.gz'),
            '-b',
            os.path.join(get_testing_resources_dir(), 'compare_model_features', 'example.tsv.gz'),
            '-o', output_path,
        ]
    )
    def test_component_compare_model_features(self):
        required_features = pd.read_csv(
            os.path.join(get_testing_resources_dir(), 'compare_model_features', 'example.tsv.gz'),
            sep='\t',
            usecols=['feature']
        )
        CompareModelFeatures().run()
        output = pd.read_csv(
            self.output_path,
            sep='\t'
        )
        for feature in required_features['feature'].values:
            self.assertIn(feature, output['feature'].values)


if __name__ == '__main__':
    unittest.main()
