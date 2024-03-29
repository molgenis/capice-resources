import unittest
from io import StringIO
from unittest.mock import patch

from molgenis.capice_resources.balance_dataset.verbosity_printer import VerbosityPrinter


class TestVerbosityPrinter(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    def test_verbose_false(self, stdout):
        """
        Test to see if a message does not get printed to stdout if False is supplied to
        VerbosityPrinter.
        """
        printer = VerbosityPrinter(False)
        message = 'This message is unique to this test: test_verbose_false'
        printer.print(message)
        self.assertNotIn(message, stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_verbose_true(self, stdout):
        """
        Test to see if a message does get printed to stdout if True is supplied to
        VerbosityPrinter.
        """
        printer = VerbosityPrinter(True)
        message = 'This message is unique to this test: test_verbose_true'
        printer.print(message)
        self.assertIn(message, stdout.getvalue())


if __name__ == '__main__':
    unittest.main()
