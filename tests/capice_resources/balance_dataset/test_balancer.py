import os
import unittest

import pandas as pd

from molgenis.capice_resources.core import GlobalEnums as Genums
from molgenis.capice_resources.utilities import split_consequences
from tests.capice_resources.testing_utilities import get_testing_resources_dir
from molgenis.capice_resources.balance_dataset.balancer import Balancer
from molgenis.capice_resources.balance_dataset import BalanceDatasetEnums as Menums


class TestBalancer(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loaded_dataset = pd.read_csv(  # type: ignore
            os.path.join(
                get_testing_resources_dir(),
                'labels.tsv.gz'
            ),
            sep=Genums.TSV_SEPARATOR.value,
            na_values=Genums.NA_VALUES.value,
            low_memory=False
        )

    def setUp(self) -> None:
        """
        Note on self.dataset = self.loaded_dataset.copy(deep=True):
        This is done to limit file handling to "labels.tsv.gz". Now it is loaded once and copied
        within RAM.
        """
        self.dataset = self.loaded_dataset.copy(deep=True)  # limiting IO
        self.hardcoded_columns = [
            'variant',
            Genums.CONSEQUENCE.value,
            Genums.GNOMAD_AF.value,
            Genums.BINARIZED_LABEL.value
        ]
        self.test_set = pd.DataFrame(
            data=[
                ['variant_1', 'consequence_1', 0.02, 0],
                ['variant_2', 'consequence_1', 0.01, 1],
                ['variant_3', 'consequence_2', 0.02, 0],
                ['variant_4', 'consequence_2', 0.01, 1]
            ], columns=self.hardcoded_columns  # type: ignore
        )
        self.balancer_nonverbose = Balancer(False)

    def test_sampler_unchanged_more_required(self):
        """
        Test to see if a greater amount of "n_required" than the sample size of "dataset" does
        not change "dataset".
        """
        self.assertEqual(self.balancer_nonverbose._sample_variants(self.test_set, 5).shape[0], 4)

    def test_sampler_unchanged_equal_required(self):
        """
        Test to see if an equal amount of "n_required" to the sample size of "dataset" does not
        change "dataset".
        """
        self.assertEqual(self.balancer_nonverbose._sample_variants(self.test_set, 4).shape[0], 4)

    def test_sampler_changed_less_required(self):
        """
        Test to see if a lower amount of "n_required" to the sample size of "dataset" does in fact
        change the sample size to "n_required".
        """
        self.assertEqual(self.balancer_nonverbose._sample_variants(self.test_set, 2).shape[0], 2)

    def test_set_columns(self):
        """
        Test to see if the balancer.columns are correctly set through the _set_columns method.
        """
        columns = ['foo', 'bar', 'baz']
        test_dataset = pd.DataFrame(columns=columns)
        self.balancer_nonverbose._set_columns(test_dataset.columns)
        pd.testing.assert_index_equal(self.balancer_nonverbose.columns, pd.Index(columns))

    def set_up_test_balancer(self):
        balanced_dataset, _ = self.balancer_nonverbose.balance(self.dataset)
        self.assertGreater(balanced_dataset.shape[0], 0)
        self.assertEqual(
            balanced_dataset[balanced_dataset[Genums.BINARIZED_LABEL.value] == 0].shape[0],
            balanced_dataset[balanced_dataset[Genums.BINARIZED_LABEL.value] == 1].shape[0]
        )
        self.assertIn(Menums.BALANCED_ON.value, balanced_dataset.columns)
        return balanced_dataset

    def test_balancer_consequences(self):
        """
        Function to test the balancer consequences with a real life dataset
        """
        balanced_dataset = self.set_up_test_balancer()
        incorrect_consequences = []
        consequences = split_consequences(balanced_dataset[Genums.CONSEQUENCE.value])
        for consequence in consequences:
            subset = balanced_dataset[balanced_dataset[Menums.BALANCED_ON.value] == consequence]
            n_benign = subset[subset[Genums.BINARIZED_LABEL.value] == 0].shape[0]
            n_pathogenic = subset[subset[Genums.BINARIZED_LABEL.value] == 1].shape[0]
            if n_benign != n_pathogenic:
                incorrect_consequences.append(
                    f'{consequence} (n_b: {n_benign}, n_p: {n_pathogenic})'
                )
        self.assertListEqual([], incorrect_consequences)

    def test_balancer_afbins(self):
        """
        Function to test the balancer allele frequency bins with a real life dataset
        :return:
        """
        balanced_dataset = self.set_up_test_balancer()
        # Required, because 0 impute is reset during balancing
        balanced_dataset[Genums.GNOMAD_AF.value].fillna(0, inplace=True)
        incorrect_afbins = []
        for ind in range(len(Genums.AF_BINS.value) - 1):  # type: ignore
            lower_bound = Genums.AF_BINS.value[ind]
            upper_bound = Genums.AF_BINS.value[ind + 1]
            subset = balanced_dataset[
                (balanced_dataset[Genums.GNOMAD_AF.value] >= lower_bound) &
                (balanced_dataset[Genums.GNOMAD_AF.value] < upper_bound)
                ]
            n_benign = subset[subset[Genums.BINARIZED_LABEL.value] == 0].shape[0]
            n_pathogenic = subset[subset[Genums.BINARIZED_LABEL.value] == 1].shape[0]
            if n_benign != n_pathogenic:
                incorrect_afbins.append(
                    f'{lower_bound}-{upper_bound} (n_b: {n_benign}, n_p: {n_pathogenic})'
                )
        self.assertListEqual([], incorrect_afbins)

    def test_balanced_remainder(self):
        balanced, remainder = self.balancer_nonverbose.balance(self.dataset)
        self.assertFalse(
            pd.concat(
                [balanced, remainder],
                axis=0
            ).duplicated().any())

    def _test_consequence(self, test_set: pd.DataFrame, expected_rows: dict) -> None:
        """
        Function to check "test_set" according to the amount of "expected_rows".
        Done to prevent duplication of test code.
        """
        self.balancer_nonverbose._set_bins(test_set[Genums.GNOMAD_AF.value])
        self.balancer_nonverbose._set_columns(test_set.columns)
        consequences = split_consequences(test_set[Genums.CONSEQUENCE.value])
        for consequence in consequences:
            observed = self.balancer_nonverbose._process_consequence(
                test_set[
                    (test_set[Genums.CONSEQUENCE.value].str.contains(consequence, regex=False)) &
                    (test_set[Genums.BINARIZED_LABEL.value] == 1)
                    ],
                test_set[
                    (test_set[Genums.CONSEQUENCE.value].str.contains(consequence, regex=False)) &
                    (test_set[Genums.BINARIZED_LABEL.value] == 0)
                    ]
            )
            self.assertEqual(
                observed.shape[0],
                expected_rows[consequence],
                msg=f'Test failed on consequence: {consequence}'
            )
            n_benign = observed[observed[Genums.BINARIZED_LABEL.value] == 0].shape[0]
            n_patho = observed[observed[Genums.BINARIZED_LABEL.value] == 1].shape[0]
            self.assertEqual(
                n_benign,
                n_patho,
                msg=f'Test failed on consequence: {consequence} for n_benign: {n_benign} and '
                    f'n_pathogenic: {n_patho}'
            )

    def test_process_consequence_equal(self):
        """
        Test for the _process_consequence method with 2 consequences that have an equal amount of
        benign and pathogenic variants
        """
        test_data = [
            ['variant_1', 'consequence_1', 0.01, 0],
            ['variant_2', 'consequence_1', 0.02, 0],
            ['variant_3', 'consequence_1', 0.03, 0],
            ['variant_4', 'consequence_1', 0.03, 1],
            ['variant_5', 'consequence_1', 0.02, 1],
            ['variant_6', 'consequence_1', 0.01, 1],
            ['variant_7', 'consequence_2', 0.01, 0],
            ['variant_8', 'consequence_2', 0.02, 0],
            ['variant_9', 'consequence_2', 0.03, 0],
            ['variant_10', 'consequence_2', 0.03, 1],
            ['variant_11', 'consequence_2', 0.02, 1],
            ['variant_12', 'consequence_2', 0.01, 1]
        ]
        test_set = pd.DataFrame(
            test_data, columns=self.hardcoded_columns
        )
        expected_rows = {'consequence_1': 6, 'consequence_2': 6}
        self._test_consequence(test_set, expected_rows)

    def test_process_consequence_patho_bias(self):
        """
        Test for the _process_consequence method with 2 consequences, of which one has a pathogenic
        variant bias
        """
        test_data = [
            ['variant_1', 'consequence_1', 0.01, 0],
            ['variant_2', 'consequence_1', 0.02, 1],
            ['variant_3', 'consequence_1', 0.03, 1],
            ['variant_4', 'consequence_1', 0.03, 1],
            ['variant_5', 'consequence_1', 0.02, 1],
            ['variant_6', 'consequence_1', 0.01, 1],
            ['variant_7', 'consequence_2', 0.01, 0],
            ['variant_8', 'consequence_2', 0.02, 0],
            ['variant_9', 'consequence_2', 0.03, 0],
            ['variant_10', 'consequence_2', 0.03, 1],
            ['variant_11', 'consequence_2', 0.02, 1],
            ['variant_12', 'consequence_2', 0.01, 1]
        ]
        test_set = pd.DataFrame(
            test_data, columns=self.hardcoded_columns
        )
        expected_rows = {'consequence_1': 2, 'consequence_2': 6}
        self._test_consequence(test_set, expected_rows)

    def test_process_consequence_double_patho_bias(self):
        """
        Test for the _process_consequence method with 2 consequences, both having more pathogenic
        variants than benign
        """
        test_data = [
            ['variant_1', 'consequence_1', 0.01, 0],
            ['variant_2', 'consequence_1', 0.02, 1],
            ['variant_3', 'consequence_1', 0.03, 1],
            ['variant_4', 'consequence_1', 0.03, 1],
            ['variant_5', 'consequence_1', 0.02, 1],
            ['variant_6', 'consequence_1', 0.01, 1],
            ['variant_7', 'consequence_2', 0.01, 0],
            ['variant_8', 'consequence_2', 0.02, 1],
            ['variant_9', 'consequence_2', 0.03, 1],
            ['variant_10', 'consequence_2', 0.03, 1],
            ['variant_11', 'consequence_2', 0.02, 1],
            ['variant_12', 'consequence_2', 0.01, 1]
        ]
        test_set = pd.DataFrame(
            test_data, columns=self.hardcoded_columns
        )
        expected_rows = {'consequence_1': 2, 'consequence_2': 2}
        self._test_consequence(test_set, expected_rows)

    def test_process_consequence_benign_bias(self):
        """
        Test for the _process_consequence method with 2 consequences, of which one has more benign
        variants than pathogenic
        """
        test_data = [
            ['variant_1', 'consequence_1', 0.01, 0],
            ['variant_2', 'consequence_1', 0.02, 0],
            ['variant_3', 'consequence_1', 0.03, 0],
            ['variant_4', 'consequence_1', 0.03, 0],
            ['variant_5', 'consequence_1', 0.02, 0],
            ['variant_6', 'consequence_1', 0.01, 1],
            ['variant_7', 'consequence_2', 0.01, 0],
            ['variant_8', 'consequence_2', 0.02, 0],
            ['variant_9', 'consequence_2', 0.03, 0],
            ['variant_10', 'consequence_2', 0.03, 1],
            ['variant_11', 'consequence_2', 0.02, 1],
            ['variant_12', 'consequence_2', 0.01, 1]
        ]
        test_set = pd.DataFrame(
            test_data, columns=self.hardcoded_columns
        )
        expected_rows = {'consequence_1': 2, 'consequence_2': 6}
        self._test_consequence(test_set, expected_rows)

    def test_process_consequence_double_benign_bias(self):
        """
        Test for the _process_consequence method with 2 consequences, both having more benign
        variants than pathogenic
        """
        test_data = [
            ['variant_1', 'consequence_1', 0.01, 0],
            ['variant_2', 'consequence_1', 0.02, 0],
            ['variant_3', 'consequence_1', 0.03, 0],
            ['variant_4', 'consequence_1', 0.03, 0],
            ['variant_5', 'consequence_1', 0.02, 0],
            ['variant_6', 'consequence_1', 0.01, 1],
            ['variant_7', 'consequence_2', 0.01, 0],
            ['variant_8', 'consequence_2', 0.02, 0],
            ['variant_9', 'consequence_2', 0.03, 0],
            ['variant_10', 'consequence_2', 0.03, 0],
            ['variant_11', 'consequence_2', 0.02, 0],
            ['variant_12', 'consequence_2', 0.01, 1]
        ]
        test_set = pd.DataFrame(
            test_data, columns=self.hardcoded_columns
        )
        expected_rows = {'consequence_1': 2, 'consequence_2': 2}
        self._test_consequence(test_set, expected_rows)

    def test_process_consequence_double_bias(self):
        """
        Test for the _process_consequence method with 2 consequences, one having a pathogenic bias
        and the other a benign bias
        """
        test_data = [
            ['variant_1', 'consequence_1', 0.01, 0],
            ['variant_2', 'consequence_1', 0.02, 0],
            ['variant_3', 'consequence_1', 0.03, 0],
            ['variant_4', 'consequence_1', 0.03, 0],
            ['variant_5', 'consequence_1', 0.02, 0],
            ['variant_6', 'consequence_1', 0.01, 1],
            ['variant_7', 'consequence_2', 0.01, 0],
            ['variant_8', 'consequence_2', 0.02, 1],
            ['variant_9', 'consequence_2', 0.03, 1],
            ['variant_10', 'consequence_2', 0.03, 1],
            ['variant_11', 'consequence_2', 0.02, 1],
            ['variant_12', 'consequence_2', 0.01, 1]
        ]
        test_set = pd.DataFrame(
            test_data, columns=self.hardcoded_columns
        )
        expected_rows = {'consequence_1': 2, 'consequence_2': 2}
        self._test_consequence(test_set, expected_rows)

    def test_process_consequence_multiconsequence(self):
        test_data = [
            ['variant_1', 'consequence_1&consequence_2&consequence_3', 0.01, 0],
            ['variant_2', 'consequence_2', 0.01, 0],
            ['variant_3', 'consequence_2', 0.01, 0],
            ['variant_4', 'consequence_1', 0.01, 1],
            ['variant_5', 'consequence_1', 0.01, 1],
            ['variant_6', 'consequence_1&consequence_2', 0.01, 1],
            ['variant_7', 'consequence_1&consequence_3', 0.01, 0],
            ['variant_8', 'consequence_1&consequence_2', 0.01, 1]
        ]
        test_set = pd.DataFrame(
            test_data, columns=self.hardcoded_columns
        )
        expected_rows = {'consequence_1': 4, 'consequence_2': 4, 'consequence_3': 0}
        self._test_consequence(test_set, expected_rows)

    def test_duplicate_processing_balancer_consequence_missing(self):
        """
        Test to see if a sample with multiple consequences gets, even if it can balance another
        consequence
        No call to _test_consequence, since that method does not check if a consequence has been
        sampled already, the balance() method does.
        """
        test_dataset = pd.DataFrame(
            {
                Genums.CONSEQUENCE.value: [
                    'consequence_1&consequence_2',
                    'consequence_1',
                    'consequence_2'
                ],
                Genums.BINARIZED_LABEL.value: [0, 1, 1],
                Genums.GNOMAD_AF.value: [0.0, 0.0, 0.0]
            }
        )
        observed, remainder = self.balancer_nonverbose.balance(test_dataset)
        self.assertFalse(observed.duplicated().any())
        self.assertFalse('consequence_2' in observed[Genums.CONSEQUENCE.value].values)
        self.assertTrue('consequence_2' in remainder[Genums.CONSEQUENCE.value].values)


if __name__ == '__main__':
    unittest.main()
