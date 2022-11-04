import os
import matplotlib
import pandas as pd
from pathlib import PosixPath


class ThresholdExporter:
    def __init__(self, output_path: PosixPath):
        self.output_directory = output_path

    def export_thresholds(self, dataset: pd.DataFrame):
        dataset.to_csv(
            os.path.join(
                self.output_directory,
                'thresholds.tsv.gz'
            ),
            index=False,
            compression='gzip',
            sep='\t'
        )

    def export_plot(self, plot: matplotlib.figure):
        plot.savefig(
            os.path.join(
                self.output_directory,
                'threshold.png'
            )
        )
