import unittest
from unittest.mock import patch
from io import StringIO

import pandas as pd

from molgenis.capice_resources.process_vep.progress_printer import ProgressPrinter


class TestProgressPrinter(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    def test_progress_printer(self, stdout):
        test_case = pd.DataFrame(
            {
                'variant': ['var1', 'var2', 'var3'],
                'dataset_source': ['train_test', 'train_test', 'validation']
            }
        )
        printer = ProgressPrinter(test_case)
        test_case.drop(index=1, inplace=True)
        printer.new_shape(test_case)
        printer.print_final_shape()
        self.assertIn('Dropped 1 variants from train_test', stdout.getvalue())
        self.assertIn('Dropped 0 variants from validation', stdout.getvalue())
        self.assertIn('Final number of samples in train_test: 1', stdout.getvalue())
        self.assertIn('Final number of samples in validation: 1', stdout.getvalue())


if __name__ == '__main__':
    unittest.main()
