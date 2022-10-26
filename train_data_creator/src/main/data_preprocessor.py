import gzip
import warnings
import numpy as np
import pandas as pd

from train_data_creator.src.main.utilities import correct_order_vcf_notation, equalize_class, \
    apply_binarized_label
from train_data_creator.src.main.validators.dataset_validator import DatasetValidator

_COLUMNS_OF_INTEREST = ['#CHROM', 'POS', 'REF', 'ALT', 'gene', 'class', 'review', 'source']


class VKGL:
    def __init__(self):
        self.validator = DatasetValidator()

    def parse(self, file_location):
        data = pd.read_csv(file_location, sep='\t')
        self.validator.validate_vkgl(data)
        self._correct_column_names(data)
        self._correct_support(data)
        correct_order_vcf_notation(data)
        self._apply_review_status(data)
        data['source'] = 'VKGL'
        data = data[_COLUMNS_OF_INTEREST]
        apply_binarized_label(data)
        data.reset_index(drop=True, inplace=True)
        return data

    @staticmethod
    def _apply_review_status(data: pd.DataFrame):
        print('Applying review status.')
        data['review'] = 2
        data.loc[data[data['support'] == 1].index, 'review'] = 1
        return data

    @staticmethod
    def _correct_support(data: pd.DataFrame):
        print('Correcting support.')
        data['support'] = data['support'].str.split(' ', expand=True)[0].astype(int)
        return data

    @staticmethod
    def _correct_column_names(data: pd.DataFrame):
        print('Correcting column names.')
        data.rename(
            columns={
                'chromosome': '#CHROM',
                'start': 'POS',
                'ref': 'REF',
                'alt': 'ALT',
                'classification': 'class'
            }, inplace=True
        )
        return data


class ClinVar:
    def __init__(self):
        self.validator = DatasetValidator()

    def parse(self, file_location):
        skiprows = self._get_n_header(file_location)
        data = pd.read_csv(file_location, sep='\t', skiprows=skiprows)
        self.validator.validate_clinvar(data)
        self._obtain_class(data)
        self._obtain_gene(data)
        self._obtain_review(data)
        data['source'] = 'ClinVar'
        data = data[_COLUMNS_OF_INTEREST]
        equalize_class(
            data,
            equalize_dict={
                'Uncertain_significance': 'VUS',
                'Likely_benign': 'LB',
                'Benign': 'B',
                'Pathogenic': 'P',
                'Likely_pathogenic': 'LP',
                'Benign/Likely_benign': 'LB',
                'Pathogenic/Likely_pathogenic': 'LP'
            }
        )
        apply_binarized_label(data)
        data.reset_index(drop=True, inplace=True)
        return data

    @staticmethod
    def _get_n_header(file_location):
        print('Obtaining amount of skip rows.')
        n_skip = 0
        if file_location.endswith('.gz'):
            file_conn = gzip.open(file_location, 'rt')
        else:
            file_conn = open(file_location, 'rt')
        for line in file_conn:
            if line.strip().startswith('##'):
                n_skip += 1
            else:
                break
        file_conn.close()
        print(f'Total skip rows: {n_skip}')
        return n_skip

    @staticmethod
    def _obtain_gene(data):
        print('Obtaining gene.')
        data['gene'] = data['INFO'].str.split(
            'GENEINFO=', expand=True
        )[1].str.split(':', expand=True)[0]
        return data

    @staticmethod
    def _obtain_class(data):
        print('Obtaining class.')
        data['class'] = data['INFO'].str.split(
            'CLNSIG=', expand=True
        )[1].str.split(';', expand=True)[0]
        return data

    @staticmethod
    def _obtain_review(data):
        print('Obtaining review.')
        # Dict with Gold stars matching the ClinVar review status
        # Conflicting -1 because we dont want those
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

        # Isolating column
        data['review'] = data['INFO'].str.split(
            'CLNREVSTAT=', expand=True
        )[1].str.split(';', expand=True)[0]

        # Dropping uninteresting review status
        for status in data['review'].unique():
            if status not in stars.keys():
                warnings.warn(f'Found unknown review status: {status}')

        # Ensuring that mapping to Gold Stars values can be performed
        data.drop(index=data[~data['review'].isin(stars.keys())].index, inplace=True)

        # Mapping to Gold Stars values
        data['review'] = data['review'].map(stars)
        data['review'] = data['review'].astype(np.int64)

        # Droppin
        data.drop(data[data['review'] < 1].index, inplace=True)
        return data
