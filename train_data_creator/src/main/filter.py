import pandas as pd


class SVFilter:
    @staticmethod
    def filter(dataset: pd.DataFrame):
        dataset.drop(
            index=dataset[
                (dataset['REF'].str.len() > 50) | (dataset['ALT'].str.len() > 50)
                ].index, inplace=True
        )
