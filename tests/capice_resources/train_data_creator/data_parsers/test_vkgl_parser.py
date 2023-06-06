import os
import unittest

import numpy as np
import pandas as pd

from tests.capice_resources.testing_utilities import get_testing_resources_dir
from molgenis.capice_resources.train_data_creator.data_parsers.vkgl import VKGLParser


class TestVKGLParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dataset = pd.read_csv(  # type: ignore
            os.path.join(
                get_testing_resources_dir(),
                'train_data_creator',
                'smol_vkgl_may2023.tsv.gz'
            ),
            sep='\t'
        )
        cls.parser = VKGLParser()  # type: ignore

    def test_component_parser(self):
        """
        Component test of the VKGL parser.
        Tests if the ModuleEnums.columns_of_interest() are all present, binarized_label and if
        the source is set correctly.
        """
        observed = self.parser.parse(self.dataset)
        self.assertIsNone(observed._is_copy)
        for col in [
            '#CHROM',
            'POS',
            'REF',
            'ALT',
            'gene',
            'class',
            'review',
            'dataset_source'
        ]:
            self.assertIn(col, observed.columns)
        self.assertIn('binarized_label', observed.columns)
        self.assertListEqual(
            list(observed['dataset_source'].unique()),
            ['VKGL']
        )

    def test_correct_columns_names(self):
        """
        Tests if the correction and equalizing of column names is performed correctly.
        """
        test_case = pd.DataFrame(
            columns=['chromosome', 'start', 'ref', 'alt', 'classification', 'other_column']
        )
        self.parser._correct_column_names(test_case)
        self.assertListEqual(
            list(test_case.columns),
            ['#CHROM', 'POS', 'REF', 'ALT', 'class', 'other_column']
        )

    def test_correct_support(self):
        """
        Tests if splitting the object "X labs" is split correctly into numerical "X".
        """
        test_case = pd.DataFrame(
            {
                'support': ['5 labs', '1 lab', '3 labs']
            }
        )
        self.parser._correct_support(test_case)
        self.assertTrue(
            test_case['support'].dtype == np.int64,
            msg=f'Actual dtype: {test_case["support"].dtype}'
        )
        self.assertListEqual(
            list(test_case['support'].values),
            [5, 1, 3]
        )

    def test_apply_review_status(self):
        """
        Tests if the support status is correctly converted to the review score.
        """
        test_case = pd.DataFrame(
            {
                'support': [
                    1, 2, 3, 4
                ]
            }
        )
        self.assertNotIn('review', test_case.columns)
        self.parser._apply_review_status(test_case)
        self.assertIn('review', test_case.columns)
        self.assertListEqual(
            list(test_case['review'].values),
            [2, 2, 2, 2]
        )

    def test_unsupported_contig(self):
        test_case = pd.DataFrame(
            {
                'chromosome': ['1', 'MT', 'FOOBAR'],
                'start': [100, 200, 300],
                'ref': ['A', 'C', 'G'],
                'alt': ['T', 'G', 'C'],
                'gene': ['foo', 'bar', 'baz'],
                'classification': ['LB', 'LP', 'P'],
                'support': ['4 labs', '3 labs', '2 labs']
            }
        )
        with self.assertWarns(UserWarning) as c:
            observed = self.parser.parse(test_case)
        self.assertNotIn('FOOBAR', list(observed['#CHROM'].values))
        self.assertEqual('Removing unsupported contig for 1 variant(s).', str(c.warning))


if __name__ == '__main__':
    unittest.main()
