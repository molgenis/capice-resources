import unittest

from molgenis.capice_resources.compare_model_performance.plotter import Plotter


class TestPlotter(unittest.TestCase):
    def test_plotter_init_consequences_supplied(self):
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
        self.assertEqual(1, plotter.n_rows)
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
