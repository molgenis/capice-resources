import pandas as pd


class DataValidator:
    @staticmethod
    def validate_capice_data(data: pd.DataFrame):
        required_columns = ['score', 'binarized_label', 'Consequence']
        for column in required_columns:
            if column not in data.columns:
                raise KeyError(f'Required column {column} not found in dataset.')
