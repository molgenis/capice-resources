import os
import unittest
from pathlib import Path

import pandas as pd

from utility_scripts.threshold_calculator.enums import ExtendedEnum
from utility_scripts.threshold_calculator.validator import Validator
from utility_scripts.threshold_calculator.calculator import ThresholdCalculator

_project_root_directory = Path(__file__).absolute().parent.parent.parent


class TestExtendedEnum(unittest.TestCase):
    def test_list_correct(self):
        class EnumTestCase(ExtendedEnum):
            SOME_VAR = 'some_var'
            OTHER_VAR = 'other_var'

        self.assertListEqual(['some_var', 'other_var'], EnumTestCase.list())


class TestValidator(unittest.TestCase):
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
        cls.validator = Validator()

    @classmethod
    def tearDownClass(cls) -> None:
        os.rmdir(cls.depth_1_directory)
        os.rmdir(cls.depth_2_directory)
        os.rmdir(cls.depth_2_directory.parent)

    def test_1_depth_correct(self):
        self.assertWarns(
            UserWarning,
            self.validator.validate_output_argument,
            self.depth_1_directory
        )
        self.assertIn('some_directory', os.listdir(_project_root_directory))

    def test_2_depth_correct(self):
        self.assertWarns(
            UserWarning,
            self.validator.validate_output_argument,
            self.depth_2_directory
        )
        self.assertIn('other_directory', os.listdir(_project_root_directory))
        self.assertIn('further_directory', os.listdir(os.path.join(_project_root_directory, 'other_directory')))


class TestCalculator:
    def test_correct(self):
        resources_directory = os.path.join(
                _project_root_directory,
                'utility_scripts',
                'test',
                'resources')
        dataset = pd.read_csv(
            os.path.join(
                resources_directory,
                'scores_labels.tsv.gz'
            ), sep='\t'
        )
        observed = ThresholdCalculator().calculate_threshold(dataset)
        expected = pd.read_csv(
            os.path.join(
                resources_directory,
                'scores_labels_thresholds.tsv.gz'
            ), sep='\t'
        )
        pd.testing.assert_frame_equal(observed, expected)


if __name__ == '__main__':
    unittest.main()
