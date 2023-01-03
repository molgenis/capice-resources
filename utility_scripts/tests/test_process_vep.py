import unittest
from unittest.mock import patch
import os
from pathlib import Path
from io import StringIO

import pandas as pd

from utility_scripts.process_vep_tsv import Validator, read_json, read_dataset, merge_data, \
    drop_duplicates, drop_genes_empty, ProgressPrinter, process_grch38, drop_duplicate_entries, \
    drop_mismatching_genes, drop_heterozygous_variants_in_ar_genes, \
    drop_variants_incorrect_label_or_weight, extract_label_and_weight, load_and_correct_cgd


class TestProcessVEP(unittest.TestCase):
    test_resources_directory = os.path.join(
        Path(__file__).absolute().parent, 'resources')
    incorrect_extension_filepath = os.path.join(test_resources_directory, 'some_other_file.txt')

    @classmethod
    def setUpClass(cls) -> None:
        # In case I need it
        pass

    @classmethod
    def tearDownClass(cls) -> None:
        directories_to_remove = [
            os.path.join(cls.test_resources_directory, 'some_other_directory')
        ]
        for directory in directories_to_remove:
            if os.path.isdir(directory):
                os.rmdir(directory)

    def setUp(self) -> None:
        # A good place to define datasets
        self.train_test_dataset = pd.read_csv(
            os.path.join(
                self.test_resources_directory, 'process_vep_test_traintest.tsv.gz'
            ), sep='\t', na_values='.'
        )
        self.validation_dataset = pd.read_csv(
            os.path.join(
                self.test_resources_directory, 'process_vep_test_validation.tsv.gz'
            ), sep='\t', na_values='.'
        )
        self.merged_test_dataset = pd.read_csv(
            os.path.join(
                self.test_resources_directory, 'process_vep_test_merged.tsv.gz'
            ), sep='\t', na_values='.'
        )

    def tearDown(self) -> None:
        # In case I need it
        pass

    def test_validator_input_cli_dataset_pass(self):
        validator = Validator()
        validator.validate_cla_dataset(
            os.path.join(self.test_resources_directory, 'scores_labels.tsv.gz')
        )

    def test_validator_input_cli_dataset_fail_not_exist(self):
        validator = Validator()
        expected_file_path = os.path.join(
            self.test_resources_directory, 'some_nonexisting_file.tsv.gz'
        )
        with self.assertRaises(FileNotFoundError) as e:
            validator.validate_cla_dataset(
                expected_file_path
            )

        self.assertEqual(str(e.exception), f'{expected_file_path} does not exist!')

    def test_validator_input_cli_dataset_fail_wrong_extension(self):
        validator = Validator()
        with self.assertRaises(IOError) as e:
            validator.validate_cla_dataset(self.incorrect_extension_filepath)
        self.assertEqual(str(e.exception), f'{self.incorrect_extension_filepath} does not match '
                                           f'the required extension: .tsv.gz, .tsv')

    def test_validator_output_cli_pass(self):
        # Side note: can't test the fail of this test
        validator = Validator()
        expected_output_directory = 'some_other_directory'
        validator.validate_output_cla(
            os.path.join(self.test_resources_directory, expected_output_directory)
        )
        self.assertIn(expected_output_directory, os.listdir(self.test_resources_directory))

    def test_validator_input_cli_cgd_pass(self):
        validator = Validator()
        validator.validate_cgd_path(os.path.join(self.test_resources_directory, 'fake_CGD.txt.gz'))

    def test_validator_input_cli_cgd_fail_extension(self):
        # Not testing FileNotExistError, since the input_cli_dataset already has one of those.
        validator = Validator()
        with self.assertRaises(IOError) as e:
            validator.validate_cgd_path(self.incorrect_extension_filepath)
        self.assertEqual(str(e.exception), f'{self.incorrect_extension_filepath} does not match '
                                           f'the required extension: .txt.gz, .tsv.gz')

    def test_validator_input_cli_json_pass(self):
        validator = Validator()
        validator.validate_cla_json(
            os.path.join(self.test_resources_directory, 'train_features.json')
        )

    def test_validator_input_cli_json_fail_extension(self):
        # Not testing FileNotExistError, since the input_cli_dataset already has one of those.
        validator = Validator()
        with self.assertRaises(IOError) as e:
            validator.validate_cla_json(self.incorrect_extension_filepath)
        self.assertEqual(str(e.exception), f'{self.incorrect_extension_filepath} does not match '
                                           f'the required extension: .json')

    def test_read_json(self):
        features = read_json(os.path.join(self.test_resources_directory, 'train_features.json'))
        self.assertSetEqual(
            set(features),
            {
                'PolyPhen', 'SIFT', 'cDNA_position', 'CDS_position', 'Protein_position',
                'Amino_acids', 'REF', 'ALT', 'Consequence', 'SpliceAI_pred_DP_AG',
                'SpliceAI_pred_DP_AL', 'SpliceAI_pred_DP_DG', 'SpliceAI_pred_DP_DL',
                'SpliceAI_pred_DS_AG', 'SpliceAI_pred_DS_AL', 'SpliceAI_pred_DS_DG',
                'SpliceAI_pred_DS_DL', 'Grantham', 'phyloP'}
        )

    def test_read_dataset_pass(self):
        features = read_json(os.path.join(self.test_resources_directory, 'train_features.json'))
        observed = read_dataset(
            os.path.join(
                self.test_resources_directory, 'process_vep_test_traintest.tsv.gz'
            ),
            features,
            'train_test'
        )
        pd.testing.assert_frame_equal(observed, self.train_test_dataset)

    def test_read_dataset_fail(self):
        features = read_json(os.path.join(self.test_resources_directory, 'train_features.json'))
        features.extend(['some_bogus_feature', 'another_bogus_feature'])
        with self.assertRaises(KeyError) as e:
            read_dataset(
                os.path.join(self.test_resources_directory, 'process_vep_test_traintest.tsv.gz'),
                features,
                'train_test'
            )
        self.assertEqual(str(e.exception), "'Missing required column in supplied dataset: "
                                           "some_bogus_feature, another_bogus_feature'")

    def test_merge_data(self):
        observed = merge_data(self.train_test_dataset, self.validation_dataset)
        pd.testing.assert_frame_equal(observed, self.merged_test_dataset)

    def test_drop_duplicates(self):
        test_case = pd.DataFrame(
            [
                ['variant_1', 'value_1', 'value_2', 'value_3'],
                ['variant_2', 'value_4', 'value_5', 'value_6'],
                ['variant_3', 'value_1', 'value_2', 'value_9'], # Duplicate of 1
                ['variant_4', 'value_10', 'value_11', 'value_12'],
                ['variant_5', 'value_13', 'value_14', 'value_15'],
                ['variant_6', 'value_16', 'value_17', 'value_18']
            ], columns=['variant', 'feature_1', 'feature_2', 'feature_3']
        )
        drop_duplicates(test_case, ['feature_1', 'feature_2'])
        self.assertNotIn('variant_3', test_case['variant'].values)
        for variant in ['variant_1', 'variant_2', 'variant_4', 'variant_5', 'variant_6']:
            self.assertIn(variant, test_case['variant'].values)

    def test_drop_genes_empty(self):
        test_case = pd.DataFrame(
            [
                ['variant_1', 'gene_1', 'train_test'],
                ['variant_2', None, 'train_test'],
                ['variant_3', 'gene_2', 'train_test']
            ], columns=['variant', 'SYMBOL', 'dataset_source']
        )
        drop_genes_empty(test_case)
        self.assertNotIn('variant_2', test_case['variant'].values)

    @patch('sys.stdout', new_callable=StringIO)
    def test_progress_printer(self, stdout):
        printer = ProgressPrinter()
        test_case = pd.DataFrame(
            {
                'variant': ['var1', 'var2', 'var3'],
                'dataset_source': ['train_test', 'train_test', 'validation']
            }
        )
        printer.set_initial_size(test_case)
        test_case.drop(index=1, inplace=True)
        printer.new_shape(test_case)
        printer.print_final_shape()
        self.assertIn('Dropped 1 variants from train_test', stdout.getvalue())
        self.assertIn('Dropped 0 variants from validation', stdout.getvalue())
        self.assertIn('Final number of samples in train_test: 1', stdout.getvalue())
        self.assertIn('Final number of samples in validation: 1', stdout.getvalue())

    def test_process_grch38(self):
        test_case = pd.DataFrame(
            {
                'CHROM': ['chr1', 'chr2', 'chr3_foobar', 'chrX', 'chrY_fake'],
                'variant': ['var1', 'var2', 'var3', 'var4', 'var5']
            }
        )
        process_grch38(test_case)
        self.assertNotIn('var3', test_case['variant'].values)
        self.assertNotIn('var5', test_case['variant'].values)
        expected = ['var1', 'var2', 'var4']
        for e in expected:
            self.assertIn(e, test_case['variant'].values)


    def test_drop_duplicate_entries(self):
        # Possible since VEP can output the same variant twice, or more
        test_case = pd.DataFrame(
            {
                'variant': ['variant_1', 'variant_2', 'variant_2', 'variant_3', 'variant_3'],
                'transcript': ['t1', 't2', 't1', 't1', 't1'],
                'feature_1': [1, 2, 3, 5, 5]
            }
        )
        expected = pd.DataFrame(
            {
                'variant': ['variant_1', 'variant_2', 'variant_2', 'variant_3'],
                'transcript': ['t1', 't2', 't1', 't1'],
                'feature_1': [1, 2, 3, 5]
            }
        )
        drop_duplicate_entries(test_case)
        pd.testing.assert_frame_equal(test_case, expected)


    def test_mismatching_genes(self):
        test_case = pd.DataFrame(
            {
                'ID': ['1!1!A!G!foo', '1!1!A!G!bar', '1!1!A!G!baz'],
                'SYMBOL': ['foo', 'bar', 'foobaz'],
                'variant': ['var1', 'var2', 'var3']
            }
        )
        drop_mismatching_genes(test_case)
        self.assertNotIn('var3', test_case['variant'].values)

    def test_load_and_correct_cgd(self):
        expected = {'foo', 'bar'}
        # Fake CGD contains: foo, bar, baz and TENM1 (of which baz is XL)
        observed = load_and_correct_cgd(
            os.path.join(self.test_resources_directory, 'fake_CGD.txt.gz'), ['foo', 'bar']
        )
        self.assertSetEqual(set(observed), expected)

    def test_drop_heterozygous_variants_in_ar_genes(self):
        test_case = pd.DataFrame(
            {
                'variant': ['var1', 'var2', 'var3'],
                'SYMBOL': ['foo', 'bar', 'baz'],
                'gnomAD_HN': [None, 0, 0]
            }
        )
        drop_heterozygous_variants_in_ar_genes(
            test_case,
            os.path.join(
                self.test_resources_directory,
                'fake_CGD.txt.gz'
            )
        )
        self.assertNotIn('var2', test_case['variant'].values)
        for variant in ['var1', 'var3']:
            self.assertIn(variant, test_case['variant'].values)

    def test_extract_label_and_weight(self):
        test_case = pd.DataFrame(
            {
                'ID': ['1!1!A!G!foo!0!0.8', '1!1!A!G!foo!1!0.5']
            }
        )
        extract_label_and_weight(test_case)
        self.assertIn('binarized_label', test_case.columns)
        self.assertIn('sample_weight', test_case.columns)
        self.assertIn(0, test_case['binarized_label'].values)
        self.assertIn(0.5, test_case['sample_weight'].values)

    def test_drop_variants_incorrect_label_or_weight(self):
        test_case = pd.DataFrame(
            {
                'ID': [None, 'foo', 'bar', 'baz'],
                'binarized_label': [None, 0.1, 0, 1],
                'sample_weight': [0.8, 0.9, 1.0, 0.7],
                'variant': ['var1', 'var2', 'var3', 'var4']
            }
        )
        drop_variants_incorrect_label_or_weight(test_case)
        self.assertNotIn('ID', test_case.columns)
        self.assertIn('var3', test_case['variant'].values)
        for notin in ['var1', 'var2', 'var4']:
            self.assertNotIn(notin, test_case['variant'].values)


if __name__ == '__main__':
    unittest.main()
