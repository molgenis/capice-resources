import pandas as pd
from sklearn.metrics import roc_curve, roc_auc_score

from molgenis.capice_resources.core import GlobalEnums
from molgenis.capice_resources.compare_model_performance import CMPMinimalFeats


class PerformanceCalculator:
    @staticmethod
    def calculate_auc(dataset: pd.DataFrame):
        return round(
            roc_auc_score(
                y_true=dataset[GlobalEnums.BINARIZED_LABEL.value],
                y_score=dataset[CMPMinimalFeats.SCORE.value]
            ),
            4
        )

    def calculate_roc(self, dataset: pd.DataFrame):
        fpr, tpr, _ = roc_curve(
            y_true=dataset[GlobalEnums.BINARIZED_LABEL.value],
            y_score=dataset[CMPMinimalFeats.SCORE.value]
        )
        return fpr, tpr, self.calculate_auc(dataset)
