import os
import unittest

import pandas as pd

from src.main.exporter import Exporter
from src.main.utilities import project_root_dir


class TestExporter(unittest.TestCase):
    __test_dir__ = os.path.join(project_root_dir, '.test_dir')

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
                'foo': [1, 2, 3],
                'bar': ['very', 'hot', 'fuzz']
            }
        )
        exporter.export_train_test_dataset(some_data)
        self.assertIn('train_test.tsv.gz', os.listdir(self.__test_dir__))
        exporter.export_validation_dataset(some_data)
        self.assertIn('validation.tsv.gz', os.listdir(self.__test_dir__))


if __name__ == '__main__':
    unittest.main()
