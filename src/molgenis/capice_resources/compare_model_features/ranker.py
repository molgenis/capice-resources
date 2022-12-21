import pandas as pd


class Ranker:
    @staticmethod
    def add_rank(dataframe: pd.DataFrame, column_names: list[str]) -> None:
        column_name = None
        for column in column_names:
            if column.endswith('_normalized'):
                column_name = column
            else:
                raise KeyError('No normalized column found to rank on!')
        column_index = dataframe.columns.get_loc(column_name)
        ranks = dataframe[column_name].rank(method='min', ascending=False).astype(int)
        dataframe.insert(column_index + 1, column_name + '_rank', ranks)
