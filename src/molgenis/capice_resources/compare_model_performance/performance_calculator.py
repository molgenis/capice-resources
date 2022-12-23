import pandas as pd
from sklearn.metrics import roc_curve, roc_auc_score

from molgenis.capice_resources.core import GlobalEnums as Genums


class PerformanceCalculator:
    @staticmethod
    def calculate_auc(dataset: pd.DataFrame) -> float:
        """
        Method to calculate the Area Under Curve (AUC) for a given dataframe containing the SCORE
        and Binarized_label columns.

        Args:
            dataset:
                frame containing the SCORE and Binarized_label columns over which an AUC should
                be calculated.
        Returns:
            float:
                Rounded float of the Area Under Curve on 4 decimals.
        """
        return round(
            roc_auc_score(
                y_true=dataset[Genums.BINARIZED_LABEL.value],
                y_score=dataset[Genums.SCORE.value]
            ),
            4
        )

    def calculate_roc(self, dataset: pd.DataFrame) -> tuple[float, float, float]:
        """
        Method to calculate the False Positive Rate (FPR), True Positive Rate (TPR) and Area
        Under Curve (AUC) for a given dataframe containing the SCORE and Binarized_label columns.

        Args:
            dataset:
                frame containing the SCORE and Binarized_label columns over which the FPR,
                TPR and AUC should be calculated.
        Returns:
            tuple:
                Tuple containing [0] False Positive Rate (float) [1] True Positive Rate (float)
                and [2] Area Under Curve (float, rounded to 4 decimals).
        """
        fpr, tpr, _ = roc_curve(
            y_true=dataset[Genums.BINARIZED_LABEL.value],
            y_score=dataset[Genums.SCORE.value]
        )
        return fpr, tpr, self.calculate_auc(dataset)
