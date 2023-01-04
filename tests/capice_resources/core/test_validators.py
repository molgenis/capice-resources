import os
import unittest
from pathlib import Path

from molgenis.capice_resources.core import GlobalEnums
from tests.capice_resources.test_utilities import get_testing_resources_dir
from molgenis.capice_resources.core.validator import InputValidator, DataValidator


class TestInputValidator(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()
