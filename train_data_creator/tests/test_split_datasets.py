import unittest

import pandas as pd

from train_data_creator.src.main.split_datasets import SplitDatasets


class TestSplitDatasets(unittest.TestCase):
    def test_split(self):
        dataset = pd.DataFrame(
            {
                '#CHROM': ['1', '2', '4', '5', '6', '7', '8', '10'],
                'POS': [100, 200, 400, 500, 600, 700, 800, 1000],
                'REF': ['A', 'A', 'C', 'A', 'A', 'G', 'C', 'CG'],
                'ALT': ['T', 'T', 'G', 'T', 'T', 'C', 'G', 'AT'],
                'source': [
                    'VKGL', 'VKGL', 'VKGL', 'VKGL', 'ClinVar', 'ClinVar', 'ClinVar', 'VKGL'
                ],
                'review': [2, 2, 2, 2, 2, 3, 2, 2],
                'sample_weight': [0.9, 0.9, 0.9, 0.9, 0.9, 1.0, 0.9, 0.9],
                'binarized_label': [1.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0, 0.0]
            }
        )
        splitter = SplitDatasets()
        observed_train, observed_validation = splitter.split(dataset)
        self.assertEqual(
            observed_validation[observed_validation['binarized_label'] == 1.0].shape[0],
            observed_validation[observed_validation['binarized_label'] == 0.0].shape[0]
        )
        self.assertGreater(
            observed_validation['review'].min(), 1
        )
        for row in observed_validation.iterrows():
            self.assertNotIn(observed_train.values.tolist(), row[1].values.tolist())


if __name__ == '__main__':
    unittest.main()
