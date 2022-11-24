import os
import unittest

import pandas as pd

from train_data_creator.tests import get_project_root_dir
from train_data_creator.src.main.exporter import Exporter


class TestExporter(unittest.TestCase):
    __test_dir__ = os.path.join(get_project_root_dir(), '.test_dir')

    @classmethod
    def tearDownClass(cls) -> None:
        for file in os.listdir(cls.__test_dir__):
            os.remove(os.path.join(cls.__test_dir__, file))
        os.rmdir(cls.__test_dir__)

    def test_exporter(self):
        if not os.path.isdir(self.__test_dir__):
            os.makedirs(self.__test_dir__)
        exporter = Exporter(self.__test_dir__)
        some_data = pd.DataFrame(
            {
                '#CHROM': [1, 2, 3],
                'POS': [100, 200, 300],
                'REF': ['A', 'A', 'A'],
                'ALT': ['C', 'C', 'C'],
                'gene': ['very', 'hot', 'fuzz'],
                'binarized_label': [1, 2, 3],
                'sample_weight': [0.8, 0.9, 1.0]
            }
        )
        exporter.export_train_test_dataset(some_data)
        self.assertIn('train_test.vcf.gz', os.listdir(self.__test_dir__))
        exporter.export_validation_dataset(some_data)
        self.assertIn('validation.vcf.gz', os.listdir(self.__test_dir__))


if __name__ == '__main__':
    unittest.main()
