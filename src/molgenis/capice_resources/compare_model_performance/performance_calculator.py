import numpy as np
import pandas as pd
from numpy import ndarray
from sklearn.metrics import roc_curve, roc_auc_score

from molgenis.capice_resources.core import ColumnEnums


class PerformanceCalculator:
    def __init__(self, ignore_zero_sample_error: bool = False):
        """
        Args:
            ignore_zero_sample_error:
                Boolean value to ignore the "ValueError: Found array with 0 sample(s) while minimum
                of 1 is required" (True to ignore) in case of a singular model comparison.
        """
        self.ignore_zero_sample_error = ignore_zero_sample_error

    def calculate_auc(self, dataset: pd.DataFrame) -> float:
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
                Will be NaN if ignore_zero_sample_error is set to True in initialization.
        """
        if self.ignore_zero_sample_error:
            try:
                return self._calculate_auc(dataset)
            except ValueError as e:
                if str(e) != "Found array with 0 sample(s) (shape=(0,)) " \
                             "while a minimum of 1 is required.":
                    raise
                else:
                    return np.nan
        else:
            return self._calculate_auc(dataset)

    @staticmethod
    def _calculate_auc(dataset: pd.DataFrame) -> float:
        return round(
                roc_auc_score(
                    y_true=dataset[ColumnEnums.BINARIZED_LABEL.value],
                    y_score=dataset[ColumnEnums.SCORE.value]
                ),
                4
            )

    def calculate_roc(
            self,
            dataset: pd.DataFrame
    ) -> tuple[ndarray, ndarray, float]:
        """
        Method to calculate the False Positive Rate (FPR), True Positive Rate (TPR) and Area
        Under Curve (AUC) for a given dataframe containing the SCORE and Binarized_label columns.

        Args:
            dataset:
                frame containing the SCORE and Binarized_label columns over which the FPR,
                TPR and AUC should be calculated.
        Returns:
            tuple:
                Tuple containing [0] False Positive Rate (numpy.array) [1] True Positive Rate (
                np.array) and [2] Area Under Curve (float, rounded to 4 decimals).
        """
        if self.ignore_zero_sample_error:
            message = "y_true takes value in {} and pos_label is not specified: " \
                      "either make y_true take value in {0, 1} or {-1, 1} or " \
                      "pass pos_label explicitly."
            try:
                fpr, tpr = self._calculate_fpr_tpr(dataset)
                return fpr, tpr, np.nan
            except ValueError as e:
                if str(e) != message:
                    raise
                else:
                    return np.nan, np.nan, np.nan
        else:
            fpr, tpr = self._calculate_fpr_tpr(dataset)
            return fpr, tpr, self._calculate_auc(dataset)

    @staticmethod
    def _calculate_fpr_tpr(
            dataset: pd.DataFrame
    ) -> tuple[np.ndarray, np.ndarray]:
        return roc_curve(
            y_true=dataset[ColumnEnums.BINARIZED_LABEL.value],
            y_score=dataset[ColumnEnums.SCORE.value]
        )[0:2]
