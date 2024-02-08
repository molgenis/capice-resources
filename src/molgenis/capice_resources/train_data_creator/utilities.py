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
    # Ensuring that the order is set to string so that any alt contigs do not get unnoticed.
    loaded_dataset['contigs'] = loaded_dataset[column_name].astype(str)
    loaded_dataset.loc[loaded_dataset[loaded_dataset['contigs'] == 'chr1'].index, 'contigs'] = '1'
    loaded_dataset.loc[loaded_dataset[loaded_dataset['contigs'] == 'chr2'].index, 'contigs'] = '2'
    loaded_dataset.loc[loaded_dataset[loaded_dataset['contigs'] == 'chr3'].index, 'contigs'] = '3'
    loaded_dataset.loc[loaded_dataset[loaded_dataset['contigs'] == 'chr4'].index, 'contigs'] = '4'
    loaded_dataset.loc[loaded_dataset[loaded_dataset['contigs'] == 'chr5'].index, 'contigs'] = '5'
    loaded_dataset.loc[loaded_dataset[loaded_dataset['contigs'] == 'chr6'].index, 'contigs'] = '6'
    loaded_dataset.loc[loaded_dataset[loaded_dataset['contigs'] == 'chr7'].index, 'contigs'] = '7'
    loaded_dataset.loc[loaded_dataset[loaded_dataset['contigs'] == 'chr8'].index, 'contigs'] = '8'
    loaded_dataset.loc[loaded_dataset[loaded_dataset['contigs'] == 'chr9'].index, 'contigs'] = '9'
    loaded_dataset.loc[loaded_dataset[loaded_dataset['contigs'] == 'chr10'].index, 'contigs'] = '10'
    loaded_dataset.loc[loaded_dataset[loaded_dataset['contigs'] == 'chr11'].index, 'contigs'] = '11'
    loaded_dataset.loc[loaded_dataset[loaded_dataset['contigs'] == 'chr12'].index, 'contigs'] = '12'
    loaded_dataset.loc[loaded_dataset[loaded_dataset['contigs'] == 'chr13'].index, 'contigs'] = '13'
    loaded_dataset.loc[loaded_dataset[loaded_dataset['contigs'] == 'chr14'].index, 'contigs'] = '14'
    loaded_dataset.loc[loaded_dataset[loaded_dataset['contigs'] == 'chr15'].index, 'contigs'] = '15'
    loaded_dataset.loc[loaded_dataset[loaded_dataset['contigs'] == 'chr16'].index, 'contigs'] = '16'
    loaded_dataset.loc[loaded_dataset[loaded_dataset['contigs'] == 'chr17'].index, 'contigs'] = '17'
    loaded_dataset.loc[loaded_dataset[loaded_dataset['contigs'] == 'chr18'].index, 'contigs'] = '18'
    loaded_dataset.loc[loaded_dataset[loaded_dataset['contigs'] == 'chr19'].index, 'contigs'] = '19'
    loaded_dataset.loc[loaded_dataset[loaded_dataset['contigs'] == 'chr20'].index, 'contigs'] = '20'
    loaded_dataset.loc[loaded_dataset[loaded_dataset['contigs'] == 'chr21'].index, 'contigs'] = '21'
    loaded_dataset.loc[loaded_dataset[loaded_dataset['contigs'] == 'chr22'].index, 'contigs'] = '22'
    loaded_dataset.loc[loaded_dataset[loaded_dataset['contigs'] == 'chrX'].index, 'contigs'] = '23'
    loaded_dataset.loc[loaded_dataset[loaded_dataset['contigs'] == 'chrY'].index, 'contigs'] = '24'
    loaded_dataset.loc[loaded_dataset[loaded_dataset['contigs'] == 'chrM'].index, 'contigs'] = '25'
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
    pseudo_vcf['order'] = pseudo_vcf[VCFEnums.CHROM.vcf_name]
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'chr1'].index, 'order'] = 1
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'chr2'].index, 'order'] = 2
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'chr3'].index, 'order'] = 3
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'chr4'].index, 'order'] = 4
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'chr5'].index, 'order'] = 5
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'chr6'].index, 'order'] = 6
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'chr7'].index, 'order'] = 7
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'chr8'].index, 'order'] = 8
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'chr9'].index, 'order'] = 9
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'chr10'].index, 'order'] = 10
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'chr11'].index, 'order'] = 11
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'chr12'].index, 'order'] = 12
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'chr13'].index, 'order'] = 13
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'chr14'].index, 'order'] = 14
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'chr15'].index, 'order'] = 15
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'chr16'].index, 'order'] = 16
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'chr17'].index, 'order'] = 17
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'chr18'].index, 'order'] = 18
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'chr19'].index, 'order'] = 19
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'chr20'].index, 'order'] = 20
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'chr21'].index, 'order'] = 21
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'chr22'].index, 'order'] = 22
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'chrX'].index, 'order'] = 23
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'chrY'].index, 'order'] = 24
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'chrM'].index, 'order'] = 25
    pseudo_vcf['order'] = pseudo_vcf['order'].astype(int)
    pseudo_vcf.sort_values(by=['order', VCFEnums.POS.value], inplace=True)
    pseudo_vcf.drop(columns='order', inplace=True)
    pseudo_vcf.reset_index(drop=True, inplace=True)


def preprocess_clinvar(clinvar_vcf: pd.DataFrame) -> None:
    clinvar_vcf.loc[clinvar_vcf[clinvar_vcf['#CHROM'] == '1'].index, '#CHROM'] = 'chr1'
    clinvar_vcf.loc[clinvar_vcf[clinvar_vcf['#CHROM'] == '2'].index, '#CHROM'] = 'chr2'
    clinvar_vcf.loc[clinvar_vcf[clinvar_vcf['#CHROM'] == '3'].index, '#CHROM'] = 'chr3'
    clinvar_vcf.loc[clinvar_vcf[clinvar_vcf['#CHROM'] == '4'].index, '#CHROM'] = 'chr4'
    clinvar_vcf.loc[clinvar_vcf[clinvar_vcf['#CHROM'] == '5'].index, '#CHROM'] = 'chr5'
    clinvar_vcf.loc[clinvar_vcf[clinvar_vcf['#CHROM'] == '6'].index, '#CHROM'] = 'chr6'
    clinvar_vcf.loc[clinvar_vcf[clinvar_vcf['#CHROM'] == '7'].index, '#CHROM'] = 'chr7'
    clinvar_vcf.loc[clinvar_vcf[clinvar_vcf['#CHROM'] == '8'].index, '#CHROM'] = 'chr8'
    clinvar_vcf.loc[clinvar_vcf[clinvar_vcf['#CHROM'] == '9'].index, '#CHROM'] = 'chr9'
    clinvar_vcf.loc[clinvar_vcf[clinvar_vcf['#CHROM'] == '10'].index, '#CHROM'] = 'chr10'
    clinvar_vcf.loc[clinvar_vcf[clinvar_vcf['#CHROM'] == '11'].index, '#CHROM'] = 'chr11'
    clinvar_vcf.loc[clinvar_vcf[clinvar_vcf['#CHROM'] == '12'].index, '#CHROM'] = 'chr12'
    clinvar_vcf.loc[clinvar_vcf[clinvar_vcf['#CHROM'] == '13'].index, '#CHROM'] = 'chr13'
    clinvar_vcf.loc[clinvar_vcf[clinvar_vcf['#CHROM'] == '14'].index, '#CHROM'] = 'chr14'
    clinvar_vcf.loc[clinvar_vcf[clinvar_vcf['#CHROM'] == '15'].index, '#CHROM'] = 'chr15'
    clinvar_vcf.loc[clinvar_vcf[clinvar_vcf['#CHROM'] == '16'].index, '#CHROM'] = 'chr16'
    clinvar_vcf.loc[clinvar_vcf[clinvar_vcf['#CHROM'] == '17'].index, '#CHROM'] = 'chr17'
    clinvar_vcf.loc[clinvar_vcf[clinvar_vcf['#CHROM'] == '18'].index, '#CHROM'] = 'chr18'
    clinvar_vcf.loc[clinvar_vcf[clinvar_vcf['#CHROM'] == '19'].index, '#CHROM'] = 'chr19'
    clinvar_vcf.loc[clinvar_vcf[clinvar_vcf['#CHROM'] == '20'].index, '#CHROM'] = 'chr20'
    clinvar_vcf.loc[clinvar_vcf[clinvar_vcf['#CHROM'] == '21'].index, '#CHROM'] = 'chr21'
    clinvar_vcf.loc[clinvar_vcf[clinvar_vcf['#CHROM'] == '22'].index, '#CHROM'] = 'chr22'
    clinvar_vcf.loc[clinvar_vcf[clinvar_vcf['#CHROM'] == 'X'].index, '#CHROM'] = 'chrX'
    clinvar_vcf.loc[clinvar_vcf[clinvar_vcf['#CHROM'] == 'Y'].index, '#CHROM'] = 'chrY'
    clinvar_vcf.loc[clinvar_vcf[clinvar_vcf['#CHROM'] == 'MT'].index, '#CHROM'] = 'chrM'


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
