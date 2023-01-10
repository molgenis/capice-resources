import os
import unittest

import numpy as np
import pandas as pd

from molgenis.capice_resources.core import GlobalEnums as Genums
from tests.capice_resources.testing_utilities import get_testing_resources_dir
from molgenis.capice_resources.train_data_creator.data_parsers.vkgl import VKGLParser
from molgenis.capice_resources.train_data_creator import TrainDataCreatorEnums as Menums


class TestVKGLParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dataset = pd.read_csv(
            os.path.join(get_testing_resources_dir(), 'train_data_creator', 'smol_vkgl.tsv.gz'),
            sep='\t'
        )
        cls.parser = VKGLParser()

    def test_component_parser(self):
        observed = self.parser.parse(self.dataset)
        self.assertIsNone(observed._is_copy)
        for col in Menums.columns_of_interest():
            self.assertIn(col, observed.columns)
        self.assertIn(Genums.BINARIZED_LABEL.value, observed.columns)
        self.assertListEqual(
            list(observed[Genums.DATASET_SOURCE.value].unique()),
            [Menums.VKGL.value]
        )

    def test_correct_columns_names(self):
        test_case = pd.DataFrame(
            columns=['chromosome', 'start', 'ref', 'alt', 'classification', 'other_column']
        )
        self.parser._correct_column_names(test_case)
        self.assertListEqual(
            list(test_case.columns),
            ['#CHROM', 'POS', 'REF', 'ALT', 'class', 'other_column']
        )

    def test_correct_support(self):
        test_case = pd.DataFrame(
            {
                Menums.SUPPORT.value: ['5 labs', '1 lab', '3 labs']
            }
        )
        self.parser._correct_support(test_case)
        self.assertTrue(
            test_case[Menums.SUPPORT.value].dtype == np.int64,
            msg=f'Actual dtype: {test_case[Menums.SUPPORT.value].dtype}'
        )
        self.assertListEqual(
            list(test_case[Menums.SUPPORT.value].values),
            [5, 1, 3]
        )

    def test_apply_review_status(self):
        test_case = pd.DataFrame(
            {
                Menums.SUPPORT.value: [
                    1, 2, 3, 4
                ]
            }
        )
        self.assertNotIn(Menums.REVIEW.value, test_case.columns)
        self.parser._apply_review_status(test_case)
        self.assertIn(Menums.REVIEW.value, test_case.columns)
        self.assertListEqual(
            list(test_case[Menums.REVIEW.value].values),
            [1, 2, 2, 2]
        )


if __name__ == '__main__':
    unittest.main()
