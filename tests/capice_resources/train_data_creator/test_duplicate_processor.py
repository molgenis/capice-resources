import unittest

import pandas as pd

from molgenis.capice_resources.core import GlobalEnums as Genums
from molgenis.capice_resources.train_data_creator import TrainDataCreatorEnums as Menums
from molgenis.capice_resources.train_data_creator.duplicate_processor import DuplicateProcessor


class TestDuplicateProcessor(unittest.TestCase):
    def test_duplicate_processor(self):
        """
        Test that ensure proper function of the DuplicateProcessor that one of the duplicates
        present remains.
        """
        dataset = pd.DataFrame(
            {
                Genums.VCF_CHROM.value: [1, 1, 2],
                Genums.POS.value: [100, 100, 200],
                Genums.REF.value: ['A', 'A', 'G'],
                Genums.ALT.value: ['T', 'T', 'C'],
                Menums.GENE.value: ['foo', 'foo', 'bar'],
                Menums.CLASS.value: ['LP', 'LP', 'LB'],
                Menums.REVIEW.value: [2, 3, 1],
                Genums.DATASET_SOURCE.value: ['ClinVar', 'VKGL', 'VKGL'],
                Genums.BINARIZED_LABEL.value: [1.0, 1.0, 0.0]
            }
        )
        processor = DuplicateProcessor()
        self.assertIn(1, dataset.index)
        processor.process(dataset)
        self.assertNotIn(1, dataset.index)


if __name__ == '__main__':
    unittest.main()
