import unittest
from unittest.mock import patch
from argparse import ArgumentParser

import pandas as pd

from tests.capice_resources.test_utilities import temp_output_file_path_and_name, \
    check_and_remove_directory
from molgenis.capice_resources.core import Module, GlobalEnums, ExtendedEnum, CommandLineInterface


class TestMultipleEnum(ExtendedEnum):
    FOO = 'foo'
    BAR = 'bar'
    BAZ = 'baz'


class TestSingleEnum(ExtendedEnum):
    FOO = 'foo'


class ModuleMetaclassTest(Module):
    """
    Testing for the mocked input "foo bar" (_create_module_specific_arguments)
    then
    Validating that "foo bar" was supplied in the CLI (_validate_module_specific_arguments)
    then
    Splitting foo and bar into a list, creating a dataframe out of it and mapping 1 to foo and 2
    to bar (run_module)
    then
    Exporting the mapped dataframe to tests/resources

    Then testing should assert frame equal.
    """
    def __init__(self):
        super().__init__(program='testing', description='testing purposes')

    @staticmethod
    def _create_module_specific_arguments(parser: ArgumentParser) -> ArgumentParser:

        required = parser.add_argument_group('Required arguments')
        required.add_argument(
            '-i',
            '--input',
            required=True,
            help='Input test argument ready to be mocked'
        )
        return parser

    def _validate_module_specific_arguments(self, parser: CommandLineInterface) -> dict[
        str, str | object]:
        foobar = parser.get_argument('input')
        print(foobar)
        if foobar != {"input": "foo bar"}:
            raise AssertionError('Incorrect implementation of mocking')
        # Adding a fake argument that should always return None
        none_value = parser.get_argument('fake')
        return {
            **foobar,
            **none_value
        }

    def run_module(self, arguments: dict[str, str | object]) -> dict:
        foobar = arguments['input']
        splitted_foobar = foobar.split(' ')
        none_object = arguments['fake']
        if none_object is not None:
            raise AssertionError('Incorrect implementation of providing None for non-existing '
                                 'argument')
        frame = pd.DataFrame({'data': splitted_foobar})
        frame['mapper'] = frame['data'].map({'foo': 1, 'bar': 2})
        return {'frame': frame}

    def export(self, output: dict[object, object]) -> None:
        self.exporter.export_pandas_file(temp_output_file_path_and_name(), output['frame'])


class TestExtendedEnum(unittest.TestCase):
    def test_multiple_enum_correct(self):
        self.assertListEqual(TestMultipleEnum.list(), ['foo', 'bar', 'baz'])

    def test_single_enum_correct(self):
        self.assertListEqual(TestSingleEnum.list(), ['foo'])



class TestModule(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        check_and_remove_directory(temp_output_file_path_and_name())

    @classmethod
    def tearDownClass(cls) -> None:
        check_and_remove_directory(temp_output_file_path_and_name())

    @patch('sys.argv', [__file__, '-i', 'foo bar'])
    def test_module(self):
        module = ModuleMetaclassTest()
        module.run()
        expected = pd.DataFrame(
            {
                'data': ['foo', 'bar'],
                'mapper': [1, 2]
            }
        )
        observed = pd.read_csv(temp_output_file_path_and_name(), sep='\t')
        pd.testing.assert_frame_equal(observed, expected)


class TestGlobalEnums(unittest.TestCase):
    def test_global_enum_present(self):
        self.assertIn('dataset_source', GlobalEnums.list())


    def test_global_enum_value(self):
        self.assertEqual('dataset_source', GlobalEnums.DATASET_SOURCE.value)


    def test_global_enum_tsv_extensions(self):
        self.assertTupleEqual(('.tsv.gz', '.tsv'), GlobalEnums.TSV_EXTENSIONS.value)


if __name__ == '__main__':
    unittest.main()
