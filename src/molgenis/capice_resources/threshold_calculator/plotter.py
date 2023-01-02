import pandas as pd
from matplotlib import pyplot as plt

from molgenis.capice_resources.core import GlobalEnums as Genums
from molgenis.capice_resources.threshold_calculator import ThresholdEnums as Menums


class ThresholdPlotter:
    def __init__(self, recall_data: pd.DataFrame):
        """
        Main plotter function of ThresholdCalculator.

        Initializes the best scores according to the first threshold (from 0 to 1) that hits a
        recall between 0.94 and 0.96.

        Args:
            recall_data:
                Full output dataframe from the ThresholdCalculator, containing all the recall,
                F1 and precision scores.
        """
        self.best_threshold = recall_data.loc[0, Menums.THRESHOLD.value]
        self.recall = recall_data.loc[0, Menums.RECALL.value]
        self.precision = recall_data.loc[0, Menums.F1.value]
        self.f1 = recall_data.loc[0, Menums.RECALL.value]
        self.figure = plt.figure()
        self.figure.set_constrained_layout(Genums.CONSTRAINED_LAYOUT.value)

    def plot_threshold(self, validation_score_data: pd.DataFrame) -> plt.Figure:
        """
        Plotting function of the plotting class.

        First plots the validation_score_data and then takes the xmin and xmax from that plot,
        and uses those to plot a horizontal line of the threshold, with in the legend the scores.

        Args:
            validation_score_data:
                Merged dataset between score and validation.

        Returns:
            figure:
                matplotlib.pyplot.Figure object of the plot containing the validation_score_data
                (scatter) and the optimal threshold (horizontal line).
        """
        ax_plot = self.figure.add_subplot(1, 1, 1)
        subset_benign = validation_score_data[
            validation_score_data[Genums.BINARIZED_LABEL.value] == 0
            ]
        subset_pathogenic = validation_score_data[
            validation_score_data[Genums.BINARIZED_LABEL.value] == 1
            ]
        ax_plot.scatter(
            subset_benign.index,
            subset_benign[Genums.SCORE.value],
            s=0.5,
            color='green',
            label=f'N benign: {subset_benign.shape[0]}'
        )
        ax_plot.scatter(
            subset_pathogenic.index,
            subset_pathogenic[Genums.SCORE.value],
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
