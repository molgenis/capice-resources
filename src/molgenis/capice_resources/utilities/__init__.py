import numpy as np
import pandas as pd

from molgenis.capice_resources.core import ColumnEnums


def add_dataset_source(frame: pd.DataFrame, name: str) -> None:
    """
    Function to add a dataset source to a dataset.

    Args:
        frame:
            The dataframe to which apply the dataset source to.
        name:
            The name of the dataset source that needs to be applied.

    """
    frame[ColumnEnums.DATASET_SOURCE.value] = name


def merge_dataset_rows(*args: pd.DataFrame, ignore_index: bool = True) -> pd.DataFrame:
    """
    Function to merge one or more pandas Dataframe rows.
    Merges on axis 0 (which means all samples are merged, not columns).
    Please note that the index is ignored.

    Args:
        *args:
            All the pandas dataframes that need to be merged together.
        ignore_index:
            Boolean value if the Index should be reset to range(0, n) or not.

    Returns:
        pandas.DataFrame:
            Singular pandas dataframe that is merged on all rows.
    """
    return pd.concat([*args], axis=0, ignore_index=ignore_index)


def split_consequences(consequence_column: pd.Series | list[str] | np.ndarray) -> list[str]:
    """
    Function to obtain all unique consequences from the Consequences column, even if hidden
    within a singular sample.

    Args:
        consequence_column:
            The pandas series, list or numpy ndarray of the consequence column over which all
            unique consequences should be obtained.
    Returns:
        list:
            List of all unique consequences from consequence_column. Even the ones hidden
            inside a singular sample.
    """
    if not isinstance(consequence_column, pd.Series):
        consequence_column = pd.Series(consequence_column)
    splitted_consequences = consequence_column.str.split('&', expand=True)
    return list(
        pd.Series(
            splitted_consequences.values.ravel()
        ).dropna().sort_values(ignore_index=True).unique()
    )
