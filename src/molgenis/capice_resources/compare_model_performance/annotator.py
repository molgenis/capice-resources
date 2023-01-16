import pandas as pd

from molgenis.capice_resources.core import GlobalEnums as Genums
from molgenis.capice_resources.compare_model_performance import CompareModelPerformanceEnums as \
    Menums


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
        merged_model_frame[Menums.SCORE_DIFF.value] = abs(
            merged_model_frame[
                Genums.SCORE.value
            ] - merged_model_frame[
                Genums.BINARIZED_LABEL.value
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
        merged_model_frame[Menums.IMPUTED.value] = False
        merged_model_frame.loc[
            merged_model_frame[Genums.GNOMAD_AF.value].isnull(),
            Menums.IMPUTED.value
        ] = True
        merged_model_frame.loc[
            merged_model_frame[
                (merged_model_frame[Menums.IMPUTED.value]) &
                (merged_model_frame[Genums.GNOMAD_AF.value].isnull())
                ].index,
            Genums.GNOMAD_AF.value
        ] = 0

    @staticmethod
    def add_model_identifier(merged_model_frame: pd.DataFrame, model: str) -> None:
        """
        Function to add a model identifier to merged_model_frame.

        Args:
            merged_model_frame:
                Merged frame between score and label frames over which a column should be added
                that marks the origin of the merged frame with "model". Please note that this is
                performed inplace.
            model:
                The string that will fill the column that marks the origin.

        """
        merged_model_frame[Menums.MODEL_IDENTIFIER.value] = model
