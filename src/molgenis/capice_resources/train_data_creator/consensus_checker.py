import warnings

import pandas as pd

from molgenis.capice_resources.core import GlobalEnums
from molgenis.capice_resources.train_data_creator import TrainDataCreatorEnums


class ConsensusChecker:
    def check_consensus_clinvar_vkgl_match(self, merged_frame: pd.DataFrame) -> None:
        before_drop = merged_frame.shape[0]
        vkgl_subset = merged_frame[
            merged_frame[GlobalEnums.DATASET_SOURCE.value] == TrainDataCreatorEnums.VKGL.value
        ].copy(deep=True)
        clinvar_subset = merged_frame[
            merged_frame[GlobalEnums.DATASET_SOURCE.value] == TrainDataCreatorEnums.CLINVAR.value
        ].copy(deep=True)
        self._perform_check(merged_frame, vkgl_subset)
        self._perform_check(merged_frame, clinvar_subset)
        after_drop = merged_frame.shape[0]
        div = int((before_drop - after_drop) / 2)
        if div > 0:
            warnings.warn(
                f'Removed {div} variant(s) due to mismatch consensus'
            )

    @staticmethod
    def _perform_check(merged_frame, subset_frame):
        indices = merged_frame.merge(
            subset_frame,
            on=TrainDataCreatorEnums.further_processing_columns(),
            suffixes=('_og', '_del'),
            how='left'
        )
        og_column_source_name = GlobalEnums.DATASET_SOURCE.value + '_og'
        og_column_bl_name = GlobalEnums.BINARIZED_LABEL.value + '_og'
        del_column_source_name = GlobalEnums.DATASET_SOURCE.value + '_del'
        del_column_bl_name = GlobalEnums.BINARIZED_LABEL.value + '_del'
        merged_frame.drop(
            index=indices[
                (indices[og_column_source_name] != indices[del_column_source_name]) &
                (indices[og_column_bl_name] != indices[del_column_bl_name]) &
                (indices[del_column_source_name].notnull())
            ].index,
            inplace=True
        )
        merged_frame.reset_index(drop=True, inplace=True)
