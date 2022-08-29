import warnings

import pandas as pd


class ConsensusChecker:
    def __init__(self):
        self.columns = ['#CHROM', 'POS', 'REF', 'ALT', 'gene']

    def check_consensus_clinvar_vgkl_match(self, merged_dataframe: pd.DataFrame):
        before_drop = merged_dataframe.shape[0]

        vkgl_subset = merged_dataframe[merged_dataframe['source'] == 'VKGL'].copy(deep=True)
        clinvar_subset = merged_dataframe[merged_dataframe['source'] == 'ClinVar'].copy(deep=True)

        self.perform_check(
            merged_dataframe,
            vkgl_subset
        )

        self.perform_check(
            merged_dataframe,
            clinvar_subset
        )
        after_drop = merged_dataframe.shape[0]
        div = int((before_drop - after_drop) / 2)
        if div > 0:
            warnings.warn(
                f'Removed {div} variant(s) with mismatching consensus between ClinVar and VKGL'
            )

    def perform_check(self, merged_dataframe, subset):
        indices = merged_dataframe.merge(
            subset, on=self.columns, suffixes=('_og', '_del'), how='left'
        )
        merged_dataframe.drop(
            index=indices[
                (indices['source_og'] != indices['source_del'])
                &
                (indices['binarized_label_og'] != indices[
                    'binarized_label_del'])
                &
                (indices['source_del'].notnull())
                ].index,
            inplace=True
        )
        merged_dataframe.reset_index(drop=True, inplace=True)
