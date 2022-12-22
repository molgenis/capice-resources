import numpy as np
import pandas as pd
from sklearn.metrics import recall_score, precision_score, f1_score

from molgenis.capice_resources.core import GlobalEnums
from molgenis.capice_resources.threshold_calculator import ThresholdEnums


class Calculator:
    def calculate_threshold(self, dataset):
        threshold_store = []
        recall_store = []
        precision_store = []
        f1_store = []
        self._reset_threshold(dataset)

        for i in np.arange(0, 1, 0.01):
            i = round(i, 2)
            dataset.loc[
                dataset[GlobalEnums.SCORE.value] >= i,
                ThresholdEnums.CALCULATED_THRESHOLD.value
            ] = 1
            recall = recall_score(
                y_true=dataset[GlobalEnums.BINARIZED_LABEL.value],
                y_pred=dataset[ThresholdEnums.CALCULATED_THRESHOLD.value]
            )
            precision = precision_score(
                y_true=dataset[GlobalEnums.BINARIZED_LABEL.value],
                y_pred=dataset[ThresholdEnums.CALCULATED_THRESHOLD.value]
            )
            f1 = f1_score(
                y_true=dataset[GlobalEnums.BINARIZED_LABEL.value],
                y_pred=dataset[ThresholdEnums.CALCULATED_THRESHOLD.value]
            )
            threshold_store.append(i)
            recall_store.append(recall)
            precision_store.append(precision)
            f1_store.append(f1)
            self._reset_threshold(dataset)
        out = pd.DataFrame(
            {
                ThresholdEnums.THRESHOLD.value: threshold_store,
                ThresholdEnums.RECALL.value: recall_store,
                ThresholdEnums.PRECISION.value: precision_store,
                ThresholdEnums.F1.value: f1_store
            }
        )
        self._sort_thresholds(out)
        return out.reset_index(drop=True)

    @staticmethod
    def _sort_thresholds(dataset):
        dataset[ThresholdEnums.INRANGE.value] = 0
        dataset.loc[
            (dataset[ThresholdEnums.RECALL.value] >= 0.94) &
            (dataset[ThresholdEnums.RECALL.value] <= 0.96),
            ThresholdEnums.INRANGE.value
        ] = 1
        dataset.sort_values(
            by=[
                ThresholdEnums.INRANGE.value,
                ThresholdEnums.RECALL.value
            ], ascending=False, inplace=True)
        dataset.drop(columns=[ThresholdEnums.INRANGE.value], inplace=True)

    @staticmethod
    def _reset_threshold(dataset):
        dataset[ThresholdEnums.CALCULATED_THRESHOLD.value] = 0
