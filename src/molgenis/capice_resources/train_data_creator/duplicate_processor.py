import pandas as pd

from molgenis.capice_resources.train_data_creator import TrainDataCreatorEnums


class DuplicateProcessor:
    @staticmethod
    def process(merged_frame: pd.DataFrame):
        print('Dropping duplicates.')
        merged_frame.drop_duplicates(
            subset=TrainDataCreatorEnums.further_processing_columns(), inplace=True
        )
