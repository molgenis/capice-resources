import os
import unittest
from pathlib import Path

import pandas as pd

from tests.capice_resources.testing_utilities import get_testing_resources_dir, \
    temp_output_file_path_and_name, check_and_remove_directory
from molgenis.capice_resources.core.validator import InputValidator, DataValidator


class TestInputValidator(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        check_and_remove_directory(temp_output_file_path_and_name())

    @classmethod
    def tearDownClass(cls) -> None:
        check_and_remove_directory(temp_output_file_path_and_name())
        check_and_remove_directory(os.path.join(get_testing_resources_dir(), 'a_new_directory'))

    def setUp(self) -> None:
        self.validator = InputValidator()

    def test_icli_file_pass(self):
        """
        Test to see if the validator performs as expected when an existing file is supplied with
        the correct extension.
        """
        correct_path = os.path.join(get_testing_resources_dir(), 'existing_tsv_file.tsv.gz')
        observed = self.validator.validate_icli_file(
            {'input': correct_path},
            extension=('.tsv.gz', '.tsv')
        )
        expected = {'input': Path(correct_path)}
        self.assertDictEqual(observed, expected)

    def test_icli_file_json_pass(self):
        """
        Same as "test_icli_file_pass" but with a JSON instead of a TSV(.gz).
        """
        correct_path = os.path.join(get_testing_resources_dir(), 'features.json')
        observed = self.validator.validate_icli_file(
            {'json': correct_path},
            extension='json'
        )
        expected = {'json': Path(correct_path)}
        self.assertDictEqual(observed, expected)

    def test_icli_file_not_exist_fail(self):
        """
        Test to check if FileNotFoundError is raised when a non-existing file is supplied,
        but the extension is correct.
        """
        incorrect_path = os.path.join(
            get_testing_resources_dir(), 'nonexisting_tsv_file.tsv.gz'
        )
        with self.assertRaises(FileNotFoundError) as e:
            self.validator.validate_icli_file(
                {'input': incorrect_path},
                extension='\t'
            )
        self.assertEqual(f'Input path: {incorrect_path} does not exist!', str(e.exception))

    def test_icli_file_none_fail(self):
        """
        Test to check if IOError is raised when None (could be supplied in case of an
        optional flag) is supplied, but can_be_optional is set to its default False.
        """
        with self.assertRaises(IOError) as e:
            self.validator.validate_icli_file(
                {'input': None},
                extension='\t'
            )
        self.assertEqual('Encountered None argument in non-optional flag.', str(e.exception))

    def test_icli_file_extension_fail(self):
        """
        Test to see if IOError is raised properly when an existing file is supplied,
        but the extension is incorrect.
        """
        path = os.path.join(
            get_testing_resources_dir(), 'existing_txt_file.txt.gz'
        )
        with self.assertRaises(IOError) as e:
            self.validator.validate_icli_file(
                {'input': path},
                extension=('.tsv.gz', '.tsv')
            )
        self.assertEqual(
            f'Input {path} does not match the correct extension: .tsv.gz, .tsv',
            str(e.exception)
        )

    def test_icli_file_none_pass(self):
        """
        Test to check if None passes when can_be_optional is set to True.
        """
        expected = {'input': None}
        observed = self.validator.validate_icli_file(
            expected,
            extension='\t',
            can_be_optional=True
        )
        self.assertDictEqual(observed, expected)

    def test_ocli_path_pass(self):
        directory = 'a_new_directory'
        path = os.path.join(get_testing_resources_dir(), directory)
        self.validator.validate_ocli_directory(
            {'output': path}
        )
        self.assertIn(directory, os.listdir(get_testing_resources_dir()))
        check_and_remove_directory(os.path.join(get_testing_resources_dir(), 'a_new_directory'))

    def test_ocli_file_pass(self):
        """
        Test to see if the validate_ocli_directory properly functions when supplied with a full
        path + filename.
        """
        filename = 'some_file.tsv.gz'
        path = os.path.join(get_testing_resources_dir(), filename)
        observed = self.validator.validate_ocli_directory(
            {'output': path},
            extension=('.tsv.gz', '.tsv')
        )
        self.assertNotIn(filename, os.listdir(get_testing_resources_dir()))
        self.assertDictEqual(observed, {'output': Path(path)})

    def test_ocli_none_fail(self):
        """
        Test to see if "validate_ocli_directory" properly raises IOError when supplied with None.
        "can_be_optional" is not a flag, since output must always be set in all modules.
        """
        with self.assertRaises(IOError) as e:
            self.validator.validate_ocli_directory(
                {'output': None}
            )
        self.assertEqual('Encountered None argument in non-optional flag.', str(e.exception))

    def test_ocli_file_extension_fail(self):
        """
        Test to check if IOError is raised when an output path + filename is supplied that does
        not have the correct extension as the module requires.
        """
        path = os.path.join(get_testing_resources_dir(), 'some_file.csv.gz')
        with self.assertRaises(IOError) as e:
            self.validator.validate_ocli_directory(
                {'output': path},
                extension=('.tsv.gz', '.tsv')
            )
        self.assertEqual(
            f'Output {path} does not end with required extension: .tsv.gz, .tsv',
            str(e.exception)
        )

    def test_ocli_file_existing_fail(self):
        """
        Test to check if FileExistsError is raised when a correct output path + filename is
        supplied but the file already exists.
        (Force is not an option by default, as it differs per module if it requires an output
        directory or an output file). To prevent additional (duplicated) code, force IS an
        argument that can be supplied to "validate_ocli_directory".
        """
        path = os.path.join(get_testing_resources_dir(), 'existing_tsv_file.tsv.gz')
        with self.assertRaises(FileExistsError) as e:
            self.validator.validate_ocli_directory(
                {'output': path},
                extension=('.tsv.gz', '.tsv')
            )
        self.assertEqual(
            f'Output {path} already exists and force is not enabled!', str(e.exception)
        )

    def test_ocli_file_existing_pass(self):
        """
        Test to check if an already existing path + filename is properly processed when the
        force flag is set to True.
        """
        path = os.path.join(get_testing_resources_dir(), 'existing_tsv_file.tsv.gz')
        observed = self.validator.validate_ocli_directory(
            {'output': path},
            extension=('.tsv.gz', '.tsv'),
            force=True
        )
        self.assertDictEqual(observed, {'output': Path(path)})

    def test_extract_key_value_dict_simple_pass(self):
        """
        Test for extract_key_value_dict_cli that the key and value are properly returned as tuple.
        """
        test_case = {'foo': 'bar/baz'}
        observed = self.validator._extract_key_value_dict_cli(test_case)
        self.assertTupleEqual(observed, ('foo', 'bar/baz'))

    def test_extract_key_value_dict_simple_none_pass(self):
        """
        Test for extract_key_value_dict_cli that the key and value are properly returned as
        tuple, even when the value is supplied as None.
        (by design, the value is converted to String, which would cause an issue when supplying
        None)
        """
        test_case = {'foo': None}
        observed = self.validator._extract_key_value_dict_cli(test_case)
        self.assertTupleEqual(observed, ('foo', None))

    def test_extract_key_value_incorrect_pass(self):
        """
        Test for extract_key_value_dict_cli that checks if something like a float is properly
        converted to string.
        """
        test_case = {'foo': 0.01}
        observed = self.validator._extract_key_value_dict_cli(test_case)  # type: ignore
        self.assertTupleEqual(observed, ('foo', '0.01'))


class TestDataValidator(unittest.TestCase):
    def setUp(self) -> None:
        self.dataframe = pd.DataFrame(
            {
                'foo': [1, 2, 3],
                'bar': ['a', 'b', 'c'],
                'baz': [0.01, 0.02, 0.3]
            }
        )
        self.validator = DataValidator()

    def test_validator_pass(self):
        """
        Test to check if the validate_pandas_dataframe properly functions when all columns are
        required.
        """
        self.validator.validate_pandas_dataframe(
            self.dataframe,
            required_columns=['foo', 'bar', 'baz']
        )

    def test_validator_pass_less_columns(self):
        """
        Test to check if validate_pandas_dataframe properly functions when fewer columns are
        supplied than there are present in the dataframe.
        """
        self.validator.validate_pandas_dataframe(
            self.dataframe,
            required_columns=['foo', 'bar']
        )

    def test_validator_fail_empty_frame(self):
        """
        Test to check if IndexError is properly raised when all the required columns are present,
        but the dataframe does not contain any samples.
        """
        with self.assertRaises(IndexError) as e:
            self.validator.validate_pandas_dataframe(
                pd.DataFrame(columns=self.dataframe.columns),
                required_columns=['foo', 'bar']
            )
        self.assertEqual('Given dataframe does not contain samples', str(e.exception))

    def test_validator_fail_missing_column(self):
        """
        Test to check if KeyError is properly raised when a single required column is missing.
        """
        with self.assertRaises(KeyError) as e:
            self.validator.validate_pandas_dataframe(
                self.dataframe.drop(columns=['foo']),
                required_columns=['foo', 'bar']
            )
        self.assertEqual("'Missing required columns: foo'", str(e.exception))

    def test_validator_fail_missing_columns(self):
        """
        Test to check if KeyError is properly raised when multiple required columns are missing.
        """
        with self.assertRaises(KeyError) as e:
            self.validator.validate_pandas_dataframe(
                self.dataframe.drop(columns=['foo', 'bar']),
                required_columns=['foo', 'bar', 'baz']
            )
        self.assertEqual("'Missing required columns: foo, bar'", str(e.exception))


if __name__ == '__main__':
    unittest.main()
