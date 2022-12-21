import pandas as pd


class Normalizer:
    @staticmethod
    def normalize_column(dataframe: pd.DataFrame, column_name: str) -> None:
        column_index = dataframe.columns.get_loc(column_name)
        normalized_values = (dataframe[column_name] - dataframe[column_name].mean()) / dataframe[
            column_name].std()
        dataframe.insert(column_index + 1, column_name + '_normalized', normalized_values)
