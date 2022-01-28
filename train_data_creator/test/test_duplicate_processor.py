import unittest

import pandas as pd

from train_data_creator.src.main.duplicate_processor import DuplicateProcessor


class TestDuplicateProcessor(unittest.TestCase):
    def test_duplicate_processor(self):
        dataset = pd.DataFrame(
            {
                '#CHROM': [1, 1, 2],
                'POS': [100, 100, 200],
                'REF': ['A', 'A', 'G'],
                'ALT': ['T', 'T', 'C'],
                'gene': ['foo', 'foo', 'bar'],
                'class': ['LP', 'LP', 'LB'],
                'review': [2, 3, 1],
                'source': ['ClinVar', 'VKGL', 'VKGL'],
                'binarized_label': [1.0, 1.0, 0.0]
            }
        )
        processor = DuplicateProcessor()
        observed = processor.process(dataset)
        expected = pd.DataFrame(
            {
                '#CHROM': [1, 2],
                'POS': [100, 200],
                'REF': ['A', 'G'],
                'ALT': ['T', 'C'],
                'gene': ['foo', 'bar'],
                'class': ['LP', 'LB'],
                'review': [2, 1],
                'source': ['ClinVar', 'VKGL'],
                'binarized_label': [1.0, 0.0]
            }, index=[0, 2]
        )
        pd.testing.assert_frame_equal(observed, expected)


if __name__ == '__main__':
    unittest.main()
