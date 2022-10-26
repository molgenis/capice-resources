import pandas as pd


class DatasetValidator:
    def validate_vkgl(self, vkgl_dataset: pd.DataFrame):
        columns_specific_to_vkgl = ['classification', 'support', 'chromosome', 'start']
        self._validate_n_variants(vkgl_dataset, 'VKGL')
        self._validate_dataset(vkgl_dataset, columns_specific_to_vkgl, 'VKGL')

    def validate_clinvar(self, clinvar_dataset: pd.DataFrame):
        columns_specific_to_clinvar = ['#CHROM', 'POS', 'REF', 'ALT', 'INFO']
        self._validate_n_variants(clinvar_dataset, 'ClinVar')
        self._validate_dataset(clinvar_dataset, columns_specific_to_clinvar, 'ClinVar')

    @staticmethod
    def _validate_dataset(dataset: pd.DataFrame, columns_required: list, data_source: str):
        for column in columns_required:
            if column not in dataset.columns:
                raise KeyError(
                    f'Input {data_source} dataset is not consensus, missing column: {column}'
                )

    @staticmethod
    def _validate_n_variants(dataset: pd.DataFrame, data_source: str):
        if dataset.shape[0] == 0:
            raise EOFError(f'Data source {data_source} does not contain variants!')
