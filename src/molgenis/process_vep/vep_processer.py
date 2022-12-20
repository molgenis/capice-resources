import numpy as np
import pandas as pd

from molgenis.core import GlobalEnums
from molgenis.process_vep import VEPProcessingEnum


class VEPProcesser:
    @staticmethod
    def drop_genes_empty(data: pd.DataFrame) -> None:
        print('Dropping empty genes.')
        data.drop(index=data[data[VEPProcessingEnum.SYMBOL.value].isnull()].index, inplace=True)

    @staticmethod
    def process_grch38(data: pd.DataFrame):
        print('Processing GRCh38.')
        data[VEPProcessingEnum.CHROM.value] = \
        data[VEPProcessingEnum.CHROM.value].str.split('chr', expand=True)[1]
        y = np.append(np.arange(1, 23).astype(str), ['X', 'Y', 'MT'])
        data.drop(data[~data[VEPProcessingEnum.CHROM.value].isin(y)].index, inplace=True)

    @staticmethod
    def drop_duplicate_entries(data: pd.DataFrame):
        print('Dropping duplicated variants.')
        data.drop_duplicates(inplace=True)

    @staticmethod
    def drop_mismatching_genes(data: pd.DataFrame):
        print('Dropping variants with mismatching genes.')
        data.drop(
            index=data[data[VEPProcessingEnum.ID.value].str.split(
                GlobalEnums.SEPARATOR.value, expand=True
            )[4] != data[VEPProcessingEnum.SYMBOL.value]].index,
            inplace=True
        )

    @staticmethod
    def drop_heterozygous_variants_in_ar_genes(data: pd.DataFrame, cgd: list):
        print('Dropping heterozygous variants in AR genes.')
        data.drop(
            data[
                (data[VEPProcessingEnum.GNOMAD_HN.value].notnull()) &
                (data[VEPProcessingEnum.GNOMAD_HN.value] == 0) &
                (data[VEPProcessingEnum.SYMBOL.value].isin(cgd))
                ].index, inplace=True
        )

    @staticmethod
    def drop_variants_incorrect_label_or_weight(data: pd.DataFrame):
        print('Dropping variants with an incorrect label or weight')
        data.drop(
            index=data[data[VEPProcessingEnum.BINARIZED_LABEL.value].isnull()].index,
            columns=[VEPProcessingEnum.ID.value],
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
