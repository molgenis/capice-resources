import os
import unittest
from unittest.mock import patch

import pandas as pd

from molgenis.capice_resources.core import GlobalEnums
from molgenis.capice_resources.process_vep.__main__ import ProcessVEP
from tests.capice_resources.testing_utilities import get_testing_resources_dir, \
    check_and_remove_directory


class TestProcessVEP(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.processor = ProcessVEP()

    @classmethod
    def tearDownClass(cls) -> None:
        directory = os.path.join(get_testing_resources_dir(), 'process_vep', 'output')
        for file in os.listdir(directory):
            check_and_remove_directory(os.path.join(directory, file))

    def test_load_train_features(self):
        observed = self.processor._read_train_features(
            os.path.join(get_testing_resources_dir(), 'features.json'
                         )
        )
        expected = ['feature1', 'feature2', 'feature3', 'foobar']
        self.assertListEqual(observed, expected)

    def test_load_cgd(self):
        observed = self.processor._read_cgd_data(
            os.path.join(get_testing_resources_dir(), 'cgd.txt.gz')
        )
        expected = ['bar', 'baz']
        self.assertListEqual(observed, expected)

    def test_extract_label_and_weight(self):
        test_case = pd.DataFrame(
            {
                'ID': ['1!1!A!G!foo!0!0.8', '1!1!A!G!foo!1!0.5']
            }
        )
        self.processor.extract_label_and_weight(test_case)
        self.assertIn('binarized_label', test_case.columns)
        self.assertIn('sample_weight', test_case.columns)
        self.assertIn(0, test_case['binarized_label'].values)
        self.assertIn(0.5, test_case['sample_weight'].values)

    @patch(
        'sys.argv',
        [
            __file__,
            '-t', os.path.join(get_testing_resources_dir(), 'process_vep', 'train_test_vep.tsv.gz'),
            '-v', os.path.join(get_testing_resources_dir(), 'process_vep', 'validation_vep.tsv.gz'),
            '-f', os.path.join(get_testing_resources_dir(), 'process_vep', 'train_features.json'),
            '-o', os.path.join(get_testing_resources_dir(), 'process_vep', 'output'),
            '-g', os.path.join(get_testing_resources_dir(), 'process_vep', 'CGD.txt.gz')
        ]
    )
    def test_component_process_vep(self):
        self.processor.run()
        for expected_output_file in ['train_test.tsv.gz', 'validation.tsv.gz']:
            self.assertIn(
                expected_output_file,
                os.listdir(
                    os.path.join(
                        get_testing_resources_dir(),
                        'process_vep',
                        'output'
                    )
                )
            )
        observed = pd.read_csv(
            os.path.join(get_testing_resources_dir(), 'process_vep', 'output','validation.tsv.gz'),
            sep='\t'
        )
        self.assertGreaterEqual(observed.shape[0], 3000)
        self.assertNotIn(GlobalEnums.DATASET_SOURCE.value, observed.columns)

    @patch(
        'sys.argv',
        [
            __file__,
            '-t', os.path.join(get_testing_resources_dir(), 'process_vep', 'train_test_vep.tsv.gz'),
            '-v', os.path.join(get_testing_resources_dir(), 'process_vep', 'validation_vep.tsv.gz'),
            '-f', os.path.join(get_testing_resources_dir(), 'process_vep', 'train_features.json'),
            '-o', os.path.join(get_testing_resources_dir(), 'process_vep', 'output'),
            '-g', os.path.join(get_testing_resources_dir(), 'process_vep', 'CGD.txt.gz'),
            '-a'
        ]
    )
    def test_build38_flag(self):
        observed = self.processor.parse_and_validate_cli()
        self.assertIn('assembly', observed.keys())
        self.assertTrue(observed['assembly'])


if __name__ == '__main__':
    unittest.main()
