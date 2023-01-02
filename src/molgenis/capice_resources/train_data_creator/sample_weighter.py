import pandas as pd

from molgenis.capice_resources.core import GlobalEnums
from molgenis.capice_resources.train_data_creator import TrainDataCreatorEnums


class SampleWeighter:
    @staticmethod
    def apply_sample_weight(merged_frame: pd.DataFrame):
        """
        Processor to apply the sample weights according to the Review Status.

        See the sample_weights variable for the applied sample weights and the VKGL and ClinVar
        data parsers to see what review scores are applied.

        Args:
            merged_frame:
                Merged dataframe between ClinVar and VKGL.
                Performed inplace.

        """
        sample_weights = {
            4: 1.0,
            3: 1.0,
            2: 0.9,
            1: 0.8
        }
        merged_frame[GlobalEnums.SAMPLE_WEIGHT.value] = merged_frame[
            TrainDataCreatorEnums.REVIEW.value].map(sample_weights)
