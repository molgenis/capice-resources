import unittest

import pandas as pd

from molgenis.capice_resources.train_data_creator.filter import SVFilter


class TestSVFilter(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        """
        Small note: the length of "structural_variant" is exactly 62 characters long.

        The structural variant has been set up this way, because without the tuple and without
        the ignore statement mypy will complain but with the ignore statement flake8 will complain.
        """
        cls.sv_filter = SVFilter()  # type: ignore
        cls.structural_variant = (  # type: ignore
            'THISISNOTAVARIANTBUTASTRUCTURALVARIANTTHATHASALENGTHOFSIXTYTWO'
        )

    def test_filter_correct_ref_sv(self):
        """
        Tests if a StructuralVariant present in only REF is correctly filtered out.
        """
        test_case = pd.DataFrame(
            {
                'REF': [self.structural_variant, 'A', 'C'],
                'ALT': ['C', 'T', 'G']
            }
        )
        shape = test_case.shape[0]
        self.sv_filter.filter(test_case)
        self.assertNotIn(self.structural_variant, test_case['REF'].values)
        self.assertEqual(shape - 1, test_case.shape[0])

    def test_filter_correct_alt_sv(self):
        """
        Tests if a StructuralVariant present in only ALT is correctly filtered out.
        """
        test_case = pd.DataFrame(
            {
                'REF': ['C', 'A', 'T'],
                'ALT': ['T', self.structural_variant, 'A']
            }
        )
        shape = test_case.shape[0]
        self.sv_filter.filter(test_case)
        self.assertNotIn(self.structural_variant, test_case['ALT'].values)
        self.assertEqual(shape - 1, test_case.shape[0])

    def test_filter_correct_ref_alt_sv(self):
        """
        Tests if StructuralVariants present in both REF and ALT are correctly filtered out.
        """
        test_case = pd.DataFrame(
            {
                'REF': ['C', self.structural_variant, 'A'],
                'ALT': ['G', 'T', self.structural_variant]
            }
        )
        shape = test_case.shape[0]
        self.sv_filter.filter(test_case)
        self.assertNotIn(self.structural_variant, test_case['REF'].values)
        self.assertNotIn(self.structural_variant, test_case['ALT'].values)
        self.assertEqual(shape - 2, test_case.shape[0])

    def test_filter_none_removed(self):
        """
        Tests that no variants are filtered out when no StructuralVariants are present.
        """
        test_case = pd.DataFrame(
            {
                'REF': ['C', 'A', 'T'],
                'ALT': ['G', 'T', 'A']
            }
        )
        shape = test_case.shape[0]
        self.sv_filter.filter(test_case)
        self.assertEqual(test_case.shape[0], shape)


if __name__ == '__main__':
    unittest.main()
