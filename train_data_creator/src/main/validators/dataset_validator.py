import pandas as pd


class DatasetValidator:
    def validate_vkgl(self, vkgl_dataset: pd.DataFrame):
        columns_specific_to_vkgl = ['consensus_classification', 'chromosome', 'start']
        self._validate_dataset(vkgl_dataset, columns_specific_to_vkgl, 'VKGL')

    def validate_clinvar(self, clinvar_dataset: pd.DataFrame):
        columns_specific_to_clinvar = ['#CHROM', 'POS', 'REF', 'ALT', 'INFO']
        self._validate_dataset(clinvar_dataset, columns_specific_to_clinvar, 'ClinVar')

    @staticmethod
    def _validate_dataset(dataset: pd.DataFrame, columns_required: list, data_source: str):
        for column in columns_required:
            if column not in dataset.columns:
                raise KeyError(
                    f'Input {data_source} dataset is not consensus, missing column: {column}'
                )
