import pandas as pd

from molgenis.capice_resources.train_data_creator import TrainDataCreatorEnums


class DuplicateProcessor:
    @staticmethod
    def process(merged_frame: pd.DataFrame):
        """
        Processor to drop full duplicates according to the Enums.further_processing_columns()

        Args:
            merged_frame:
                Merged dataframe between VKGL and CLinVar.
                Performed inplace.

        """
        print('Dropping duplicates.')
        merged_frame.drop_duplicates(
            subset=TrainDataCreatorEnums.further_processing_columns(),
            inplace=True
        )
