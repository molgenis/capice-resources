import unittest

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


if __name__ == '__main__':
    unittest.main()
