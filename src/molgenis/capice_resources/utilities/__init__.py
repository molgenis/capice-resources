import numpy as np
import pandas as pd


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


def extract_key_value_dict_cli(cli_dict: dict[str, str | None]) -> tuple[str, str | None]:
    """
    Function to extract the CLI argument key and its value from an CLI dictionary

    Args:
        cli_dict:
            The dictionary containing the (key) argument key and (value) its command line value.

    Returns:
        tuple:
            Tuple containing [0] the argument key (str) and [1] its value (str or None).
    """
    # Done with list(path.keys())[0] so that the path_key is stored as string instead of
    # dict_keys()
    key = list(cli_dict.keys())[0]
    # Check for None in case we meet an optional argument
    if cli_dict[key] is not None:
        value = str(cli_dict[key])
    else:
        value = None
    return key, value

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
