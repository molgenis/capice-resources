import numpy as np
import pandas as pd

from molgenis.capice_resources.core import ColumnEnums, VCFEnums
from molgenis.capice_resources.process_vep import ProcessVEPEnums


class VEPProcesser:
    """
    Class to house all VEP processors.

    Please note that a print statement should be made what the processor is processing, as the
    progress printer does not know what each of these processors do.
    """
    @staticmethod
    def drop_genes_empty(data: pd.DataFrame) -> None:
        """
        Method to drop all entries where the VEP output GENE column does not contain any entries.

        Args:
            data:
                Merged dataframe between train-test and validation.
                It is performed inplace and does not return anything.

        """
        print('Dropping empty genes.')
        data.drop(index=data[data[ColumnEnums.SYMBOL.value].isnull()].index, inplace=True)

    @staticmethod
    def process_grch38(data: pd.DataFrame) -> None:
        """
        Method to process all GRCh38 entries and their alternative contigs.

        Args:
            data:
                Merged dataframe between train-test and validation.
                It is performed inplace and does not return anything.

        """
        print('Processing GRCh38.')
        data[VCFEnums.CHROM.processed_name] = data[VCFEnums.CHROM.processed_name].str.split(
            VCFEnums.CHROM.shortened_name, expand=True)[1]
        y = np.append(np.arange(1, 23).astype(str), ['X', 'Y', 'MT'])
        data.drop(data[~data[VCFEnums.CHROM.processed_name].isin(y)].index, inplace=True)

    @staticmethod
    def drop_duplicate_entries(data: pd.DataFrame) -> None:
        """
        Method drop fully duplicated entries, regardless of the train features or not.

        Args:
            data:
                Merged dataframe between train-test and validation.
                It is performed inplace and does not return anything.

        """
        print('Dropping duplicated variants.')
        data.drop_duplicates(inplace=True)

    @staticmethod
    def drop_mismatching_genes(data: pd.DataFrame) -> None:
        """
        Method to drop entries where the ID gene does not match the SYMBOL gene.

        Args:
            data:
                Merged dataframe between train-test and validation.
                It is performed inplace and does not return anything.

        """
        print('Dropping variants with mismatching genes.')
        data.drop(
            index=data[data[VCFEnums.ID.value].str.split(
                VCFEnums.ID_SEPARATOR.value, expand=True
            )[4] != data[ColumnEnums.SYMBOL.value]].index,
            inplace=True
        )

    @staticmethod
    def drop_heterozygous_variants_in_ar_genes(data: pd.DataFrame, cgd: list) -> None:
        """
        Method to drop variants that have only been observed heterozygous in Autosomal Recessive
        genes.

        Args:
            data:
                Merged dataframe between train-test and validation.
                It is performed inplace and does not return anything.
            cgd:
                List of all the CGD AR genes.
        """
        print('Dropping heterozygous variants in AR genes.')
        data.drop(
            data[
                (data[ProcessVEPEnums.GNOMAD_HN.value].notnull()) &
                (data[ProcessVEPEnums.GNOMAD_HN.value] == 0) &
                (data[ColumnEnums.SYMBOL.value].isin(cgd))
                ].index, inplace=True
        )

    @staticmethod
    def drop_variants_incorrect_label_or_weight(data: pd.DataFrame) -> None:
        """
        Method to drop samples where the label or sample weight does not adhere to standards.

        Args:
            data:
                Merged dataframe between train-test and validation.
                It is performed inplace and does not return anything.

        """
        print('Dropping variants with an incorrect label or weight')
        data.drop(
            index=data[data[ColumnEnums.BINARIZED_LABEL.value].isnull()].index,
            columns=[VCFEnums.ID.value],
            inplace=True
        )
        data.drop(
            index=data[~data[ColumnEnums.BINARIZED_LABEL.value].isin([0.0, 1.0])].index,
            inplace=True
        )
        data.drop(
            index=data[~data[ColumnEnums.SAMPLE_WEIGHT.value].isin(
                ProcessVEPEnums.SAMPLE_WEIGHTS.value)].index,
            inplace=True
        )

    @staticmethod
    def drop_duplicates(data: pd.DataFrame, features: list) -> None:
        """
        Method drop fully duplicated entries according to the training features.

        Args:
            data:
                Merged dataframe between train-test and validation.
                It is performed inplace and does not return anything.
            features:
                List of all the features that are going to be used in capice train.
        """
        print('Dropping duplicates according to train features.')
        data.drop_duplicates(subset=features, inplace=True)
