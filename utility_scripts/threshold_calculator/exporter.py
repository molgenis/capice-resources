import pandas as pd


class ThresholdExporter:
    def __init__(self, dataset: pd.DataFrame):
        self.dataset = dataset

    def export(self, output_path: str):
        self.dataset.to_csv(output_path, index=False, compression='gzip', sep='\t')
