import warnings

import numpy as np
import pandas as pd

from molgenis.capice_resources.core import VCFEnums, ColumnEnums
from molgenis.capice_resources.train_data_creator import TrainDataCreatorEnums


def check_unsupported_contigs(loaded_dataset: pd.DataFrame, column_name: str) -> None:
    """
    Function to check a loaded VKGL and/or ClinVar dataframe "chromosome" column for alternative
    contigs to 1-22, X, Y and MT. Performed inplace.

    Args:
        loaded_dataset:
            The loaded in pandas.DataFrame of the VKGL or ClinVar dataset.
        column_name:
            The column name to check upon.
    """
    loaded_dataset['contigs'] = loaded_dataset[column_name].astype(str)
    loaded_dataset.loc[loaded_dataset[loaded_dataset['contigs'] == 'X'].index, 'contigs'] = '23'
    loaded_dataset.loc[loaded_dataset[loaded_dataset['contigs'] == 'Y'].index, 'contigs'] = '24'
    loaded_dataset.loc[loaded_dataset[loaded_dataset['contigs'] == 'MT'].index, 'contigs'] = '25'
    present_contigs = np.array(range(1, 26)).astype(str)
    alt_contigs = loaded_dataset[~loaded_dataset['contigs'].isin(present_contigs)]
    if alt_contigs.shape[0] > 0:
        warnings.warn(f'Removing unsupported contig for {alt_contigs.shape[0]} variant(s).')
        loaded_dataset.drop(index=alt_contigs.index, inplace=True)
    loaded_dataset.drop(columns='contigs', inplace=True)


def correct_order_vcf_notation(pseudo_vcf: pd.DataFrame) -> None:
    """
    Function to order a (pseudo) VCF on chromosome and position.

    Args:
        pseudo_vcf:
            The pandas dataframe containing #CHROM and POS columns.
            Please note that this ordering is performed inplace.

    """
    # Ensuring that the order is set to string so that any alt contigs do not get unnoticed.
    pseudo_vcf['order'] = pseudo_vcf[VCFEnums.CHROM.vcf_name]
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'X'].index, 'order'] = 23
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'Y'].index, 'order'] = 24
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'MT'].index, 'order'] = 25
    pseudo_vcf['order'] = pseudo_vcf['order'].astype(int)
    pseudo_vcf.sort_values(by=['order', VCFEnums.POS.value], inplace=True)
    pseudo_vcf.drop(columns='order', inplace=True)
    pseudo_vcf.reset_index(drop=True, inplace=True)


def apply_binarized_label(data: pd.DataFrame) -> None:
    """
    Function to apply the binarized label.

    Args:
        data:
            The somewhat parsed data that contains the "class" column.
            Adds the "binarized_label" column. Which is 0 for LB and B, and 1 for P and LP.
            Please note that this performed inplace.
    """
    data[ColumnEnums.BINARIZED_LABEL.value] = np.nan
    data.loc[
        data[data[TrainDataCreatorEnums.CLASS.value].isin(['LB', 'B'])].index,
        ColumnEnums.BINARIZED_LABEL.value
    ] = 0
    data.loc[
        data[data[TrainDataCreatorEnums.CLASS.value].isin(['LP', 'P'])].index,
        ColumnEnums.BINARIZED_LABEL.value
    ] = 1
    data.drop(index=data[data[ColumnEnums.BINARIZED_LABEL.value].isnull()].index, inplace=True)
