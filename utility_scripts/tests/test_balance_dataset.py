import os
import shutil
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from utility_scripts.balance_dataset import Balancer, \
    CommandLineArgumentsValidator, InputDatasetValidator, __bins__, VerbosityPrinter

_project_root_directory = Path(__file__).absolute().parent.parent.parent


class TestBalancer(unittest.TestCase):
    __current_directory__ = _project_root_directory
    __test_path__ = os.path.join(__current_directory__, '.test_folder')
    depth_1_directory = Path(os.path.join(
        _project_root_directory,
        'some_directory'
    ))
    depth_2_directory = Path(os.path.join(
        _project_root_directory,
        'other_directory',
        'further_directory'
    ))

    @classmethod
    def setUpClass(cls) -> None:
        if not os.path.isdir(cls.__test_path__):
            os.makedirs(cls.__test_path__)
        cls.dataset = pd.read_csv(
            os.path.join(
                cls.__current_directory__,
                'utility_scripts',
                'tests',
                'resources',
                'train_input.tsv.gz'
            ),
            sep='\t',
            na_values='.',
            low_memory=False
        )
        cls.hardcoded_columns = ['variant', 'Consequence', 'gnomAD_AF', 'binarized_label']
        cls.test_sampler_data = pd.DataFrame(
            {
                'variant': ['variant_1', 'consequence_1', 0.02, 0],
                'Consequence': ['variant_2', 'consequence_1', 0.01, 1],
                'gnomAD_AF': ['variant_3', 'consequence_2', 0.02, 0],
                'binarized_label': ['variant_4', 'consequence_2', 0.01, 1]
            }
        )

    @classmethod
    def tearDownClass(cls) -> None:
        if os.path.isdir(cls.depth_1_directory):
            os.rmdir(cls.depth_1_directory)
        if os.path.isdir(cls.depth_2_directory):
            os.rmdir(cls.depth_2_directory)
            os.rmdir(cls.depth_2_directory.parent)
        if os.path.isdir(cls.__test_path__):
            for filename in os.listdir(cls.__test_path__):
                filepath = os.path.join(cls.__test_path__, filename)
                try:
                    if os.path.isfile(filepath) or os.path.islink(filepath):
                        os.unlink(filepath)
                    elif os.path.isdir(filepath):
                        shutil.rmtree(filepath)
                except Exception as e:
                    print(f'Failed to delete {filepath}, reason: {e}')
            try:
                os.rmdir(cls.__test_path__)
            except Exception as e:
                print(f'Failed to remove tests folder {cls.__test_path__}, reason: {e}')

    def setUp(self) -> None:
        print('Testing Class:')

    def tearDown(self) -> None:
        print('Done.')

    def test_obtain_consequences(self):
        balancer = Balancer(VerbosityPrinter())
        consequence_series = pd.Series(
            name='Consequence',
            data=[
                'consequence_1',
                'consequence_2',
                'consequence_3&consequence_4',
                'consequence_3'
            ]
        )
        self.assertTrue(
            np.array_equal(
                np.array(
                    [
                        'consequence_1',
                        'consequence_2',
                        'consequence_3',
                        'consequence_4'
                    ]
                ),
                balancer._obtain_consequences(consequence_series)
            )
        )

    def test_sampler_unchanged_more_required(self):
        balancer = Balancer(VerbosityPrinter())
        test_set = self.test_sampler_data.copy(deep=True)
        self.assertEqual(balancer._sample_variants(test_set, 5).shape[0], 4)

    def test_sampler_unchanged_equal_required(self):
        balancer = Balancer(VerbosityPrinter())
        test_set = self.test_sampler_data.copy(deep=True)
        self.assertEqual(balancer._sample_variants(test_set, 4).shape[0], 4)

    def test_sampler_changed_less_required(self):
        balancer = Balancer(VerbosityPrinter())
        test_set = self.test_sampler_data.copy(deep=True)
        self.assertEqual(balancer._sample_variants(test_set, 2).shape[0], 2)

    def test_sampler_changed_zero_required(self):
        balancer = Balancer(VerbosityPrinter())
        test_set = self.test_sampler_data.copy(deep=True)
        self.assertEqual(balancer._sample_variants(test_set, 0).shape[0], 0)

    def test_set_columns(self):
        balancer = Balancer(VerbosityPrinter())
        columns = ['foo', 'bar', 'baz']
        test_dataset = pd.DataFrame(columns=columns)
        balancer._set_columns(test_dataset.columns)
        columns.append('balanced_on')
        pd.testing.assert_index_equal(balancer.columns, pd.Index(columns))

    def set_up_test_balancer(self):
        balancer = Balancer(VerbosityPrinter())
        dataset = self.dataset.copy(deep=True)
        balanced_dataset, _ = balancer.balance(dataset)
        self.assertGreater(balanced_dataset.shape[0], 0)
        self.assertEqual(
            balanced_dataset[balanced_dataset['binarized_label'] == 0].shape[0],
            balanced_dataset[balanced_dataset['binarized_label'] == 1].shape[0]
        )
        self.assertIn('balanced_on', balanced_dataset.columns)
        return balanced_dataset

    def test_balancer_consequences(self):
        """
        Function to test the balancer consequences with a real life dataset
        """
        balanced_dataset = self.set_up_test_balancer()
        incorrect_consequences = []
        conseqs = Balancer(VerbosityPrinter())._obtain_consequences(balanced_dataset['Consequence'])
        for consequence in conseqs:
            subset = balanced_dataset[balanced_dataset['balanced_on'] == consequence]
            n_benign = subset[subset['binarized_label'] == 0].shape[0]
            n_pathogenic = subset[subset['binarized_label'] == 1].shape[0]
            if n_benign != n_pathogenic:
                incorrect_consequences.append(
                    f'{consequence} (n_b: {n_benign}, n_p: {n_pathogenic})'
                )
        self.assertListEqual([], incorrect_consequences)

    def test_balancer_afbins(self):
        """
        Function to test the balancer allele frequency bins with a real life dataset
        :return:
        """
        balanced_dataset = self.set_up_test_balancer()
        # Required, because 0 impute is reset during balancing
        balanced_dataset['gnomAD_AF'].fillna(0, inplace=True)
        incorrect_afbins = []
        for ind in range(len(__bins__) - 1):
            lower_bound = __bins__[ind]
            upper_bound = __bins__[ind + 1]
            subset = balanced_dataset[
                (balanced_dataset['gnomAD_AF'] >= lower_bound) &
                (balanced_dataset['gnomAD_AF'] < upper_bound)
                ]
            n_benign = subset[subset['binarized_label'] == 0].shape[0]
            n_pathogenic = subset[subset['binarized_label'] == 1].shape[0]
            if n_benign != n_pathogenic:
                incorrect_afbins.append(
                    f'{lower_bound}-{upper_bound} (n_b: {n_benign}, n_p: {n_pathogenic})'
                )
        self.assertListEqual([], incorrect_afbins)

    def test_balanced_remainder(self):
        balancer = Balancer(VerbosityPrinter())
        dataset = self.dataset.copy(deep=True)
        balanced, remainder = balancer.balance(dataset)
        # Subset because of the "balanced_on" column
        self.assertFalse(
            pd.concat(
                [balanced, remainder],
                axis=0
            ).duplicated(subset=remainder.columns).any())

    def test_process_consequence_equal(self):
        """
        Test for the _process_consequence method with 2 consequences that have an equal amount of
        benign and pathogenic variants
        """
        test_data = [
            ['variant_1', 'consequence_1', 0.01, 0],
            ['variant_2', 'consequence_1', 0.02, 0],
            ['variant_3', 'consequence_1', 0.03, 0],
            ['variant_4', 'consequence_1', 0.03, 1],
            ['variant_5', 'consequence_1', 0.02, 1],
            ['variant_6', 'consequence_1', 0.01, 1],
            ['variant_7', 'consequence_2', 0.01, 0],
            ['variant_8', 'consequence_2', 0.02, 0],
            ['variant_9', 'consequence_2', 0.03, 0],
            ['variant_10', 'consequence_2', 0.03, 1],
            ['variant_11', 'consequence_2', 0.02, 1],
            ['variant_12', 'consequence_2', 0.01, 1]
        ]
        test_set = pd.DataFrame(
            test_data, columns=self.hardcoded_columns
        )
        expected_rows = {'consequence_1': 6, 'consequence_2': 6}
        self._test_consequence(test_set, expected_rows)

    def test_process_consequence_patho_bias(self):
        """
        Test for the _process_consequence method with 2 consequences, of which one has a pathogenic
        variant bias
        """
        test_data = [
            ['variant_1', 'consequence_1', 0.01, 0],
            ['variant_2', 'consequence_1', 0.02, 1],
            ['variant_3', 'consequence_1', 0.03, 1],
            ['variant_4', 'consequence_1', 0.03, 1],
            ['variant_5', 'consequence_1', 0.02, 1],
            ['variant_6', 'consequence_1', 0.01, 1],
            ['variant_7', 'consequence_2', 0.01, 0],
            ['variant_8', 'consequence_2', 0.02, 0],
            ['variant_9', 'consequence_2', 0.03, 0],
            ['variant_10', 'consequence_2', 0.03, 1],
            ['variant_11', 'consequence_2', 0.02, 1],
            ['variant_12', 'consequence_2', 0.01, 1]
        ]
        test_set = pd.DataFrame(
            test_data, columns=self.hardcoded_columns
        )
        expected_rows = {'consequence_1': 2, 'consequence_2': 6}
        self._test_consequence(test_set, expected_rows)

    def test_process_consequence_double_patho_bias(self):
        """
        Test for the _process_consequence method with 2 consequences, both having more pathogenic
        variants than benign
        """
        test_data = [
            ['variant_1', 'consequence_1', 0.01, 0],
            ['variant_2', 'consequence_1', 0.02, 1],
            ['variant_3', 'consequence_1', 0.03, 1],
            ['variant_4', 'consequence_1', 0.03, 1],
            ['variant_5', 'consequence_1', 0.02, 1],
            ['variant_6', 'consequence_1', 0.01, 1],
            ['variant_7', 'consequence_2', 0.01, 0],
            ['variant_8', 'consequence_2', 0.02, 1],
            ['variant_9', 'consequence_2', 0.03, 1],
            ['variant_10', 'consequence_2', 0.03, 1],
            ['variant_11', 'consequence_2', 0.02, 1],
            ['variant_12', 'consequence_2', 0.01, 1]
        ]
        test_set = pd.DataFrame(
            test_data, columns=self.hardcoded_columns
        )
        expected_rows = {'consequence_1': 2, 'consequence_2': 2}
        self._test_consequence(test_set, expected_rows)

    def test_process_consequence_benign_bias(self):
        """
        Test for the _process_consequence method with 2 consequences, of which one has more benign
        variants than pathogenic
        """
        test_data = [
            ['variant_1', 'consequence_1', 0.01, 0],
            ['variant_2', 'consequence_1', 0.02, 0],
            ['variant_3', 'consequence_1', 0.03, 0],
            ['variant_4', 'consequence_1', 0.03, 0],
            ['variant_5', 'consequence_1', 0.02, 0],
            ['variant_6', 'consequence_1', 0.01, 1],
            ['variant_7', 'consequence_2', 0.01, 0],
            ['variant_8', 'consequence_2', 0.02, 0],
            ['variant_9', 'consequence_2', 0.03, 0],
            ['variant_10', 'consequence_2', 0.03, 1],
            ['variant_11', 'consequence_2', 0.02, 1],
            ['variant_12', 'consequence_2', 0.01, 1]
        ]
        test_set = pd.DataFrame(
            test_data, columns=self.hardcoded_columns
        )
        expected_rows = {'consequence_1': 2, 'consequence_2': 6}
        self._test_consequence(test_set, expected_rows)

    def test_process_consequence_double_benign_bias(self):
        """
        Test for the _process_consequence method with 2 consequences, both having more benign
        variants than pathogenic
        """
        test_data = [
            ['variant_1', 'consequence_1', 0.01, 0],
            ['variant_2', 'consequence_1', 0.02, 0],
            ['variant_3', 'consequence_1', 0.03, 0],
            ['variant_4', 'consequence_1', 0.03, 0],
            ['variant_5', 'consequence_1', 0.02, 0],
            ['variant_6', 'consequence_1', 0.01, 1],
            ['variant_7', 'consequence_2', 0.01, 0],
            ['variant_8', 'consequence_2', 0.02, 0],
            ['variant_9', 'consequence_2', 0.03, 0],
            ['variant_10', 'consequence_2', 0.03, 0],
            ['variant_11', 'consequence_2', 0.02, 0],
            ['variant_12', 'consequence_2', 0.01, 1]
        ]
        test_set = pd.DataFrame(
            test_data, columns=self.hardcoded_columns
        )
        expected_rows = {'consequence_1': 2, 'consequence_2': 2}
        self._test_consequence(test_set, expected_rows)

    def test_process_consequence_double_bias(self):
        """
        Test for the _process_consequence method with 2 consequences, one having a pathogenic bias
        and the other a benign bias
        """
        test_data = [
            ['variant_1', 'consequence_1', 0.01, 0],
            ['variant_2', 'consequence_1', 0.02, 0],
            ['variant_3', 'consequence_1', 0.03, 0],
            ['variant_4', 'consequence_1', 0.03, 0],
            ['variant_5', 'consequence_1', 0.02, 0],
            ['variant_6', 'consequence_1', 0.01, 1],
            ['variant_7', 'consequence_2', 0.01, 0],
            ['variant_8', 'consequence_2', 0.02, 1],
            ['variant_9', 'consequence_2', 0.03, 1],
            ['variant_10', 'consequence_2', 0.03, 1],
            ['variant_11', 'consequence_2', 0.02, 1],
            ['variant_12', 'consequence_2', 0.01, 1]
        ]
        test_set = pd.DataFrame(
            test_data, columns=self.hardcoded_columns
        )
        expected_rows = {'consequence_1': 2, 'consequence_2': 2}
        self._test_consequence(test_set, expected_rows)

    def test_process_consequence_multiconsequence(self):
        test_data = [
            ['variant_1', 'consequence_1&consequence_2&consequence_3', 0.01, 0],
            ['variant_2', 'consequence_2', 0.01, 0],
            ['variant_3', 'consequence_2', 0.01, 0],
            ['variant_4', 'consequence_1', 0.01, 1],
            ['variant_5', 'consequence_1', 0.01, 1],
            ['variant_6', 'consequence_1&consequence_2', 0.01, 1],
            ['variant_7', 'consequence_1&consequence_3', 0.01, 0],
            ['variant_8', 'consequence_1&consequence_2', 0.01, 1]
        ]
        test_set = pd.DataFrame(
            test_data, columns=self.hardcoded_columns
        )
        expected_rows = {'consequence_1': 4, 'consequence_2': 4, 'consequence_3': 0}
        self._test_consequence(test_set, expected_rows)

    def _test_consequence(self, test_set: pd.DataFrame, expected_rows: dict):
        balancer = Balancer(VerbosityPrinter())
        balancer._set_bins(test_set['gnomAD_AF'])
        consequences = balancer._obtain_consequences(test_set['Consequence'])
        for consequence in consequences:
            observed = balancer._process_consequence(
                test_set[
                    (test_set['Consequence'].str.contains(consequence, regex=False)) &
                    (test_set['binarized_label'] == 1)
                    ],
                test_set[
                    (test_set['Consequence'].str.contains(consequence, regex=False)) &
                    (test_set['binarized_label'] == 0)
                    ]
            )
            self.assertEqual(
                observed.shape[0],
                expected_rows[consequence],
                msg=f'Test failed on consequence: {consequence}'
            )

    def test_balancer_known_input(self):
        """
        Tests the balancer function with a hardcoded dataframe
        """
        variant_data = [
            ['variant_1', 'consequence_1', 0.8, 0],  # Paired with variant_2
            ['variant_2', 'consequence_1', 0.75, 1],  # Paired with variant_1
            ['variant_3', 'consequence_2', 0.2, 1],  # Paired with variant_5
            ['variant_4', 'consequence_2', 0.01, 0],  # Paired with variant_6
            ['variant_5', 'consequence_2', 0.45, 0],  # Paired with variant_3
            ['variant_6', 'consequence_1&consequence_2', 0.02, 1],  # Paired with variant_4
            ['variant_7', 'consequence_2&consequence_3', 0.001, 1],  # Removed
            ['variant_8', 'consequence_3', 0.9, 0]  # Removed
        ]
        test_case = pd.DataFrame(
            variant_data, columns=['variant', 'Consequence', 'gnomAD_AF', 'binarized_label']
        )
        balanced, _ = Balancer(VerbosityPrinter()).balance(test_case)
        expected_variants = [
            'variant_1',
            'variant_2',
            'variant_3',
            'variant_4',
            'variant_5',
            'variant_6'
        ]
        for variant in balanced['variant'].values:
            self.assertIn(variant, expected_variants)
        self.assertFalse(balanced['variant'].duplicated().any())

    def test_duplicate_processing_balancer(self):
        """
        Test to see if a sample with multiple consequences gets sampled only once
        """
        test_dataset = pd.DataFrame(
            {
                'Consequence': [
                    'consequence_1&consequence_2',
                    'consequence_1',
                    'consequence_2',
                    'consequence_2'
                ],
                'binarized_label': [0, 1, 0, 1],
                'gnomAD_AF': [0.0, 0.0, 0.0, 0.0]
            }
        )
        observed, _ = Balancer(VerbosityPrinter()).balance(test_dataset)
        self.assertFalse(observed.duplicated().any())

    def test_cla_validator(self):
        """
        Function to test the Command Line Arguments validator
        """
        print('CLA Validator')
        validator = CommandLineArgumentsValidator()
        self.assertRaises(
            FileNotFoundError,
            validator.validate_input_path,
            self.__current_directory__
        )
        self.assertRaises(
            OSError,
            validator.validate_input_path,
            str(Path(__file__))
        )

        self.assertWarns(
            UserWarning,
            validator.validate_output_path,
            self.depth_1_directory
        )
        self.assertIn('some_directory', os.listdir(_project_root_directory))

        self.assertWarns(
            UserWarning,
            validator.validate_output_path,
            self.depth_2_directory
        )
        self.assertIn('other_directory', os.listdir(_project_root_directory))
        self.assertIn('further_directory',
                      os.listdir(os.path.join(_project_root_directory, 'other_directory')))

    def test_dataset_validator(self):
        """
        Function to test if the dataset validator does what it is supposed to.
        """
        print('Dataset validator')
        validator = InputDatasetValidator()
        dataset = self.dataset.copy(deep=True)
        self.assertRaises(KeyError,
                          validator.validate_columns_required,
                          dataset.drop(columns=['gnomAD_AF']))
        self.assertRaises(ValueError,
                          validator.validate_b_p_present,
                          dataset[dataset['binarized_label'] == 0])
        self.assertRaises(ValueError,
                          validator.validate_b_p_present,
                          dataset[dataset['binarized_label'] == 1])


if __name__ == '__main__':
    unittest.main()
