import os
import unittest

from train_data_creator.src.main.utilities import project_root_dir
from train_data_creator.src.main.validators.input_validator import InputValidator


class TestInputValidator(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = InputValidator()

    def test_vkgl_corr(self):
        input_path = os.path.join(project_root_dir, 'test', 'resources', 'smol_vkgl.tsv.gz')
        self.validator.validate_vkgl(input_path)

    def test_clinvar_corr(self):
        input_path = os.path.join(project_root_dir, 'test', 'resources', 'smol_clinvar.vcf.gz')
        self.validator.validate_clinvar(input_path)

    def test_vkgl_incorr(self):
        input_path = os.path.join(project_root_dir, 'test', 'resources', 'smol_clinvar.vcf.gz')
        self.assertRaises(
            FileNotFoundError,
            self.validator.validate_vkgl,
            input_path
        )

    def test_clinvar_incorr(self):
        input_path = os.path.join(project_root_dir, 'test', 'resources', 'smol_vkgl.tsv.gz')
        self.assertRaises(
            FileNotFoundError,
            self.validator.validate_clinvar,
            input_path
        )

    def test__validate_file_exist(self):
        input_path = os.path.join(project_root_dir, 'test', 'resources', 'not_a_file.tsv.gz')
        self.assertRaises(
            FileNotFoundError,
            self.validator._validate_file_exist,
            input_path,
            'VKGL'
        )

    def test_output_not_directory(self):
        output = os.path.join('/', 'not_a_directory')
        self.assertRaises(
            OSError,
            self.validator.validate_output,
            output
        )

    def test_output_back_to_parent(self):
        output = os.path.join(project_root_dir, 'not_a_directory')
        print(output)
        self.validator.validate_output(output)
        directories = os.listdir(project_root_dir)
        full_directories = []
        for directory in directories:
            full_directories.append(str(os.path.join(project_root_dir, directory)))
        self.assertIn(output, full_directories)
        os.removedirs(output)


if __name__ == '__main__':
    unittest.main()
