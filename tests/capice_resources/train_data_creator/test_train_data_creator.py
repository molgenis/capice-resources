import os
import gzip
import unittest
from unittest.mock import patch

import pandas as pd

from molgenis.capice_resources.core import GlobalEnums as Genums
from tests.capice_resources.testing_utilities import get_testing_resources_dir, \
    check_and_remove_directory
from molgenis.capice_resources.train_data_creator.__main__ import TrainDataCreator


class TestTrainDataCreator(unittest.TestCase):
    output_directory = os.path.join(
        get_testing_resources_dir(),
        'train_data_creator',
        'output'
        )

    @classmethod
    def tearDownClass(cls) -> None:
        check_and_remove_directory(os.path.join(cls.output_directory, 'train_test.vcf.gz'))
        check_and_remove_directory(os.path.join(cls.output_directory, 'validation.vcf.gz'))

    @patch(
        'sys.argv',
        [
            __file__,
            '-v', os.path.join(
                        get_testing_resources_dir(),
                        'train_data_creator',
                        'smol_vkgl.tsv.gz'
                        ),
            '-c', os.path.join(
                        get_testing_resources_dir(),
                        'train_data_creator',
                        'smol_clinvar.vcf.gz'
                        ),
            '-o', output_directory
        ]
    )
    def test_component(self):
        TrainDataCreator().run()
        filepath_train_test = os.path.join(self.output_directory, 'train_test.vcf.gz')
        filepath_validation = os.path.join(self.output_directory, 'validation.vcf.gz')
        for file in [filepath_train_test, filepath_validation]:
            filename = os.path.basename(file)
            self.assertIn(
                filename,
                os.listdir(self.output_directory),
                msg=f'{filename} not found in {self.output_directory}'
            )
            n_header_lines = 0
            with gzip.open(file, 'rt') as fh:
                for line in fh:
                    if line.startswith('##'):
                        n_header_lines += 1
                    else:
                        break
            self.assertEqual(n_header_lines, 27)
        tt = pd.read_csv(
            filepath_train_test,
            sep='\t',
            skiprows=27,
            na_values=Genums.NA_VALUES.value
        )
        self.assertGreaterEqual(
            tt.shape[0],
            99
        )
        val = pd.read_csv(
            filepath_validation,
            sep='\t',
            skiprows=27,
            na_values=Genums.NA_VALUES.value
        )
        self.assertGreaterEqual(
            val.shape[0],
            6
        )


if __name__ == '__main__':
    unittest.main()
