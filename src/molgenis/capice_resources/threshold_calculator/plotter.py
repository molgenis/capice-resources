import pandas as pd
from matplotlib import pyplot as plt

from molgenis.capice_resources.core import GlobalEnums
from molgenis.capice_resources.threshold_calculator import ThresholdEnums


class ThresholdPlotter:
    def __init__(self, recall_data: pd.DataFrame):
        self.best_threshold = recall_data.loc[0, ThresholdEnums.THRESHOLD.value]
        self.recall = recall_data.loc[0, ThresholdEnums.RECALL.value]
        self.precision = recall_data.loc[0, ThresholdEnums.F1.value]
        self.f1 = recall_data.loc[0, ThresholdEnums.RECALL.value]
        self.figure = plt.figure()
        self.figure.set_constrained_layout(GlobalEnums.CONSTRAINED_LAYOUT.value)

    def plot_threshold(self, validation_score_data: pd.DataFrame):
        ax_plot = self.figure.add_subplot(1, 1, 1)
        subset_benign = validation_score_data[
            validation_score_data[GlobalEnums.BINARIZED_LABEL.value] == 0
            ]
        subset_pathogenic = validation_score_data[
            validation_score_data[GlobalEnums.BINARIZED_LABEL.value] == 1
            ]
        ax_plot.scatter(
            subset_benign.index,
            subset_benign[GlobalEnums.SCORE.value],
            s=0.5,
            color='green',
            label=f'N benign: {subset_benign.shape[0]}'
        )
        ax_plot.scatter(
            subset_pathogenic.index,
            subset_pathogenic[GlobalEnums.SCORE.value],
            s=0.5,
            color='red',
            label=f'N pathogenic: {subset_pathogenic.shape[0]}'
        )
        xmin, xmax = ax_plot.get_xlim()
        ax_plot.hlines(
            self.best_threshold,
            xmin,
            xmax,
            color='black',
            label=f'Threshold: {round(self.best_threshold, 4)}\n'
                  f'Recall: {round(self.recall, 4)}\n'
                  f'Precision: {round(self.precision, 4)}\n'
                  f'F1: {round(self.f1, 4)}'
        )
        ax_plot.set_xticks([])
        ax_plot.set_xlabel('Variants')
        ax_plot.set_ylabel('CAPICE score')
        ax_plot.set_title('Optimal recall threshold')
        ax_plot.legend(
            loc='upper left',
            bbox_to_anchor=(1.0, 1.02),
            labelspacing=1.2
        )
        ax_plot.set_xlim(xmin, xmax)
        ax_plot.set_ylim(0, 1)
        return self.figure