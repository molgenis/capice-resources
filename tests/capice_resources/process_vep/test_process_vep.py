import os
import unittest
from unittest.mock import patch

import pandas as pd

from molgenis.capice_resources.process_vep.__main__ import ProcessVEP
from tests.capice_resources.testing_utilities import get_testing_resources_dir, \
    check_and_remove_directory


class TestProcessVEP(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.processor = ProcessVEP()  # type: ignore

    def tearDown(self) -> None:
        directory = os.path.join(get_testing_resources_dir(), 'process_vep', 'output')
        for file in os.listdir(directory):
            check_and_remove_directory(os.path.join(directory, file))

    def test_load_train_features(self):
        """
        Test to check if a json with train_features is properly loaded and returned as a list.
        """
        observed = self.processor._read_train_features(
            os.path.join(get_testing_resources_dir(), 'features.json')
        )
        expected = ['feature1', 'feature2', 'feature3', 'foobar']
        self.assertListEqual(observed, expected)

    def test_load_cgd(self):
        """
        Test to check if the CGD txt is properly loaded and processed.
        CGD txt contains foo (AD), TENM1 (AR), bar (AR) and baz (AR/AD).
        foo is filtered out since it is not AR and TENM1 is filtered out because it can not be AR.
        TENM1: https://www.omim.org/entry/300588
        """
        observed = self.processor._read_cgd_data(
            os.path.join(get_testing_resources_dir(), 'cgd.txt.gz')
        )
        expected = ['bar', 'baz']
        self.assertListEqual(observed, expected)

    def test_extract_label_and_weight(self):
        """
        Test to check if the binarized_label and sample_weight are properly extracted from the ID
        column.
        """
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
        """
        Full component test of process-vep from CLI to export. Also tests if the "smallest" of
        the 2 output datasets contains at least a considerable amount of samples.
        """
        self.processor.run()
        output_path = os.path.join(get_testing_resources_dir(), 'process_vep', 'output')
        for expected_output_file in ['train_test.tsv.gz', 'validation.tsv.gz']:
            self.assertIn(
                expected_output_file,
                os.listdir(output_path)
            )
        self.assertNotIn('validation_filtered.tsv.gz', os.listdir(output_path))
        observed = pd.read_csv(  # type: ignore
            os.path.join(get_testing_resources_dir(), 'process_vep', 'output', 'validation.tsv.gz'),
            sep='\t'
        )
        self.assertGreaterEqual(observed.shape[0], 3000)
        self.assertNotIn('dataset_source', observed.columns)

    @patch(
        'sys.argv',
        [
            __file__,
            '-t', os.path.join(get_testing_resources_dir(), 'process_vep', 'train_test_vep.tsv.gz'),
            '-f', os.path.join(get_testing_resources_dir(), 'process_vep', 'train_features.json'),
            '-o', os.path.join(get_testing_resources_dir(), 'process_vep', 'output'),
            '-g', os.path.join(get_testing_resources_dir(), 'process_vep', 'CGD.txt.gz')
        ]
    )
    def test_component_process_vep_no_validation(self):
        """
        Full component test of process-vep from CLI to export, but without the optionally given
        validation dataset. Checks if the validation.tsv.gz is not created and if the output
        train_test.tsv.gz contains a considerable amount of samples.
        """
        self.processor.run()
        self.assertIn(
            'train_test.tsv.gz',
            os.listdir(
                os.path.join(
                    get_testing_resources_dir(),
                    'process_vep',
                    'output'
                )
            )
        )
        output_directory = os.path.join(get_testing_resources_dir(), 'process_vep', 'output')
        observed = pd.read_csv(  # type: ignore
            os.path.join(output_directory, 'train_test.tsv.gz'),
            sep='\t',
            low_memory=False
        )
        self.assertNotIn('validation.tsv.gz', os.listdir(output_directory))
        self.assertNotIn('validation_filtered.tsv.gz', os.listdir(output_directory))
        self.assertGreaterEqual(observed.shape[0], 10000)
        self.assertNotIn('dataset_source', observed.columns)

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
        """
        CLI test of process-vep to see if the GRCh38 flag is set to True when the flag is
        supplied on the command line.
        """
        observed = self.processor.parse_and_validate_cli()
        self.assertIn('assembly', observed.keys())
        self.assertTrue(observed['assembly'])

    @patch(
        'sys.argv',
        [
            __file__,
            '-t', os.path.join(get_testing_resources_dir(), 'process_vep', 'train_test_vep.tsv.gz'),
            '-v', os.path.join(get_testing_resources_dir(), 'process_vep', 'validation_vep.tsv.gz'),
            '-f', os.path.join(get_testing_resources_dir(), 'process_vep', 'train_features.json'),
            '-o', os.path.join(get_testing_resources_dir(), 'process_vep', 'output'),
            '-g', os.path.join(get_testing_resources_dir(), 'process_vep', 'CGD.txt.gz'),
            '-r', os.path.join(get_testing_resources_dir(), 'process_vep',
                               'train_test_vep_previous_iteration.tsv.gz')

        ]
    )
    def test_integration_filtered_validation(self):
        """
        Integration test to see if the filtered validation file gets produced properly and exported
        properly.
        """
        self.processor.run()
        output_path = os.path.join(get_testing_resources_dir(), 'process_vep', 'output')
        self.assertIn('train_test.tsv.gz', os.listdir(output_path))
        self.assertIn('validation.tsv.gz', os.listdir(output_path))
        self.assertIn('validation_filtered.tsv.gz', os.listdir(output_path))
        filtered_validation = pd.read_csv(
            os.path.join(output_path, 'validation_filtered.tsv.gz'),
            sep='\t'
        )
        previous_iteration_tt = pd.read_csv(
            os.path.join(
                get_testing_resources_dir(),
                'process_vep',
                'train_test_vep_previous_iteration.tsv.gz'
            ),
            sep='\t'
        )
        for identifier in previous_iteration_tt['ID'].values:
            self.assertNotIn(identifier, filtered_validation['ID'].values)

    def test_filtered_validation_pass(self):
        """
        Test to see if the new filter to filter out train-test variants of previous models
        functions properly.
        """
        test_validation = pd.DataFrame(
            {
                'CHROM': [1, 2, 3, 4, 'X'],
                'POS': [100, 200, 300, 400, 500],
                'REF': ['A', 'C', 'T', 'G', 'GC'],
                'ALT': ['C', 'A', 'G', 'T', 'CA'],
                'SYMBOL': ['FOO1', 'FOO2', 'FOO3', 'FOO4', 'FOO5'],
                'UniqueID': ['id1', 'id2', 'id3', 'id4', 'id5']
            }
        )
        test_previous_iteration = pd.DataFrame(
            {
                'CHROM': [1, 2, 4, 'X', 6],
                'POS': [100, 300, 400, 500, 600],
                'REF': ['A', 'A', 'G', 'C', 'GC'],
                'ALT': ['C', 'T', 'T', 'A', 'CA'],
                'SYMBOL': ['FOO1', 'FOO2', 'FOO4', 'FOO2', 'FOO6']
            }
        )
        observed = self.processor._process_previous_iteration(
            test_validation,
            test_previous_iteration
        )
        # Checking if the 2 identifiers that are duplicates are removed
        self.assertNotIn('id1', observed['UniqueID'].values)
        self.assertNotIn('id4', observed['UniqueID'].values)
        # Checking if the remainder of the identifiers are still present
        for identifier in ['id2', 'id3', 'id5']:
            self.assertIn(identifier, observed['UniqueID'].values)
        # Checking if observed has the right amount of samples
        self.assertEqual(observed.shape[0], 3)
        # Checking if the original validation is unaltered
        self.assertEqual(test_validation.shape[0], 5)

    def test_filtered_validation_none_pass(self):
        """
        Test to see if None gets returned with input None to the validation filter.
        """
        test_validation = pd.DataFrame(
            {
                'CHROM': [1, 2, 3, 4, 'X'],
                'POS': [100, 200, 300, 400, 500],
                'REF': ['A', 'C', 'T', 'G', 'GC'],
                'ALT': ['C', 'A', 'G', 'T', 'CA'],
                'SYMBOL': ['FOO1', 'FOO2', 'FOO3', 'FOO4', 'FOO5'],
                'UniqueID': ['id1', 'id2', 'id3', 'id4', 'id5']
            }
        )
        test_previous_iteration = None
        observed = self.processor._process_previous_iteration(
            test_validation,
            test_previous_iteration
        )
        self.assertIsNone(observed)
        # Checking if validation remains unaltered
        self.assertEqual(test_validation.shape[0], 5)


if __name__ == '__main__':
    unittest.main()
