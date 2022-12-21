import numpy as np
import pandas as pd

from molgenis.capice_resources.core import GlobalEnums
from molgenis.capice_resources.process_vep import VEPProcessingEnum, VEPFileEnum


class VEPProcesser:
    @staticmethod
    def drop_genes_empty(data: pd.DataFrame) -> None:
        print('Dropping empty genes.')
        data.drop(index=data[data[VEPFileEnum.SYMBOL.value].isnull()].index, inplace=True)

    @staticmethod
    def process_grch38(data: pd.DataFrame):
        print('Processing GRCh38.')
        data[VEPFileEnum.CHROM.value] = \
        data[VEPFileEnum.CHROM.value].str.split('chr', expand=True)[1]
        y = np.append(np.arange(1, 23).astype(str), ['X', 'Y', 'MT'])
        data.drop(data[~data[VEPFileEnum.CHROM.value].isin(y)].index, inplace=True)

    @staticmethod
    def drop_duplicate_entries(data: pd.DataFrame):
        print('Dropping duplicated variants.')
        data.drop_duplicates(inplace=True)

    @staticmethod
    def drop_mismatching_genes(data: pd.DataFrame):
        print('Dropping variants with mismatching genes.')
        data.drop(
            index=data[data[VEPFileEnum.ID.value].str.split(
                GlobalEnums.SEPARATOR.value, expand=True
            )[4] != data[VEPFileEnum.SYMBOL.value]].index,
            inplace=True
        )

    @staticmethod
    def drop_heterozygous_variants_in_ar_genes(data: pd.DataFrame, cgd: list):
        print('Dropping heterozygous variants in AR genes.')
        data.drop(
            data[
                (data[VEPFileEnum.GNOMAD_HN.value].notnull()) &
                (data[VEPFileEnum.GNOMAD_HN.value] == 0) &
                (data[VEPFileEnum.SYMBOL.value].isin(cgd))
                ].index, inplace=True
        )

    @staticmethod
    def drop_variants_incorrect_label_or_weight(data: pd.DataFrame):
        print('Dropping variants with an incorrect label or weight')
        data.drop(
            index=data[data[VEPProcessingEnum.BINARIZED_LABEL.value].isnull()].index,
            columns=[VEPFileEnum.ID.value],
            inplace=True
        )
        data.drop(
            index=data[~data[VEPProcessingEnum.BINARIZED_LABEL.value].isin([0.0, 1.0])].index,
            inplace=True
        )
        data.drop(
            index=data[~data[VEPProcessingEnum.SAMPLE_WEIGHT.value].isin(
                VEPProcessingEnum.SAMPLE_WEIGHTS.value)].index,
            inplace=True
        )

    @staticmethod
    def drop_duplicates(data: pd.DataFrame, features: list) -> None:
        print('Dropping duplicates according to train features.')
        data.drop_duplicates(subset=features, inplace=True)
