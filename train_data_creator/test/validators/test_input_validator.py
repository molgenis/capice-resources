import os
import unittest
from stat import S_IREAD

from train_data_creator.test import get_project_root_dir
from train_data_creator.src.main.validators.input_validator import InputValidator


class TestInputValidator(unittest.TestCase):
    __DIRECTORY__ = 'some_very_special_directory'
    __READONLY_DIRECTORY__ = 'a_readonly_directory'

    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = InputValidator()

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.__DIRECTORY__ in os.listdir(get_project_root_dir()):
            os.removedirs(os.path.join(get_project_root_dir(), cls.__DIRECTORY__))
        if cls.__READONLY_DIRECTORY__ in os.listdir(get_project_root_dir()):
            os.removedirs(os.path.join(get_project_root_dir(), cls.__READONLY_DIRECTORY__))

    def test_vkgl_corr(self):
        input_path = os.path.join(get_project_root_dir(), 'test', 'resources', 'smol_vkgl.tsv.gz')
        self.validator.validate_vkgl(input_path)

    def test_clinvar_corr(self):
        input_path = os.path.join(get_project_root_dir(), 'test', 'resources', 'smol_clinvar.vcf.gz')
        self.validator.validate_clinvar(input_path)

    def test_vkgl_incorr(self):
        input_path = os.path.join(get_project_root_dir(), 'test', 'resources', 'smol_clinvar.vcf.gz')
        self.assertRaises(
            IOError,
            self.validator.validate_vkgl,
            input_path
        )

    def test_clinvar_incorr(self):
        input_path = os.path.join(get_project_root_dir(), 'test', 'resources', 'smol_vkgl.tsv.gz')
        self.assertRaises(
            IOError,
            self.validator.validate_clinvar,
            input_path
        )

    def test__validate_file_exist(self):
        input_path = os.path.join(get_project_root_dir(), 'test', 'resources', 'not_a_file.tsv.gz')
        self.assertRaises(
            FileNotFoundError,
            self.validator._validate_file_exist,
            input_path,
            'VKGL'
        )

    def test_output_not_directory(self):
        output = os.path.join(get_project_root_dir(), 'not_a_directory', 'not_a_directory')
        self.assertRaises(
            OSError,
            self.validator.validate_output,
            output
        )

    def test_output_not_writable(self):
        output = os.path.join(get_project_root_dir(), self.__READONLY_DIRECTORY__)
        os.mkdir(os.path.join(output))
        os.chmod(output, S_IREAD)
        # Testing if an existing not writable directory raises OSError
        self.assertRaises(
            OSError,
            self.validator.validate_output,
            output
        )
        # Testing if making a new directory in a not writable directory raises OSError
        self.assertRaises(
            OSError,
            self.validator.validate_output,
            os.path.join(output, 'not_a_directory')
        )

    def test_output_back_to_parent(self):
        output = os.path.join(get_project_root_dir(), self.__DIRECTORY__)
        self.validator.validate_output(output)
        directories = os.listdir(get_project_root_dir())
        full_directories = []
        for directory in directories:
            full_directories.append(str(os.path.join(get_project_root_dir(), directory)))
        self.assertIn(output, full_directories)


if __name__ == '__main__':
    unittest.main()
