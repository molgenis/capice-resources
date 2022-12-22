import pandas as pd

from molgenis.capice_resources.core import GlobalEnums


class ProgressPrinter:
    def __init__(self):
        self.grouped_save = None

    def set_initial_size(self, dataset: pd.DataFrame):
        self.grouped_save = dataset.groupby(GlobalEnums.DATASET_SOURCE.value).size()

    def new_shape(self, dataset: pd.DataFrame):
        new_save = dataset.groupby(GlobalEnums.DATASET_SOURCE.value).size()
        dropped = self.grouped_save - new_save
        for group, counts in zip(dropped.index, dropped.values):
            print(f'Dropped {counts} variants from {group}')
        self.grouped_save = new_save

    def print_final_shape(self):
        for group, counts in zip(self.grouped_save.index, self.grouped_save.values):
            print(f'Final number of samples in {group}: {counts}')
