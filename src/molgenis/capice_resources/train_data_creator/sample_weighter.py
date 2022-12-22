import pandas as pd

from molgenis.capice_resources.core import GlobalEnums
from molgenis.capice_resources.train_data_creator import TrainDataCreatorEnums


class SampleWeighter:
    @staticmethod
    def apply_sample_weight(merged_frame: pd.DataFrame):
        sample_weights = {
            4: 1.0,
            3: 1.0,
            2: 0.9,
            1: 0.8
        }
        merged_frame[GlobalEnums.SAMPLE_WEIGHT.value] = merged_frame[
            TrainDataCreatorEnums.REVIEW.value].map(sample_weights)
