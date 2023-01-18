import unittest
from unittest.mock import patch
from argparse import Namespace
from io import StringIO

from molgenis.capice_resources.core.command_line_interface import CommandLineInterface


class TestCommandLineInterface(unittest.TestCase):
    def setUp(self) -> None:
        self.cli = CommandLineInterface()
        self.parser = self.cli.create_initial('Testing', 'For testing purposes')

    @patch('sys.argv', [__file__])  # Required for Pytest since that adds additional sys.argv
    def test_emtpy_cli(self):
        """
        Test to see if an empty Namespace object is returned when the CLI is not supplied with
        argument (groups).
        """
        self.cli.parse_args(self.parser)
        self.assertEqual(self.cli.arguments, Namespace())

    @patch('sys.argv', [__file__])  # Required for Pytest since that adds additional sys.argv
    def test_has_default_not_supplied(self):
        """
        Test to see if a default value is properly return in a dictionary of "{argument:
        argument_value}" when the CLI argument is not given on the command line.
        """
        self.parser.add_argument('-i', '--input', default='foobar', help='foobar test')
        self.cli.parse_args(self.parser)
        self.assertIn('input', self.cli.arguments)
        self.assertEqual({'input': 'foobar'}, self.cli.get_argument('input'))

    @patch('sys.argv', [__file__, '-i', 'barbaz'])
    def test_has_default_other_supplied(self):
        """
        Test to see if a default value is overwritten with the CLI command line supplied
        argument, properly returned in a dictionary of "{argument: argument_value}".
        """
        self.parser.add_argument('-i', '--input', default='foobar', help='foobar test')
        self.cli.parse_args(self.parser)
        self.assertIn('input', self.cli.arguments)
        self.assertEqual({'input': 'barbaz'}, self.cli.get_argument('input'))

    @patch('sys.stderr', new_callable=StringIO)
    def test_no_default_not_supplied(self, stderr):
        """
        Test to check if the CLI parser exits when a required argument is not supplied on
        the command line.
        """
        self.parser.add_argument('-i', '--input', required=True, help='foobar test')
        with self.assertRaises(SystemExit):
            self.cli.parse_args(self.parser)
        self.assertIn('error: the following arguments are required: -i/--input', stderr.getvalue())

    @patch('sys.argv', [__file__, '-i', 'foobar'])
    def test_argument_not_supplied(self):
        """
        Double test to see if a required argument is supplied through the command line and
        properly returned, as well as an "unknown argument" is returned properly as None.
        Unknown argument is an argument that is not added to the parser, but is requested from CLI.
        """
        self.parser.add_argument('-i', '--input', required=True, help='foobar test')
        self.cli.parse_args(self.parser)
        self.assertIn('input', self.cli.arguments)
        self.assertEqual({'input': 'foobar'}, self.cli.get_argument('input'))
        self.assertEqual({'output': None}, self.cli.get_argument('output'))


if __name__ == '__main__':
    unittest.main()
