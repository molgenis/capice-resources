import pandas as pd

from molgenis.capice_resources.compare_model_features import CompareModelFeaturesEnums


class Normalizer:
    @staticmethod
    def normalize_column(dataframe: pd.DataFrame, column_name: str) -> None:
        """
        Function to perform Z-score normalization over column_name.

        Args:
            dataframe:
                pandas Dataframe over which the normalization should be performed.
                Please note that normalization is performed inplace.
            column_name:
                The column that should be used to perform the normalization on.

        """
        column_index = dataframe.columns.get_loc(column_name)
        normalized_values = (dataframe[column_name] - dataframe[column_name].mean()) / dataframe[
            column_name].std()
        dataframe.insert(
            column_index + 1,
            column_name + CompareModelFeaturesEnums.NORMALIZED.value,
            normalized_values
        )
