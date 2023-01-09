import os
import unittest
from unittest.mock import patch

import pandas as pd
from matplotlib import pyplot as plt

from molgenis.capice_resources.core import GlobalEnums as Genums
from molgenis.capice_resources.core.errors import SampleMismatchError
from tests.capice_resources.testing_utilities import get_testing_resources_dir, \
    check_and_remove_directory
from molgenis.capice_resources.compare_model_performance import PlottingEnums as Penums
from molgenis.capice_resources.compare_model_performance import CompareModelPerformanceEnums as \
    Menums
from molgenis.capice_resources.compare_model_performance.__main__ import CompareModelPerformance


class TestComponentCompareModelPerformance(unittest.TestCase):
    output_directory = os.path.join(get_testing_resources_dir(), 'compare_model_performance')

    @classmethod
    def tearDownClass(cls) -> None:
        for file in os.listdir(cls.output_directory):
            check_and_remove_directory(os.path.join(cls.output_directory, file))

    def tearDown(self) -> None:
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
        module = CompareModelPerformance()
        scores = pd.DataFrame(
            {
                 Menums.CHR.value: [1, 2, 3, 4],
                 Genums.POS.value.lower(): [100, 200, 300, 400],
                 Genums.REF.value.lower(): ['A', 'C', 'T', 'G'],
                 Genums.ALT.value.lower(): ['T', 'G', 'A', 'C'],
                 Menums.GENE_NAME.value: ['foo', 'foo', 'bar', 'baz']
            }
        )
        labels = pd.DataFrame(
            {
                Genums.CHROM.value: [1, 2, 3],
                Genums.POS.value: [100, 200, 300],
                Genums.REF.value: ['A', 'C', 'T'],
                Genums.ALT.value: ['T', 'G', 'A'],
                Genums.SYMBOL.value: ['foo', 'foo', 'bar'],
                'SuperUniqueLabelColumn': [1, 0, 0]
            }
        )
        observed = module._merge_scores_and_labes(scores, labels, force_merge=True)
        self.assertIn(Genums.CHROM.value, observed.columns)
        self.assertIn('SuperUniqueLabelColumn', observed.columns)


if __name__ == '__main__':
    unittest.main()
