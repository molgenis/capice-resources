import pandas as pd


class Ranker:
    @staticmethod
    def add_rank(dataframe: pd.DataFrame, column_names: list[str]) -> None:
        """
        Function to add a rank column to dataframe.
        Ranked according to the first "_normalized" that occurs within column_names.

        Args:
            dataframe:
                The pandas Dataframe over which a rank column should be added to.
                Please note that ranking is performed inplace.
            column_names:
                List of all the column names that have been added after performing normalization.

        """
        column_name = ''
        for column in column_names:
            if column.endswith('_normalized'):
                column_name = column
            else:
                raise KeyError('No normalized column found to rank on!')
        column_index = dataframe.columns.get_loc(column_name)
        ranks = dataframe[column_name].rank(method='min', ascending=False).astype(int)
        dataframe.insert(column_index + 1, column_name + '_rank', ranks)
