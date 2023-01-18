import unittest

import pandas as pd

from molgenis.capice_resources.core import GlobalEnums as Genums
from molgenis.capice_resources.train_data_creator import TrainDataCreatorEnums as Menums
from molgenis.capice_resources.train_data_creator.dataset_splitter import SplitDatasets


class TestSplitDatasets(unittest.TestCase):
    def test_split(self):
        """
        Tests if the train-test and validation splitter performs as expected. Unique IDentifiers
        are added to ensure that samples are in 1 dataset but not the other.
        """
        dataset = pd.DataFrame(
            {
                Genums.VCF_CHROM.value: ['1', '2', '4', '5', '6', '7', '8', '10'],
                Genums.POS.value: [100, 200, 400, 500, 600, 700, 800, 1000],
                Genums.REF.value: ['A', 'A', 'C', 'A', 'A', 'G', 'C', 'CG'],
                Genums.ALT.value: ['T', 'T', 'G', 'T', 'T', 'C', 'G', 'AT'],
                Genums.DATASET_SOURCE.value: [
                    'VKGL', 'VKGL', 'VKGL', 'VKGL', 'CLINVAR', 'CLINVAR', 'CLINVAR', 'VKGL'
                ],
                Menums.REVIEW.value: [2, 2, 2, 2, 2, 3, 2, 2],
                Genums.SAMPLE_WEIGHT.value: [0.9, 0.9, 0.9, 0.9, 0.9, 1.0, 0.9, 0.9],
                Genums.BINARIZED_LABEL.value: [1.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0, 0.0],
                'unique_id': ['fooa', 'foob', 'fooc', 'food', 'fooe', 'foof', 'foog', 'fooh']
            }
        )
        splitter = SplitDatasets()
        observed_train, observed_validation = splitter.split(dataset)
        self.assertEqual(
            observed_validation[observed_validation[Genums.BINARIZED_LABEL.value] == 1.0].shape[0],
            observed_validation[observed_validation[Genums.BINARIZED_LABEL.value] == 0.0].shape[0]
        )
        self.assertGreater(
            observed_validation[Menums.REVIEW.value].min(), 1
        )
        for uid in observed_train['unique_id'].values:
            self.assertNotIn(
                uid,
                observed_validation['unique_id'].values
            )
        for uid in observed_validation['unique_id'].values:
            self.assertNotIn(
                uid,
                observed_train['unique_id'].values
            )


if __name__ == '__main__':
    unittest.main()
