import pandas as pd

from molgenis.capice_resources.compare_model_features import CompareModelFeaturesEnums


class Orderer:
    @staticmethod
    def order(merged_dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Function to order the column names to ["feature", "feat_rank_model1", "feat_rank_model2"].
        Args:
            merged_dataframe:
                The merged pandas dataframe between model 1 and model 2 that has been normalized
                and ranked. Please note that ordering is performed inplace.

        """
        start_column = CompareModelFeaturesEnums.FEATURE.value
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
