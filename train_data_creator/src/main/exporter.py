import os
import pandas as pd


class Exporter:
    def __init__(self, output):
        self.output = output

    def export_validation_dataset(self, data: pd.DataFrame):
        self._export(data, dataset_type='validation')

    def export_train_test_dataset(self, data: pd.DataFrame):
        self._export(data, dataset_type='train_test')

    def _export(self, data: pd.DataFrame, dataset_type: str):
        export_loc = os.path.join(self.output, dataset_type+'.tsv.gz')
        data.to_csv(export_loc, sep='\t', index=False, compression='gzip')
        print(f'Export to {export_loc} successful.')
