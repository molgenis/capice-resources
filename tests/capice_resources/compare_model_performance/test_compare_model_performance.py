import os
import unittest
from unittest.mock import patch

import pandas as pd
from matplotlib import pyplot as plt

from molgenis.capice_resources.core import ColumnEnums, VCFEnums
from molgenis.capice_resources.core.errors import SampleMismatchError
from tests.capice_resources.testing_utilities import get_testing_resources_dir, \
    check_and_remove_directory
from molgenis.capice_resources.compare_model_performance import CMPPlottingEnums as Penums
from molgenis.capice_resources.compare_model_performance import CompareModelPerformanceEnums as \
    Menums
from molgenis.capice_resources.compare_model_performance.__main__ import CompareModelPerformance


class TestCompareModelPerformance(unittest.TestCase):
    output_directory = os.path.join(get_testing_resources_dir(), 'compare_model_performance')

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
        for figure in [
            Penums.FIG_AF.value,
            Penums.FIG_ROC.value,
            Penums.FIG_AUC.value,
            Penums.FIG_B_DIFF.value,
            Penums.FIG_V_DIFF.value,
            Penums.FIG_B_DIST.value,
            Penums.FIG_V_DIST.value
        ]:
            self.assertIn(figure + '.png', os.listdir(self.output_directory))

    def test_attempt_mismatch_merge_fail(self):
        """
        Test to see if the "_merge_scores_and_labels" function raises the SampleMismatchError as
        a result of unequal sample sizes and force_merge being set to False (by default).

        Since it doesn't matter what is inside the dataframes, supplying empty frames.
        (as the error is raised before anything is done with the frame)
        """
        module = CompareModelPerformance()
        with self.assertRaises(SampleMismatchError) as e:
            module._merge_scores_and_labes(
                pd.DataFrame({'foo': ['bar', 'baz']}),
                pd.DataFrame({'bar': ['foo']}),
                force_merge=False
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
        scores = pd.DataFrame(
            {
                 Menums.CHR.value: [1, 2, 3, 4],
                 VCFEnums.POS.value.lower(): [100, 200, 300, 400],
                 VCFEnums.REF.value.lower(): ['A', 'C', 'T', 'G'],
                 VCFEnums.ALT.value.lower(): ['T', 'G', 'A', 'C'],
                 Menums.GENE_NAME.value: ['foo', 'foo', 'bar', 'baz']
            }
        )
        labels = pd.DataFrame(
            {
                ColumnEnums.CHROM.value: [1, 2, 3],
                VCFEnums.POS.value: [100, 200, 300],
                VCFEnums.REF.value: ['A', 'C', 'T'],
                VCFEnums.ALT.value: ['T', 'G', 'A'],
                ColumnEnums.SYMBOL.value: ['foo', 'foo', 'bar'],
                'SuperUniqueLabelColumn': [1, 0, 0]
            }
        )
        observed = module._merge_scores_and_labes(scores, labels, force_merge=True)
        self.assertIn(ColumnEnums.CHROM.value, observed.columns)
        self.assertIn('SuperUniqueLabelColumn', observed.columns)


if __name__ == '__main__':
    unittest.main()
