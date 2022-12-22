import os
from pathlib import Path

import pandas as pd


def merge_dataset_rows(*args: pd.DataFrame) -> pd.DataFrame:
    """
    Function to merge one or more pandas Dataframe rows.
    Merges on axis 0 (which means all samples are merged, not columns).
    Please note that the index is ignored.

    Args:
        *args:
            All the pandas dataframes that need to be merged together.
    Returns:
        pandas.DataFrame:
            Singular pandas dataframe that is merged on all rows.
    """
    return pd.concat([*args], axis=0, ignore_index=True)


def extract_key_value_dict_cli(cli_dict: dict[str, str | None]) -> tuple[str, str]:
    """
    Function to extract the CLI argument key and its value from an CLI dictionary

    Args:
        cli_dict:
            The dictionary containing the (key) argument key and (value) its command line value.

    Returns:
        tuple:
            Tuple containing [0] the argument key (str) and [1] its value (pathlib.Path).
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
