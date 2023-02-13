import pandas as pd

from molgenis.capice_resources.core import ColumnEnums
from molgenis.capice_resources.compare_model_performance import CompareModelPerformanceEnums


class Annotator:
    @staticmethod
    def add_score_difference(merged_model_frame: pd.DataFrame) -> None:
        """
        Function to add the "score_difference" column.

        Args:
            merged_model_frame:
                Merged frame between score and label over which the absolute score difference
                between the CAPICE score and the binarized_label should be calculated.
                Is performed inplace.

        """
        merged_model_frame[CompareModelPerformanceEnums.SCORE_DIFF.value] = abs(
            merged_model_frame[
                ColumnEnums.SCORE.value
            ] - merged_model_frame[
                ColumnEnums.BINARIZED_LABEL.value
            ]
        )

    @staticmethod
    def add_and_process_impute_af(merged_model_frame: pd.DataFrame) -> None:
        """
        Function to add a marker if the Allele Frequency has been imputed or not and impute the
        Allele Frequency where missing.

        Args:
            merged_model_frame:
                Merged frame between score and label over which the Allele Frequency should be
                imputed. Marks samples that have been imputed. Is performed inplace.

        """
        merged_model_frame[ColumnEnums.IMPUTED.value] = False
        merged_model_frame.loc[
            merged_model_frame[ColumnEnums.GNOMAD_AF.value].isnull(),
            ColumnEnums.IMPUTED.value
        ] = True
        merged_model_frame.loc[
            merged_model_frame[
                (merged_model_frame[ColumnEnums.IMPUTED.value]) &
                (merged_model_frame[ColumnEnums.GNOMAD_AF.value].isnull())
                ].index,
            ColumnEnums.GNOMAD_AF.value
        ] = 0
