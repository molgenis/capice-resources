import os
import pandas as pd
from matplotlib import pyplot as plt
from enums import ValidationColumns, ScoreColumns


class ThresholdPlotter:
    def __init__(self, recall_data: pd.DataFrame):
        self.best_threshold = recall_data.loc[0, 'Threshold']
        self.best_recall = recall_data.loc[0, 'Recall_score']
        self.figure = plt.figure()

    def plot_threshold(self, validation_score_data: pd.DataFrame):
        ax_plot = self.figure.add_subplot(1, 1, 1)
        subset_benign = validation_score_data[
            validation_score_data[
                ValidationColumns.BINARIZED_LABEL.value == 0
            ]
        ]
        subset_pathogenic = validation_score_data[
            validation_score_data[
                ValidationColumns.BINARIZED_LABEL.value == 1
            ]
        ]
        ax_plot.scatter(
            subset_benign.index,
            subset_benign[ScoreColumns.SCORE.value],
            color=''
        )
        ax_plot.plot()

    def export(self, output_path: str):
        self.figure.savefig(os.path.join(os.path.basename(output_path), 'thresholds.png'))
