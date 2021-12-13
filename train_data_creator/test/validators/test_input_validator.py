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

    def test_output(self):
        output_path = project_root_dir
        self.validator.validate_output(output_path)

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
        output = os.path.join(project_root_dir, 'not_a_directory')
        self.assertRaises(
            OSError,
            self.validator.validate_output,
            output
        )


if __name__ == '__main__':
    unittest.main()
