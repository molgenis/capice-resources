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
        self.reset_threshold()
        threshold_calculated = False
        for i in np.arange(0, 1, 0.01):
            self.data.loc[self.data['score'] >= i, 'calculated_threshold'] = 1
            recall = recall_score(y_true=self.data['binarized_label'], y_pred=self.data['calculated_threshold'])
            if 0.94 <= recall <= 0.96:
                threshold_calculated = True
                print(f'Threshold calculated, final threshold: {i}')
                print(f'At recall score: {recall}')
                break
            self.reset_threshold()
        if not threshold_calculated:
            raise ValueError("Unable to calculate threshold!")

    def reset_threshold(self):
        self.data['calculated_threshold'] = 0
