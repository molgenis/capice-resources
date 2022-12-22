import warnings

import pandas as pd

from molgenis.capice_resources.compare_model_performance import CMPExtendedFeats


class ConsequenceTools:
    @staticmethod
    def has_consequence(
            merged_model_1: pd.DataFrame,
            merged_model_2: pd.DataFrame
    ) -> bool | list[str]:
        if (
                not CMPExtendedFeats.CONSEQUENCE.value in merged_model_1.columns
        ) or (
                not CMPExtendedFeats.CONSEQUENCE.value in merged_model_2.columns
        ):
            warnings.warn(
                'Missing consequence column. Disabling per-consequence performance metrics.'
            )
            return False
        else:
            if CMPExtendedFeats.CONSEQUENCE.value in merged_model_1:
                return list(merged_model_1[CMPExtendedFeats.CONSEQUENCE.value].values())
            else:
                return list(merged_model_2[CMPExtendedFeats.CONSEQUENCE.value].values())

    @staticmethod
    def split_consequences(consequence_column: pd.Series | list[str]) -> list[str]:
        if isinstance(consequence_column, list):
            consequence_column = pd.Series(consequence_column)
        splitted_consequences = consequence_column.str.split('&', expand=True)
        return list(
            pd.Series(
                splitted_consequences.values.ravel()
            ).dropna().sort_values(ignore_index=True).unique()
        )

    @staticmethod
    def subset_consequence(dataframe: pd.DataFrame, consequence: str) -> pd.DataFrame:
        return dataframe[dataframe[CMPExtendedFeats.CONSEQUENCE.value].str.contains(consequence)]

    @staticmethod
    def validate_consequence_samples_equal(
            merged_model_1: pd.DataFrame,
            merged_model_2: pd.DataFrame,
            splitted_consequences: list[str]
    ) -> None:
        nonequal = []
        for consequence in splitted_consequences:
            m1 = merged_model_1[
                merged_model_1[CMPExtendedFeats.CONSEQUENCE.value].str.contains(consequence)
            ]
            m2 = merged_model_2[
                merged_model_2[CMPExtendedFeats.CONSEQUENCE.value].str.contains(consequence)
            ]
            if m1.shape[0] != m2.shape[0]:
                nonequal.append(consequence)
            if len(nonequal) > 0:
                warnings.warn(
                    f'Model files differ in sample size for consequence(s): '
                    f'{", ".join(nonequal)}'
                )
