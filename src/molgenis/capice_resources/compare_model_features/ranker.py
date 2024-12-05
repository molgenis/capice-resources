import numpy
import pandas as pd


class Ranker:
    @staticmethod
    def add_rank(dataframe: pd.DataFrame, column_name: str) -> None:
        """
        Function to add a rank column to dataframe.
        Ranked according to the first "_normalized" that occurs within column_names.

        Args:
            dataframe:
                The pandas Dataframe over which a rank column should be added to.
                Please note that ranking is performed inplace.
            column_name:
                Name of the column over which a rank should be obtained and added.

        """
        column_index = dataframe.columns.get_loc(column_name)
        ranks = dataframe[column_name].rank(method='min', ascending=False).astype(numpy.int64)
        dataframe.insert(column_index + 1, column_name + '_rank', ranks)
