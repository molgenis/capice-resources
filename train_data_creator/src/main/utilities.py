from pathlib import Path

import numpy as np
import pandas as pd


def correct_order_vcf_notation(pseudo_vcf: pd.DataFrame):
    print('Ordering (pseudo_)VCF')
    pseudo_vcf['order'] = pseudo_vcf['#CHROM']
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'X'].index, 'order'] = 23
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'Y'].index, 'order'] = 24
    pseudo_vcf.loc[pseudo_vcf[pseudo_vcf['order'] == 'MT'].index, 'order'] = 25
    pseudo_vcf['order'] = pseudo_vcf['order'].astype(int)
    pseudo_vcf.sort_values(by=['order', 'POS'], inplace=True)
    pseudo_vcf.drop(columns='order', inplace=True)
    pseudo_vcf.reset_index(drop=True, inplace=True)
    return pseudo_vcf


columns_of_interest = ['#CHROM', 'POS', 'REF', 'ALT', 'gene', 'class', 'review', 'source']


def equalize_class(data: pd.DataFrame, equalize_dict: dict):
    print('Equalizing classes.')
    # Drop the classes that we are not interested in.
    for c in data['class'].unique():
        if c not in equalize_dict.keys():
            data.drop(index=data[data['class'] == c].index, inplace=True)
    for key, value in equalize_dict.items():
        data.loc[data[data['class'] == key].index, 'class'] = value
    return data


def apply_binarized_label(data: pd.DataFrame):
    print('Applying binarized label.')
    data['binarized_label'] = np.nan
    data.loc[data[data['class'].isin(['LB', 'B'])].index, 'binarized_label'] = 0
    data.loc[data[data['class'].isin(['LP', 'P'])].index, 'binarized_label'] = 1
    data.drop(index=data[data['binarized_label'].isnull()].index, inplace=True)
    return data


project_root_dir = Path(__file__).parent.parent.parent
