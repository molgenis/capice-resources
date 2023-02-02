import unittest

import pandas as pd

from molgenis.capice_resources.train_data_creator.duplicate_processor import DuplicateProcessor


class TestDuplicateProcessor(unittest.TestCase):
    def test_duplicate_processor(self):
        """
        Test that ensure proper function of the DuplicateProcessor that one of the duplicates
        present remains.
        """
        dataset = pd.DataFrame(
            {
                '#CHROM': [1, 1, 2],
                'POS': [100, 100, 200],
                'REF': ['A', 'A', 'G'],
                'ALT': ['T', 'T', 'C'],
                'gene': ['foo', 'foo', 'bar'],
                'class': ['LP', 'LP', 'LB'],
                'review': [2, 3, 1],
                'dataset_source': ['ClinVar', 'VKGL', 'VKGL'],
                'binarized_label': [1.0, 1.0, 0.0]
            }
        )
        processor = DuplicateProcessor()
        self.assertIn(1, dataset.index)
        processor.process(dataset)
        self.assertNotIn(1, dataset.index)


if __name__ == '__main__':
    unittest.main()
