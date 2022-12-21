import pandas as pd

from molgenis.capice_resources.compare_model_features import CompareModelFeaturesEnum


class Orderer:
    @staticmethod
    def order(merged_dataframe: pd.DataFrame) -> pd.DataFrame:
        start_column = CompareModelFeaturesEnum.FEATURE.value
        col_names = merged_dataframe.columns
        front_columns = []
        other_columns = []
        for column in col_names:
            if column == start_column:
                continue
            elif "rank" in column:
                front_columns.append(column)
            else:
                other_columns.append(column)
        front_columns.sort()
        return merged_dataframe.loc[:, [start_column, *front_columns, *other_columns]]
