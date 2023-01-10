import warnings

import numpy as np
import pandas as pd

from molgenis.capice_resources.core import add_dataset_source
from molgenis.capice_resources.core import GlobalEnums as Genums
from molgenis.capice_resources.train_data_creator import TrainDataCreatorEnums as Menums
from molgenis.capice_resources.train_data_creator.utilities import apply_binarized_label


class ClinVarParser:
    def parse(self, clinvar_frame: pd.DataFrame) -> pd.DataFrame:
        """
        Main parsing function of the ClinVar data parser.

        Args:
            clinvar_frame:
                The loaded in dataframe of the ClinVar VCF (not including the VCF headers).

        Returns:
            frame:
                Fully parsed and processed ClinVar dataframe, adhering to all the standard
                columns and equalized to VKGL.
        """
        self._obtain_class(clinvar_frame)
        self._obtain_gene(clinvar_frame)
        self._obtain_review(clinvar_frame)
        add_dataset_source(clinvar_frame, Menums.CLINVAR.value)  # type: ignore
        clinvar_frame_interest = clinvar_frame.loc[:, Menums.columns_of_interest()]
        del clinvar_frame  # freeing up memory
        self._correct_class(clinvar_frame_interest)
        apply_binarized_label(clinvar_frame_interest)
        return clinvar_frame_interest

    def _obtain_class(self, clinvar_frame: pd.DataFrame) -> None:
        """
        Function to obtain the classification from the INFO field.

        Args:
            clinvar_frame:
                The clinvar dataframe.
                Performed inplace.
        """
        self._process_column(clinvar_frame, Menums.CLASS.value, 'CLNSIG=')

    def _obtain_gene(self, clinvar_frame: pd.DataFrame) -> None:
        """
        Function to obtain the gene from the INFO field.

        Args:
            clinvar_frame:
                The clinvar dataframe.
                Performed inplace.
        """
        self._process_column(clinvar_frame, Menums.GENE.value, 'GENEINFO=')

    def _obtain_review(self, clinvar_frame: pd.DataFrame) -> None:
        """
        Function to obtain the review score from the INFO field.
        Also warns the user if a review status is found that is not yet known or been made aware of.

        Args:
            clinvar_frame:
                The clinvar dataframe.
                Performed inplace.
        """
        self._process_column(clinvar_frame, Menums.REVIEW.value, 'CLNREVSTAT=')
        stars = {
            'criteria_provided,_conflicting_interpretations': -1,
            'no_assertion_provided': 0,
            'no_assertion_criteria_provided': 0,
            'no_interpretation_for_the_single_variant': 0,
            'criteria_provided,_single_submitter': 1,
            'criteria_provided,_multiple_submitters,_no_conflicts': 2,
            'reviewed_by_expert_panel': 3,
            'practice_guideline': 4
        }
        for status in clinvar_frame[Menums.REVIEW.value].unique():
            if status not in stars.keys():
                warnings.warn(f'Found unknown review status: {status}')

        clinvar_frame.drop(
            index=clinvar_frame[
                ~clinvar_frame[Menums.REVIEW.value].isin(stars.keys())
            ].index, inplace=True
        )

        clinvar_frame[Menums.REVIEW.value] = clinvar_frame[
            Menums.REVIEW.value].map(stars)
        clinvar_frame[Menums.REVIEW.value] = clinvar_frame[
            Menums.REVIEW.value].astype(np.int64)
        clinvar_frame.drop(
            index=clinvar_frame[clinvar_frame[Menums.REVIEW.value] < 1].index,
            inplace=True
        )

    @staticmethod
    def _process_column(clinvar_frame: pd.DataFrame, column_to_add: str, split_identifier: str) \
            -> None:
        """
        Function to reduce code duplication to obtain columns from the INFO field.

        Args:
            clinvar_frame:
                The clinvar dataframe.
                Performed inplace.
            column_to_add:
                What the newly added column should be called.
            split_identifier:
                The identifier on what to split the INFO field.

        """
        clinvar_frame[column_to_add] = clinvar_frame[
            Genums.INFO.value
        ].str.split(split_identifier, expand=True)[1].str.split(';', expand=True)[0]

    @staticmethod
    def _correct_class(clinvar_frame: pd.DataFrame) -> None:
        """
        Method to correct and equalize the classifications that can be obtained from the ClinVar
        classification column.

        Args:
            clinvar_frame:
                The clinvar dataframe.
                Performed inplace.

        """
        classes = {
                'Uncertain_significance': 'VUS',
                'Likely_benign': 'LB',
                'Benign': 'B',
                'Pathogenic': 'P',
                'Likely_pathogenic': 'LP',
                'Benign/Likely_benign': 'LB',
                'Pathogenic/Likely_pathogenic': 'LP'
            }
        for c in clinvar_frame[Menums.CLASS.value].unique():
            if c not in classes.keys():
                clinvar_frame.drop(
                    index=clinvar_frame[
                        clinvar_frame[Menums.CLASS.value] == c
                        ].index,
                    inplace=True
                )
        for key, value in classes.items():
            clinvar_frame.loc[
                clinvar_frame[clinvar_frame[Menums.CLASS.value] == key].index,
                Menums.CLASS.value
            ] = value
