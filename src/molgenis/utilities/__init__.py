import pandas as pd


def merge_dataset_rows(*args: pd.DataFrame):
    return pd.concat([*args], axis=1, ignore_index=True)
