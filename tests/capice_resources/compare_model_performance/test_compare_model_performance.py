import os
import unittest
from unittest.mock import patch

import pandas as pd
from matplotlib import pyplot as plt

from molgenis.capice_resources.core.errors import SampleSizeMismatchError
from tests.capice_resources.testing_utilities import get_testing_resources_dir, \
    check_and_remove_directory
from molgenis.capice_resources.compare_model_performance.__main__ import CompareModelPerformance


class TestCompareModelPerformance(unittest.TestCase):
    output_directory = os.path.join(
        get_testing_resources_dir(),
        'compare_model_performance',
        'output'
    )
    expected_figures = [
        'auc',
        'roc',
        'allele_frequency',
        'score_distributions_box',
        'score_distributions_vio',
        'score_differences_vio',
        'score_differences_box'
    ]

    @classmethod
    def tearDownClass(cls) -> None:
        for file in os.listdir(cls.output_directory):
            check_and_remove_directory(os.path.join(cls.output_directory, file))

    def tearDown(self) -> None:
        """
        plt.close('all') is required, as matplotlib keeps all figures loaded. With the amount of
        matplotlib related tests in capice-resources, matplotlib does throw an warning that too
        many figures are loaded unless this call is made.
        """
        plt.close('all')

    @patch(
        'sys.argv',
        [
            __file__,
            '-a', os.path.join(get_testing_resources_dir(), 'scores.tsv.gz'),
            '-l', os.path.join(get_testing_resources_dir(), 'labels.tsv.gz'),
            '-b', os.path.join(get_testing_resources_dir(), 'scores.tsv.gz'),
            '-o', output_directory
        ]
    )
    def test_component_full(self):
        """
        Full component testing of the compare-model-performance from CLI to export.
        It does not matter that the scores for both model 1 and model 2 are equal,
        as compare-model-performance does not really care about that.
        """
        CompareModelPerformance().run()
        for figure in self.expected_figures:
            self.assertIn(figure + '.png', os.listdir(self.output_directory))

    @patch(
        'sys.argv',
        [
            __file__,
            '-a', os.path.join(get_testing_resources_dir(),
                               'compare_model_performance',
                               'scores_no_benign_frameshifts.tsv.gz'),
            '-l', os.path.join(get_testing_resources_dir(),
                               'compare_model_performance',
                               'labels_no_benign_frameshifts.tsv.gz'),
            '-b', os.path.join(get_testing_resources_dir(), 'scores.tsv.gz'),
            '-m', os.path.join(get_testing_resources_dir(), 'labels.tsv.gz'),
            '-o', output_directory
        ]
    )
    def test_component_full_model_1_missing_consequence(self):
        """
        Full component testing of the compare-model-performance from CLI to export.
        Tests the case where model 1 does not contain data for benign frameshift variants and
        pathogenic splice_polypirimidine_tract variants, but model 2 does.
        """
        with self.assertWarns(UserWarning) as w:
            CompareModelPerformance().run()
        for figure in self.expected_figures:
            self.assertIn(figure + '.png', os.listdir(self.output_directory))
        self.assertEqual(
            str(w.warning),
            'Model files differ in sample size for consequence(s): '
            '5_prime_UTR_variant, '
            'coding_sequence_variant, '
            'frameshift_variant, intron_variant, '
            'splice_acceptor_variant, splice_donor_5th_base_variant, '
            'splice_donor_variant, splice_polypyrimidine_tract_variant, '
            'splice_region_variant, stop_gained'
        )

    @patch(
        'sys.argv',
        [
            __file__,
            '-a', os.path.join(get_testing_resources_dir(), 'scores.tsv.gz'),
            '-l', os.path.join(get_testing_resources_dir(), 'labels.tsv.gz'),
            '-b', os.path.join(get_testing_resources_dir(),
                               'compare_model_performance',
                               'scores_no_benign_frameshifts.tsv.gz'),
            '-m', os.path.join(get_testing_resources_dir(),
                               'compare_model_performance',
                               'labels_no_benign_frameshifts.tsv.gz'),
            '-o', output_directory
        ]
    )
    def test_component_full_model_2_missing_consequence(self):
        """
        Full component testing of the compare-model-performance from CLI to export.
        Inverse of test "test_component_full_model_1_missing_consequence"
        """
        with self.assertWarns(UserWarning) as w:
            CompareModelPerformance().run()
        for figure in self.expected_figures:
            self.assertIn(figure + '.png', os.listdir(self.output_directory))
        self.assertEqual(
            str(w.warning),
            'Model files differ in sample size for consequence(s): '
            '5_prime_UTR_variant, '
            'coding_sequence_variant, '
            'frameshift_variant, intron_variant, '
            'splice_acceptor_variant, splice_donor_5th_base_variant, '
            'splice_donor_variant, splice_polypyrimidine_tract_variant, '
            'splice_region_variant, stop_gained'
        )

    @patch(
        'sys.argv',
        [
            __file__,
            '-a', os.path.join(get_testing_resources_dir(), 'scores.tsv.gz'),
            '-l', os.path.join(get_testing_resources_dir(), 'labels.tsv.gz'),
            '-o', output_directory
        ]
    )
    def test_component_single_model_plot(self):
        """
        Full component test to see if code functions when only 1 model data is supplied
        """
        CompareModelPerformance().run()
        for figure in self.expected_figures:
            self.assertIn(figure + '.png', os.listdir(self.output_directory))

    @patch(
        'sys.argv',
        [
            __file__,
            '-a', os.path.join(get_testing_resources_dir(), 'scores.tsv.gz'),
            '-l', os.path.join(get_testing_resources_dir(), 'labels.tsv.gz'),
            '-b', os.path.join(get_testing_resources_dir(), 'scores.tsv.gz'),
            '-m', os.path.join(get_testing_resources_dir(), 'labels.tsv.gz'),
            '-o', output_directory
        ]
    )
    def test_component_labels2_supplied(self):
        """
        Full component test to see if code functions when model 2 labels are supplied in CLI
        """
        CompareModelPerformance().run()
        for figure in self.expected_figures:
            self.assertIn(figure + '.png', os.listdir(self.output_directory))

    @patch(
        'sys.argv',
        [
            __file__,
            '-a', os.path.join(get_testing_resources_dir(), 'scores.tsv.gz'),
            '-l', os.path.join(get_testing_resources_dir(), 'labels.tsv.gz'),
            '-m', os.path.join(get_testing_resources_dir(), 'labels.tsv.gz'),
            '-o', output_directory
        ]
    )
    def test_raise_ioerror_incorrect_cli(self):
        """
        Full component testing of the compare-model-performance from CLI to export.
        It does not matter that the scores for both model 1 and model 2 are equal,
        as compare-model-performance does not really care about that.
        """
        with self.assertRaises(IOError) as e:
            CompareModelPerformance().run()
        self.assertEqual(
            str(e.exception),
            'Model 2 label argument is supplied, while model 2 score argument is not.'
        )

    def test_attempt_mismatch_merge_fail(self):
        """
        Test to see if the "_merge_scores_and_labels" function raises the SampleSizeMismatchError as
        a result of unequal sample sizes and force_merge being set to False (by default).

        Since it doesn't matter what is inside the dataframes, supplying empty frames.
        (as the error is raised before anything is done with the frame)
        """
        module = CompareModelPerformance()
        module.force_merge = False
        with self.assertRaises(SampleSizeMismatchError) as e:
            module._merge_scores_and_labes(
                pd.DataFrame({'foo': ['bar', 'baz']}),
                pd.DataFrame({'bar': ['foo']})
            )
        self.assertEqual(
            str(e.exception),
            'Sample sizes differ and -f/--force-merge is not supplied!'
        )

    def test_attempt_mismatch_merge_pass(self):
        """
        More expanded test to see if "_attempt_mismatch_merge" correctly merges 2 unequal sample
        size dataframes if force_merge is supplied as True. Also checks if a unique column to
        "labels" is preserved after the merge (mimicking the binarized_label column).
        """
        module = CompareModelPerformance()
        module.force_merge = True
        scores = pd.DataFrame(
            {
                 'chr': [1, 2, 3, 4],
                 'pos': [100, 200, 300, 400],
                 'ref': ['A', 'C', 'T', 'G'],
                 'alt': ['T', 'G', 'A', 'C'],
                 'gene_name': ['foo', 'foo', 'bar', 'baz']
            }
        )
        labels = pd.DataFrame(
            {
                'CHROM': [1, 2, 3],
                'POS': [100, 200, 300],
                'REF': ['A', 'C', 'T'],
                'ALT': ['T', 'G', 'A'],
                'SYMBOL': ['foo', 'foo', 'bar'],
                'SuperUniqueLabelColumn': [1, 0, 0]
            }
        )
        observed = module._merge_scores_and_labes(scores, labels)
        self.assertIn('CHROM', observed.columns)
        self.assertIn('SuperUniqueLabelColumn', observed.columns)


if __name__ == '__main__':
    unittest.main()
