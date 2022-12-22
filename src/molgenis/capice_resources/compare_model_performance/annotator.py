import pandas as pd

from molgenis.capice_resources.core import GlobalEnums
from molgenis.capice_resources.compare_model_performance import CMPExtendedFeats, CMPMinimalFeats


class Annotator:
    @staticmethod
    def add_score_difference(merged_model_frame: pd.DataFrame) -> None:
        merged_model_frame[CMPExtendedFeats.SCORE_DIFF.value] = abs(
            merged_model_frame[
                GlobalEnums.SCORE.value
            ] - merged_model_frame[
                GlobalEnums.BINARIZED_LABEL.value
            ]
        )

    @staticmethod
    def add_and_process_impute_af(merged_model_frame: pd.DataFrame) -> None:
        merged_model_frame[CMPExtendedFeats.IMPUTED.value] = False
        merged_model_frame.loc[
            merged_model_frame[CMPMinimalFeats.GNOMAD_AF.value].isnull(),
            CMPExtendedFeats.IMPUTED.value
        ] = True
        merged_model_frame.loc[
            CMPExtendedFeats.IMPUTED.value,
            CMPMinimalFeats.GNOMAD_AF.value
        ] = 0

    @staticmethod
    def add_model_identifier(merged_model_frame: pd.DataFrame, model: str) -> None:
        merged_model_frame[CMPExtendedFeats.MODEL_IDENTIFIER.value] = model
