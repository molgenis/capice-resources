import numpy as np
import pandas as pd

from molgenis.capice_resources.core import VCFEnums, ColumnEnums
from molgenis.capice_resources.train_data_creator import TrainDataCreatorEnums as Menums


def correct_order_vcf_notation(pseudo_vcf: pd.DataFrame) -> None:
    """
    Function to order a (pseudo) VCF on chromosome and position.

    Args:
        pseudo_vcf:
            The pandas dataframe containing #CHROM and POS columns.
            Please note that this ordering is performed inplace.

    """
    pseudo_vcf['order'] = pseudo_vcf[VCFEnums.VCF_CHROM.value]
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
    print('Applying binarized label.')
    data[ColumnEnums.BINARIZED_LABEL.value] = np.nan
    data.loc[
        data[data[Menums.CLASS.value].isin(['LB', 'B'])].index,
        ColumnEnums.BINARIZED_LABEL.value
    ] = 0
    data.loc[
        data[data[Menums.CLASS.value].isin(['LP', 'P'])].index,
        ColumnEnums.BINARIZED_LABEL.value
    ] = 1
    data.drop(index=data[data[ColumnEnums.BINARIZED_LABEL.value].isnull()].index, inplace=True)
