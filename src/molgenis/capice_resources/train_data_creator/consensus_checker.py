import warnings

import pandas as pd

from molgenis.capice_resources.core import ColumnEnums, VCFEnums
from molgenis.capice_resources.train_data_creator import TrainDataCreatorEnums


class ConsensusChecker:
    def check_consensus_clinvar_vkgl_match(self, merged_frame: pd.DataFrame) -> None:
        """
        Method to check if the consensus for a variant between VKGL and ClinVar matches.

        Args:
            merged_frame:
                The pandas.Dataframe merged between VKGL and ClinVar.
                Please note that this check is performed inplace.

        """
        before_drop = merged_frame.shape[0]

        # For consistency reasons creating a new merge_column to ensure proper function in the merge
        merged_frame[TrainDataCreatorEnums.MERGE_COLUMN.value] = merged_frame[
            TrainDataCreatorEnums.further_processing_columns()
        ].astype(str).agg(VCFEnums.ID_SEPARATOR.value.join, axis=1)
        columns_to_check = [
            TrainDataCreatorEnums.MERGE_COLUMN.value,
            ColumnEnums.DATASET_SOURCE.value,
            ColumnEnums.BINARIZED_LABEL.value
        ]

        vkgl_subset = merged_frame.loc[
            merged_frame[
                merged_frame[ColumnEnums.DATASET_SOURCE.value] == TrainDataCreatorEnums.VKGL.value
                ].index,
            columns_to_check
        ]
        clinvar_subset = merged_frame.loc[
            merged_frame[
                merged_frame[
                    ColumnEnums.DATASET_SOURCE.value
                ] == TrainDataCreatorEnums.CLINVAR.value
                ].index,
            columns_to_check
        ]
        self._perform_check(merged_frame, vkgl_subset)
        self._perform_check(merged_frame, clinvar_subset)

        merged_frame.drop(columns=TrainDataCreatorEnums.MERGE_COLUMN.value, inplace=True)

        after_drop = merged_frame.shape[0]
        div = int((before_drop - after_drop) / 2)
        if div > 0:
            warnings.warn(
                f'Removed {div} variant(s) due to mismatch in consensus'
            )

    @staticmethod
    def _perform_check(merged_frame: pd.DataFrame, subset_frame: pd.DataFrame) -> None:
        """
        Method to reduce code duplication for checking both ClinVar and VKGL independently.

        Args:
            merged_frame:
                The merged dataframe between VKGL and ClinVar.
                Please note that this is performed inplace.
            subset_frame:
                Subset of merged dataframe containing either only variants from VKGL or ClinVar.

        """
        indices = merged_frame.merge(
            subset_frame,
            on=TrainDataCreatorEnums.MERGE_COLUMN.value,
            suffixes=('_og', '_del'),
            how='left'
        )
        og_column_source_name = ColumnEnums.DATASET_SOURCE.value + '_og'
        og_column_bl_name = ColumnEnums.BINARIZED_LABEL.value + '_og'
        del_column_source_name = ColumnEnums.DATASET_SOURCE.value + '_del'
        del_column_bl_name = ColumnEnums.BINARIZED_LABEL.value + '_del'
        merged_frame.drop(
            index=indices[
                (indices[og_column_source_name] != indices[del_column_source_name]) &
                (indices[og_column_bl_name] != indices[del_column_bl_name]) &
                (indices[del_column_source_name].notnull())
            ].index,
            inplace=True
        )
        merged_frame.reset_index(drop=True, inplace=True)
