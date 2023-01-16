import warnings

import pandas as pd

from molgenis.capice_resources.utilities import split_consequences
from molgenis.capice_resources.core import GlobalEnums as Genums


class ConsequenceTools:
    def has_consequence(
            self,
            merged_model_1: pd.DataFrame,
            merged_model_2: pd.DataFrame
    ) -> bool | list[str]:
        """
        Method to extract if one of 2 merged_model frames has the Consequence column or not.
        Args:
            merged_model_1:
                Merged frame of score and label files of model 1.
            merged_model_2:
                Merged frame of score and label files of model 2.
        Returns:
            out:
                False if Consequence is not present in the merge of model 1 or model 2.
                Else will return a list of all unique and split consequences present in
                either model 1 merge frame or model 2 merge frame.
        """
        if (
                Genums.CONSEQUENCE.value not in merged_model_1.columns or
                Genums.CONSEQUENCE.value not in merged_model_2.columns
        ):
            warnings.warn(
                'Missing consequence column. Disabling per-consequence performance metrics.'
            )
            return False
        else:
            if Genums.CONSEQUENCE.value in merged_model_1:
                return split_consequences(merged_model_1[Genums.CONSEQUENCE.value].values)
            else:
                return split_consequences(merged_model_2[Genums.CONSEQUENCE.value].values)

    @staticmethod
    def subset_consequence(dataframe: pd.DataFrame, consequence: str) -> pd.DataFrame:
        """
        Method to subset dataframe on the presence of consequence.

        Args:
            dataframe:
                The dataframe containing the Consequence column that a subset should be obtained
                from. Please note that consequence should not exactly match, just that a sample
                should contain consequence.
            consequence:
                The consequence that should lead the sub setting.
        Returns:
            dataframe:
                The sub setted input dataframe in which all samples contain the consequence
                "consequence".
        """
        return dataframe[dataframe[Genums.CONSEQUENCE.value].str.contains(consequence)]

    @staticmethod
    def validate_consequence_samples_equal(
            merged_model_1: pd.DataFrame,
            merged_model_2: pd.DataFrame,
            splitted_consequences: list[str]
    ) -> None:
        """
        Validator to see if per consequence the sample sizes of model 1 and model 2 match.

        Args:
            merged_model_1:
                Merged frame of score and label files of model 1.
            merged_model_2:
                Merged frame of score and label files of model 2.
            splitted_consequences:
                List containing all unique and split consequences present in either
                merged_model_1 or merged_model_2.

        """
        nonequal = []
        for consequence in splitted_consequences:
            m1 = merged_model_1[
                merged_model_1[Genums.CONSEQUENCE.value].str.contains(consequence)
            ]
            m2 = merged_model_2[
                merged_model_2[Genums.CONSEQUENCE.value].str.contains(consequence)
            ]
            if m1.shape[0] != m2.shape[0] and consequence not in nonequal:
                nonequal.append(consequence)
        if len(nonequal) > 0:
            warnings.warn(
                f'Model files differ in sample size for consequence(s): '
                f'{", ".join(nonequal)}'
            )
