import os
import unittest
from pathlib import Path

from molgenis.capice_resources.core import GlobalEnums
from tests.capice_resources.test_utilities import get_testing_resources_dir, \
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
        correct_path = os.path.join(get_testing_resources_dir(), 'existing_tsv_file.tsv.gz')
        observed = self.validator.validate_icli_file(
            {'input': correct_path},
            extension=GlobalEnums.TSV_EXTENSIONS.value
        )
        expected = {'input': Path(correct_path)}
        self.assertDictEqual(observed, expected)

    def test_icli_file_not_exist_fail(self):
        incorrect_path = os.path.join(
            get_testing_resources_dir(), 'nonexisting_tsv_file.tsv.gz'
        )
        with self.assertRaises(FileNotFoundError) as e:
            self.validator.validate_icli_file(
                {'input': incorrect_path},
                extension=GlobalEnums.TSV_EXTENSIONS.value
            )
        self.assertEqual(f'Input path: {incorrect_path} does not exist!', str(e.exception))

    def test_icli_file_none_fail(self):
        with self.assertRaises(IOError) as e:
            self.validator.validate_icli_file(
                {'input': None},
                extension=GlobalEnums.TSV_EXTENSIONS.value
            )
        self.assertEqual('Encountered None argument in non-optional flag.', str(e.exception))

    def test_icli_file_extension_fail(self):
        path = os.path.join(
            get_testing_resources_dir(), 'existing_txt_file.txt.gz'
        )
        with self.assertRaises(IOError) as e:
            self.validator.validate_icli_file(
                {'input': path},
                extension=GlobalEnums.TSV_EXTENSIONS.value
            )
        self.assertEqual(
            f'Input {path} does not match the correct extension: '
            f'{", ".join(GlobalEnums.TSV_EXTENSIONS.value)}',
            str(e.exception)
        )

    def test_icli_file_none_pass(self):
        expected = {'input': None}
        observed = self.validator.validate_icli_file(
            expected,
            extension=GlobalEnums.TSV_EXTENSIONS.value,
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
        filename = 'some_file.tsv.gz'
        path = os.path.join(get_testing_resources_dir(), filename)
        observed = self.validator.validate_ocli_directory(
            {'output': path},
            extension=GlobalEnums.TSV_EXTENSIONS.value
        )
        self.assertNotIn(filename, os.listdir(get_testing_resources_dir()))
        self.assertDictEqual(observed, {'output': get_testing_resources_dir()})

    def test_ocli_none_fail(self):
        with self.assertRaises(IOError) as e:
            self.validator.validate_ocli_directory(
                {'output': None}
            )
        self.assertEqual('Encountered None argument in non-optional flag.', str(e.exception))

    def test_ocli_file_extension_fail(self):
        path = os.path.join(get_testing_resources_dir(), 'some_file.csv.gz')
        with self.assertRaises(IOError) as e:
            self.validator.validate_ocli_directory(
                {'output': path},
                extension=GlobalEnums.TSV_EXTENSIONS.value
            )
        self.assertEqual(
            f'Output {path} does not end with required extension: .tsv.gz, .tsv',
            str(e.exception)
        )

    def test_ocli_file_existing_fail(self):
        path = os.path.join(get_testing_resources_dir(), 'existing_tsv_file.tsv.gz')
        with self.assertRaises(FileExistsError) as e:
            self.validator.validate_ocli_directory(
                {'output': path},
                extension=GlobalEnums.TSV_EXTENSIONS.value
            )
        self.assertEqual(
            f'Output {path} already exists and force is not enabled!', str(e.exception)
        )

    def test_ocli_file_existing_pass(self):
        path = os.path.join(get_testing_resources_dir(), 'existing_tsv_file.tsv.gz')
        observed = self.validator.validate_ocli_directory(
            {'output': path},
            extension=GlobalEnums.TSV_EXTENSIONS.value,
            force=True
        )
        self.assertDictEqual(observed, {'output': Path(path)})


if __name__ == '__main__':
    unittest.main()
