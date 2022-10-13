import numpy as np
import pandas as pd
from sklearn.metrics import recall_score


class ThresholdCalculator:
    def __init__(self, labels, scores):
        self.data = self._combine_datasets(labels, scores)

    @staticmethod
    def _combine_datasets(dataset1, dataset2):
        return pd.concat([dataset1, dataset2], axis=1)

    def calculate_threshold(self):
        threshold_store = []
        recall_store = []

        for i in np.arange(0, 1, 0.01):
            self.data.loc[self.data['score'] >= i, 'calculated_threshold'] = 1
            recall = recall_score(y_true=self.data['binarized_label'], y_pred=self.data['calculated_threshold'])
            threshold_store.append(i)
            recall_store.append(recall)
        return pd.DataFrame({'Threshold': threshold_store, 'Recall_score': recall_store}).sort_values(
            by='Recall_score', ascending=False
        ).reset_index(drop=True)

    def reset_threshold(self):
        self.data['calculated_threshold'] = 0
