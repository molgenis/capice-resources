import os
import unittest
from pathlib import Path

import pandas as pd

from utility_scripts.threshold_calculator.enums import ExtendedEnum
from utility_scripts.threshold_calculator.validator import Validator
from utility_scripts.threshold_calculator.calculator import ThresholdCalculator

_project_root_directory = Path(__file__).absolute().parent.parent.parent


class TestExtendedEnum(unittest.TestCase):
    def test_list_single_enum_correct(self):
        class EnumTestCase(ExtendedEnum):
            SOME_VAR = 'some_var'

        self.assertListEqual(['some_var'], EnumTestCase.list())

    def test_list_multiple_enum_correct(self):
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
        with self.assertWarns(UserWarning) as w:
            self.validator.validate_output_argument(self.depth_1_directory)
        self.assertIn('some_directory', os.listdir(_project_root_directory))
        self.assertEqual('Output directory does not exist, attempting to create.', str(w.warning))

    def test_2_depth_correct(self):
        with self.assertWarns(UserWarning) as w:
            self.validator.validate_output_argument(self.depth_2_directory)
        self.assertIn('other_directory', os.listdir(_project_root_directory))
        self.assertIn('further_directory', os.listdir(os.path.join(_project_root_directory, 'other_directory')))
        self.assertEqual('Output directory does not exist, attempting to create.', str(w.warning))

    def test_incorrect_columns_raised(self):
        class ColumnsEnum(ExtendedEnum):
            first_column = 'first_column'
            second_column = 'second_column'
            third_column = 'third_column'

        test_dataframe = pd.DataFrame(
            {
                'first_column': [1, 2, 3],
                'foo_column': [1, 2, 3],
                'bar_column': [1, 2, 3],
            }
        )

        with self.assertRaises(KeyError) as e:
            self.validator.validate_columns_dataset(test_dataframe, ColumnsEnum.list(), 'testcase')
        # Additional quotes are because raise KeyError adds single quotes to the error message exception
        self.assertEqual(
            "'Required column(s) second_column, third_column missing from testcase!'",
            str(e.exception)
        )


class TestCalculator:
    def test_correct(self):
        resources_directory = os.path.join(
                _project_root_directory,
                'utility_scripts',
                'tests',
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
