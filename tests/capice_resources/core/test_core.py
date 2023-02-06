import unittest
from unittest.mock import patch
from argparse import ArgumentParser

import pandas as pd

from tests.capice_resources.testing_utilities import temp_output_file_path_and_name, \
    check_and_remove_directory
from molgenis.capice_resources.core import Module, CommandLineInterface, ColumnEnums, VCFEnums, \
    TSVFileEnums


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

    def _validate_module_specific_arguments(
            self,
            parser: CommandLineInterface
    ) -> dict[str, str | object]:
        foobar = parser.get_argument('input')
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
        splitted_foobar = foobar.split(' ')  # type: ignore
        none_object = arguments['fake']
        if none_object is not None:
            raise AssertionError('Incorrect implementation of providing None for non-existing '
                                 'argument')
        frame = pd.DataFrame({'data': splitted_foobar})
        frame['mapper'] = frame['data'].map({'foo': 1, 'bar': 2})
        return {'frame': frame}

    def export(self, output: dict[object, object]) -> None:
        self.exporter.export_pandas_file(temp_output_file_path_and_name(), output['frame'])


class TestModule(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        check_and_remove_directory(temp_output_file_path_and_name())

    @classmethod
    def tearDownClass(cls) -> None:
        check_and_remove_directory(temp_output_file_path_and_name())

    @patch('sys.argv', [__file__, '-i', 'foo bar'])
    def test_module(self):
        """
        Component testing of proper function of the core "Module" metaclass.
        """
        module = ModuleMetaclassTest()
        module.run()
        expected = pd.DataFrame(
            {
                'data': ['foo', 'bar'],
                'mapper': [1, 2]
            }
        )
        observed = pd.read_csv(  # type: ignore
            temp_output_file_path_and_name(),
            sep='\t'
        )
        check_and_remove_directory(temp_output_file_path_and_name())
        pd.testing.assert_frame_equal(observed, expected)


class TestEnums(unittest.TestCase):
    def test_column_enum_value(self):
        """
        Test to see if dataset_source is correctly saved within ColumnEnums.
        """
        self.assertEqual('dataset_source', ColumnEnums.DATASET_SOURCE.value)

    def test_vcf_enum(self):
        """
        Test to see if the VCFEnums is set up properly
        """
        self.assertEqual('#CHROM', VCFEnums.CHROM.vcf_name)
        self.assertEqual('CHROM', VCFEnums.CHROM.processed_name)
        self.assertEqual('chr', VCFEnums.CHROM.shortened_name)
        self.assertEqual('POS', VCFEnums.POS.processed_name)
        self.assertEqual('POS', VCFEnums.POS.vcf_name)
        self.assertEqual('pos', VCFEnums.POS.lower)

    def test_tsv_enum_tsv_extensions(self):
        """
        Test to see if the (.tsv.gz, .tsv) tuple within TSVFileEnums.TSV_EXTENSIONS is set
        correctly.
        """
        self.assertTupleEqual(('.tsv.gz', '.tsv'), TSVFileEnums.TSV_EXTENSIONS.value)


if __name__ == '__main__':
    unittest.main()
