import unittest

from molgenis.capice_resources.core import Module, GlobalEnums, ExtendedEnum


class TestMultipleEnum(ExtendedEnum):
    FOO = 'foo'
    BAR = 'bar'
    BAZ = 'baz'


class TestSingleEnum(ExtendedEnum):
    FOO = 'foo'


class TestExtendedEnum(unittest.TestCase):
    def test_multiple_enum_correct(self):
        self.assertListEqual(TestMultipleEnum.list(), ['foo', 'bar', 'baz'])

    def test_single_enum_correct(self):
        self.assertListEqual(TestSingleEnum.list(), ['foo'])


if __name__ == '__main__':
    unittest.main()
