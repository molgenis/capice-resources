import warnings

import pandas as pd


class ConsensusChecker:
    @staticmethod
    def check_consensus_clinvar_vgkl_match(merged_dataframe: pd.DataFrame):
        subset = ['#CHROM', 'POS', 'REF', 'ALT', 'gene']
        n_dupes_inc_consensus = merged_dataframe[merged_dataframe.duplicated(
            subset=subset + ['binarized_label']
        )].shape[0]
        n_dupes_no_consensus = merged_dataframe[merged_dataframe.duplicated(
            subset=subset
        )].shape[0]
        n = abs(n_dupes_no_consensus - n_dupes_inc_consensus)
        if n > 0:
            warnings.warn(
                f'There are {n} variants with mismatching consensus between ClinVar and VKGL'
            )
        merged_dataframe.drop_duplicates(subset=subset, keep=False, inplace=True)
