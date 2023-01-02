import numpy as np
import pandas as pd
from sklearn.metrics import recall_score, precision_score, f1_score

from molgenis.capice_resources.core import GlobalEnums as Genums
from molgenis.capice_resources.threshold_calculator import ThresholdEnums as Menums


class Calculator:
    def calculate_threshold(self, dataset: pd.DataFrame) -> pd.DataFrame:
        """
        Method to calculate the statistics for each threshold, sort the best threshold between
        0.94 and 0.96 recall and return the statistics dataframe.

        Please note that the return dataframe is sorted by threshold between recall 0.94 and
        0.96, then sorted by remainder recall scores.

        Args:
            dataset:
                Merged dataset between score and validation.

        Returns:
            dataframe:
                Score dataframe containing the Recall, Precision and F1 score for each of the
                attempted threshold. Please note that the return dataframe is sorted
                by threshold between recall 0.94 and 0.96, then sorted by remainder recall scores.
        """
        threshold_store = []
        recall_store = []
        precision_store = []
        f1_store = []
        self._reset_threshold(dataset)

        for i in np.arange(0, 1, 0.01):
            i = round(i, 2)
            dataset.loc[
                dataset[Genums.SCORE.value] >= i,
                Menums.CALCULATED_THRESHOLD.value
            ] = 1
            recall = recall_score(
                y_true=dataset[Genums.BINARIZED_LABEL.value],
                y_pred=dataset[Menums.CALCULATED_THRESHOLD.value]
            )
            precision = precision_score(
                y_true=dataset[Genums.BINARIZED_LABEL.value],
                y_pred=dataset[Menums.CALCULATED_THRESHOLD.value]
            )
            f1 = f1_score(
                y_true=dataset[Genums.BINARIZED_LABEL.value],
                y_pred=dataset[Menums.CALCULATED_THRESHOLD.value]
            )
            threshold_store.append(i)
            recall_store.append(recall)
            precision_store.append(precision)
            f1_store.append(f1)
            self._reset_threshold(dataset)
        out = pd.DataFrame(
            {
                Menums.THRESHOLD.value: threshold_store,
                Menums.RECALL.value: recall_store,
                Menums.PRECISION.value: precision_store,
                Menums.F1.value: f1_store
            }
        )
        self._sort_thresholds(out)
        return out.reset_index(drop=True)

    @staticmethod
    def _sort_thresholds(dataset: pd.DataFrame) -> None:
        """
        Object Orientated function to perform the somewhat complicated sorting of the statistics
        output dataframe.

        First sorts thresholds by recall score between 0.94 and 0.96, as per CAPICE publication.
        Then sorts the rest of the thresholds by the remainder recall scores.

        Args:
            dataset:
                The statistics dataset, fully looped through all possible thresholds.
                Please note that sorting is performed inplace.

        """
        dataset[Menums.INRANGE.value] = 0
        dataset.loc[
            (dataset[Menums.RECALL.value] >= 0.94) &
            (dataset[Menums.RECALL.value] <= 0.96),
            Menums.INRANGE.value
        ] = 1
        dataset.sort_values(
            by=[
                Menums.INRANGE.value,
                Menums.RECALL.value
            ], ascending=False, inplace=True)
        dataset.drop(columns=[Menums.INRANGE.value], inplace=True)

    @staticmethod
    def _reset_threshold(dataset: pd.DataFrame) -> None:
        """
        Reset function for the threshold to reset all "calculated threshold" values to 0.

        Args:
            dataset:
                The input dataset over which thresholds should be calculated.
                Please note that this method is performed inplace.

        """
        dataset[Menums.CALCULATED_THRESHOLD.value] = 0
