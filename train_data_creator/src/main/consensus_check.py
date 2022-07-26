import warnings

import pandas as pd


class ConsensusChecker:
    def __init__(self):
        self.columns = ['#CHROM', 'POS', 'REF', 'ALT', 'gene']

    def check_consensus_clinvar_vgkl_match(
            self, merged_dataframe: pd.DataFrame
    ):
        before_drop = merged_dataframe.shape[0]

        vkgl_subset = merged_dataframe[merged_dataframe['source'] == 'VKGL'].copy(deep=True)
        clinvar_subset = merged_dataframe[merged_dataframe['source'] == 'ClinVar'].copy(deep=True)

        output_dataframe = self.perform_check(
            merged_dataframe,
            vkgl_subset
        )

        output_dataframe = self.perform_check(
            output_dataframe,
            clinvar_subset
        )
        after_drop = output_dataframe.shape[0]
        div = int((before_drop - after_drop) / 2)
        if div > 0:
            warnings.warn(
                f'There are {div} variants with mismatching consensus between ClinVar and '
                f'VKGL'
            )
        return output_dataframe

    def perform_check(self, merged_dataframe, subset):
        original_labels = merged_dataframe.columns
        checking_dataframe = merged_dataframe.merge(
            subset, on=self.columns, suffixes=('_og', '_del'), how='left'
        )
        checking_dataframe.drop(
            index=checking_dataframe[
                (checking_dataframe['source_og'] != checking_dataframe['source_del'])
                &
                (checking_dataframe['binarized_label_og'] != checking_dataframe[
                    'binarized_label_del'])
                &
                (checking_dataframe['source_del'].notnull())
                ].index,
            inplace=True
        )
        checking_dataframe.drop(
            columns=['class_del', 'review_del', 'source_del', 'binarized_label_del'], inplace=True
        )
        checking_dataframe.columns = original_labels
        return checking_dataframe
