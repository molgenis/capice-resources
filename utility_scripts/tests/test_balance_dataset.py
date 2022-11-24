import os
import shutil
import unittest
from pathlib import Path

import pandas as pd

from utility_scripts.balance_dataset import Balancer, \
    CommandLineArgumentsValidator, InputDatasetValidator, __bins__

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

    @classmethod
    def tearDownClass(cls) -> None:
        os.rmdir(cls.depth_1_directory)
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

    def test_balancer(self):
        """
        Function to test the balancer
        """
        print('Balancer')
        balancer = Balancer()
        dataset = self.dataset.copy(deep=True)
        balanced_dataset = balancer.balance(dataset)
        self.assertGreater(balanced_dataset.shape[0], 0)
        self.assertEqual(
            balanced_dataset[balanced_dataset['binarized_label'] == 0].shape[0],
            balanced_dataset[balanced_dataset['binarized_label'] == 1].shape[0]
        )
        for ind in range(len(__bins__) - 1):
            lower_bound = __bins__[ind]
            upper_bound = __bins__[ind + 1]
            self.assertEqual(
                balanced_dataset[(balanced_dataset['gnomAD_AF'] >= lower_bound) &
                                 (balanced_dataset['gnomAD_AF'] < upper_bound) &
                                 (balanced_dataset['binarized_label'] == 0)].shape[0],
                balanced_dataset[(balanced_dataset['gnomAD_AF'] >= lower_bound) &
                                 (balanced_dataset['gnomAD_AF'] < upper_bound) &
                                 (balanced_dataset['binarized_label'] == 1)].shape[0]
            )

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
        observed = Balancer().balance(test_dataset)
        print(observed)
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
