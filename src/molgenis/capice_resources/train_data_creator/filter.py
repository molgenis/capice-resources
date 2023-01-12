import pandas as pd

from molgenis.capice_resources.core import GlobalEnums


class SVFilter:
    @staticmethod
    def filter(merged_frame: pd.DataFrame):
        """
        Filters out structural variants if present in either REF or ALT.

        Args:
            merged_frame:
                Merged dataframe between VKGL and CLinVar.
                Performed inplace.

        """
        merged_frame.drop(
            index=merged_frame[
                (merged_frame[GlobalEnums.REF.value].str.len() > 50) |
                (merged_frame[GlobalEnums.ALT.value].str.len() > 50)
                ].index, inplace=True
        )
