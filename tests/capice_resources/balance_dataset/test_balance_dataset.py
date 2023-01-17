import os
import unittest
from unittest.mock import patch

import pandas as pd

from molgenis.capice_resources.core import GlobalEnums as Genums
from tests.capice_resources.testing_utilities import get_testing_resources_dir, \
    check_and_remove_directory
from molgenis.capice_resources.balance_dataset.__main__ import BalanceDataset


class TestBalanceDataset(unittest.TestCase):
    output_directory = os.path.join(
        get_testing_resources_dir(),
        'balance_dataset',
        'output'
    )

    @classmethod
    def tearDownClass(cls) -> None:
        check_and_remove_directory(
            os.path.join(cls.output_directory, 'balanced.tsv.gz')
        )
        check_and_remove_directory(
            os.path.join(cls.output_directory, 'remainder.tsv.gz')
        )

    @patch(
        'sys.argv',
        [
            __file__,
            '-i', os.path.join(get_testing_resources_dir(), 'labels.tsv.gz'),
            '-o', output_directory
        ]
    )
    def test_component(self):
        BalanceDataset().run()
        filepath_balanced = os.path.join(self.output_directory, 'balanced.tsv.gz')
        filepath_remainder = os.path.join(self.output_directory, 'remainder.tsv.gz')
        for file in [filepath_balanced, filepath_remainder]:
            self.assertIn(os.path.basename(file), os.listdir(self.output_directory))
        balanced = pd.read_csv(
            filepath_balanced,
            sep='\t',
            na_values=Genums.NA_VALUES.value
        )
        self.assertGreaterEqual(
            balanced.shape[0],
            100
        )
        remainder = pd.read_csv(
            filepath_remainder,
            sep='\t',
            na_values=Genums.NA_VALUES.value
        )
        self.assertGreaterEqual(
            remainder.shape[0],
            200
        )
        self.assertGreater(
            remainder.shape[0],
            balanced.shape[0]
        )


if __name__ == '__main__':
    unittest.main()
