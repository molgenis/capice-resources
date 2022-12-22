import warnings

import numpy as np
import pandas as pd

from molgenis.capice_resources.core import GlobalEnums
from molgenis.capice_resources.utilities import add_dataset_source
from molgenis.capice_resources.train_data_creator import TrainDataCreatorEnums
from molgenis.capice_resources.train_data_creator.utilities import apply_binarized_label


class ClinVarParser:
    def parse(self, clinvar_frame: pd.DataFrame) -> pd.DataFrame:
        self._obtain_class(clinvar_frame)
        self._obtain_gene(clinvar_frame)
        self._obtain_review(clinvar_frame)
        add_dataset_source(clinvar_frame, TrainDataCreatorEnums.CLINVAR.value)
        clinvar_frame = clinvar_frame[TrainDataCreatorEnums.columns_of_interest()]
        self._correct_class(clinvar_frame)
        apply_binarized_label(clinvar_frame)
        return clinvar_frame

    def _obtain_class(self, clinvar_frame) -> None:
        self._process_column(clinvar_frame, TrainDataCreatorEnums.CLASS.value, 'CLNSIG=')

    def _obtain_gene(self, clinvar_frame) -> None:
        self._process_column(clinvar_frame, TrainDataCreatorEnums.GENE.value, 'GENEINFO=')

    def _obtain_review(self, clinvar_frame) -> None:
        self._process_column(clinvar_frame, TrainDataCreatorEnums.REVIEW.value, 'CLNREVSTAT=')
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
        for status in clinvar_frame[TrainDataCreatorEnums.REVIEW.value].unique():
            if status not in stars.keys():
                warnings.warn(f'Found unknown review status: {status}')

        clinvar_frame.drop(
            index=clinvar_frame[
                ~clinvar_frame[TrainDataCreatorEnums.REVIEW.value].isin(stars.keys())
            ].index, inplace=True
        )

        clinvar_frame[TrainDataCreatorEnums.REVIEW.value] = clinvar_frame[
            TrainDataCreatorEnums.REVIEW.value].map(stars)
        clinvar_frame[TrainDataCreatorEnums.REVIEW.value] = clinvar_frame[
            TrainDataCreatorEnums.REVIEW.value].astype(np.int64)
        clinvar_frame.drop(
            index=clinvar_frame[clinvar_frame[TrainDataCreatorEnums.REVIEW.value] < 1].index,
            inplace=True
        )

    @staticmethod
    def _process_column(clinvar_frame, column_to_add, split_identifier):
        clinvar_frame[column_to_add] = clinvar_frame[
            GlobalEnums.INFO.value
        ].str.split(split_identifier, expand=True)[1].str.split(';', expand=True)[0]

    @staticmethod
    def _correct_class(clinvar_frame):
        classes = {
                'Uncertain_significance': 'VUS',
                'Likely_benign': 'LB',
                'Benign': 'B',
                'Pathogenic': 'P',
                'Likely_pathogenic': 'LP',
                'Benign/Likely_benign': 'LB',
                'Pathogenic/Likely_pathogenic': 'LP'
            }
        for c in clinvar_frame[TrainDataCreatorEnums.CLASS.value].unique():
            if c not in classes.keys():
                clinvar_frame.drop(
                    index=clinvar_frame[
                        clinvar_frame[TrainDataCreatorEnums.CLASS.value] == c
                        ].index,
                    inplace=True
                )
        for key, value in classes.items():
            clinvar_frame.loc[
                clinvar_frame[clinvar_frame[TrainDataCreatorEnums.CLASS.value] == key].index,
                TrainDataCreatorEnums.CLASS.value
            ] = value
