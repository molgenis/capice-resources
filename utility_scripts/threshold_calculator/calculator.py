import numpy as np
import pandas as pd
from enums import ValidationColumns, ScoreColumns
from sklearn.metrics import recall_score, precision_score, f1_score


class ThresholdCalculator:
    def calculate_threshold(self, dataset):
        threshold_store = []
        recall_store = []
        precision_store = []
        f1_store = []
        self._reset_threshold(dataset)

        for i in np.arange(0, 1, 0.01):
            i = round(i, 2)
            dataset.loc[dataset[ScoreColumns.SCORE.value] >= i, 'calculated_threshold'] = 1
            recall = recall_score(
                y_true=dataset[ValidationColumns.BINARIZED_LABEL.value],
                y_pred=dataset['calculated_threshold']
            )
            precision = precision_score(
                y_true=dataset[ValidationColumns.BINARIZED_LABEL.value],
                y_pred=dataset['calculated_threshold']
            )
            f1 = f1_score(
                y_true=dataset[ValidationColumns.BINARIZED_LABEL.value],
                y_pred=dataset['calculated_threshold']
            )
            threshold_store.append(i)
            recall_store.append(recall)
            precision_store.append(precision)
            f1_store.append(f1)
            self._reset_threshold(dataset)
        out = pd.DataFrame(
            {
                'Threshold': threshold_store,
                'Recall_score': recall_store,
                'Precision_score': precision_store,
                'F1_score': f1_store
            }
        )
        self._sort_thresholds(out)
        return out.reset_index(drop=True)

    @staticmethod
    def _sort_thresholds(dataset):
        dataset['in_range'] = 0
        dataset.loc[
            (dataset['Recall_score'] >= 0.94) & (dataset['Recall_score'] <= 0.96),
            'in_range'
        ] = 1
        dataset.sort_values(by=['in_range', 'Recall_score'], ascending=False, inplace=True)
        dataset.drop(columns=['in_range'], inplace=True)

    @staticmethod
    def _reset_threshold(dataset):
        dataset['calculated_threshold'] = 0
