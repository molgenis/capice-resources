import unittest

import pandas as pd

from molgenis.capice_resources.utilities import merge_dataset_rows, extract_key_value_dict_cli


class TestUtilities(unittest.TestCase):
    def setUp(self) -> None:
        self.frame1 = pd.DataFrame({'foo': [1, 2, 3]})
        self.frame2_foo = pd.DataFrame({'foo': [4, 5, 6]})
        self.frame2_bar = pd.DataFrame({'bar': [4, 5, 6]})

    def test_merge_rows_simple_2_frame(self):
        observed = merge_dataset_rows(self.frame1, self.frame2_foo)
        expected = pd.DataFrame({'foo': [1, 2, 3, 4, 5, 6]})
        pd.testing.assert_frame_equal(observed, expected)

    def test_merge_rows_simple_3_frame(self):
        frame1 = pd.DataFrame({'foo': [1, 2]})
        frame2 = pd.DataFrame({'foo': [3, 4]})
        frame3 = pd.DataFrame({'foo': [5, 6]})
        observed = merge_dataset_rows(frame1, frame2, frame3)
        expected = pd.DataFrame({'foo': [1, 2, 3, 4, 5, 6]})
        pd.testing.assert_frame_equal(observed, expected)

    def test_merge_rows_column_mismatch_2_frame(self):
        observed = merge_dataset_rows(self.frame1, self.frame2_bar)
        expected = pd.DataFrame(
            {
                'foo': [1, 2, 3, None, None, None],
                'bar': [None, None, None, 4, 5, 6]
             }
        )
        pd.testing.assert_frame_equal(observed, expected)

    def test_merge_rows_index_correct(self):
        observed = merge_dataset_rows(self.frame1, self.frame2_foo)
        pd.testing.assert_index_equal(observed.index, pd.Index(range(0, 6)))

    def test_merge_rows_ignore_index_false_correct(self):
        self.frame1.index = ['a', 'b', 'c']
        self.frame2_foo.index = ['d', 'e', 'f']
        observed = merge_dataset_rows(self.frame1, self.frame2_foo, ignore_index=False)
        pd.testing.assert_index_equal(observed.index, pd.Index(['a', 'b', 'c', 'd', 'e', 'f']))

    def test_merge_rows_same_index_ignore_index_false(self):
        self.frame1.index = ['a', 'b', 'c']
        self.frame2_foo.index = ['b', 'c', 'e']
        observed = merge_dataset_rows(self.frame1, self.frame2_foo, ignore_index=False)
        # Intended, by default pd.concat flag verify_integrity is set false to reduce
        # how expensive the function is.
        pd.testing.assert_index_equal(observed.index, pd.Index(['a', 'b', 'c', 'b', 'c', 'e']))

    def test_extract_key_value_dict_simple_pass(self):
        test_case = {'foo': 'bar/baz'}
        observed = extract_key_value_dict_cli(test_case)
        self.assertTupleEqual(observed, ('foo', 'bar/baz'))

    def test_extract_key_value_dict_simple_none_pass(self):
        test_case = {'foo': None}
        observed = extract_key_value_dict_cli(test_case)
        self.assertTupleEqual(observed, ('foo', None))

    def test_extract_key_value_incorrect_pass(self):
        test_case = {'foo': 0.01}
        observed = extract_key_value_dict_cli(test_case)  # type: ignore
        self.assertTupleEqual(observed, ('foo', '0.01'))


if __name__ == '__main__':
    unittest.main()
