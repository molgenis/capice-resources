import unittest

import pandas as pd
from matplotlib import pyplot as plt

from molgenis.capice_resources.compare_model_performance.plotter import Plotter


class TestPlotter(unittest.TestCase):
    def tearDown(self) -> None:
        """
        plt.close('all') is required, as matplotlib keeps all figures loaded. With the amount of
        matplotlib related tests in capice-resources, matplotlib does throw an warning that too
        many figures are loaded unless this call is made.
        """
        plt.close('all')

    def test_plotter_init_consequences_supplied(self):
        """
        Test to see if the __init__ of the Plotter class correctly sets the amount of rows,
        columns, figure size and supertitles if supplied with a list of consequences.
        """
        consequences = [
                    'frameshift_variant',
                    'intron_variant',
                    'synonymous_variant'
                ]
        plotter = Plotter(
            consequences,
            'path_model_1_scores',
            'path_model_1_labels',
            'path_model_2_scores',
            'path_model_2_labels'
        )
        self.assertEqual(2, plotter.n_rows)
        self.assertEqual(3, plotter.n_cols)
        self.assertTupleEqual((20, 40), plotter._set_figure_size(consequences))
        self.assertEqual(100, plotter.fig_auc.dpi)
        figure_size = list(plotter.fig_auc.get_size_inches()*plotter.fig_auc.dpi)
        self.assertEqual(2000.0, figure_size[0])
        self.assertEqual(4000.0, figure_size[1])
        self.assertEqual(1, plotter.index)
        self.assertEqual(
            plotter.fig_auc._suptitle.get_text(),
            "Model 1 vs Model 2 Area Under Receiver Operator Curve\n"
            "Model 1 scores: path_model_1_scores\n"
            "Model 1 labels: path_model_1_labels\n"
            "Model 2 scores: path_model_2_scores\n"
            "Model 2 labels: path_model_2_labels\n"
        )

    def test_plotter_init_consequences_not_supplied(self):
        """
        Test to see if the __init__ of the Plotter class correctly sets the amount of rows,
        columns, figure size and supertitles if supplied with "False", meaning per-Consequence
        plotting should not be possible.
        """
        plotter = Plotter(
            False,
            'path_model_1_scores',
            'path_model_1_labels',
            'path_model_2_scores',
            'path_model_2_labels'
        )
        self.assertEqual(1, plotter.n_rows)
        self.assertEqual(1, plotter.n_cols)
        self.assertTupleEqual((10, 15), plotter._set_figure_size(False))
        figure_size = list(plotter.fig_auc.get_size_inches()*plotter.fig_auc.dpi)
        self.assertEqual(1000.0, figure_size[0])
        self.assertEqual(1500.0, figure_size[1])
        self.assertEqual(1, plotter.index)
        self.assertEqual(
            plotter.fig_auc._suptitle.get_text(),
            "Model 1 vs Model 2 Area Under Receiver Operator Curve\n"
            "Model 1 scores: path_model_1_scores\n"
            "Model 1 labels: path_model_1_labels\n"
            "Model 2 scores: path_model_2_scores\n"
            "Model 2 labels: path_model_2_labels\n"
        )

    def test_consequence_not_present_for_one_of_two_models(self):
        """
        Test that ensures proper function of the violinplots when supplied with a dataframe
        consisting of a singular consequence that is present for 1 model, but not the other.
        """
        test_case_model1 = pd.DataFrame(
            {
                "binarized_label": [1, 0, 1],
                "score": [0.1, 0.1, 0.6],
                "gnomAD_AF": [0.01, 0.02, 0.03],
                "Consequence": ['Foo', 'Foo', 'Foo'],
                "is_imputed": [True, True, False],
                "dataset_source": ['model_1', 'model_1', 'model_1']
            }
        )
        test_case_model1['score_diff'] = abs(
            test_case_model1['score'] - test_case_model1['binarized_label']
        )
        test_case_model2 = pd.DataFrame(
            {
                "binarized_label": [0, 1],
                "score": [0.8, 0.9],
                "gnomAD_AF": [0.04, 0.05],
                "Consequence": ['Bar', 'Bar'],
                "is_imputed": [False, False],
                "dataset_source": ['model_2', 'model_2']
            }
        )
        test_case_model2['score_diff'] = abs(
            test_case_model2['score'] - test_case_model2['binarized_label']
        )
        plotter = Plotter(
            ['Foo', 'Bar'],
            'path1',
            'path2',
            'path3',
            'path4'
        )
        plotter.plot(test_case_model1, test_case_model2)


if __name__ == '__main__':
    unittest.main()
