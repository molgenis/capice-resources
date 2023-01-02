import pandas as pd

from molgenis.capice_resources.core import GlobalEnums as Genums


class ProgressPrinter:
    def __init__(self, dataset: pd.DataFrame):
        """
        Class to house the ProgressPrinter to backtrack how many samples have been filtered out
        with each processing step.

        After initialization, ProgressPrinter().new_shape()
        should be called to update the sample size of each of the dataset sources.

        Args:
            dataset:
                Merged dataset containing both train-test and validation.
                Should also contain the dataset source column.
        """
        self.grouped_save = dataset.groupby(Genums.DATASET_SOURCE.value).size()

    def new_shape(self, dataset: pd.DataFrame):
        """
        Method to set a new sample size for each of the dataset sources.

        Args:
            dataset:
                Merged dataset containing both train-test and validation. Should be called after
                each of the processing steps.

        """
        new_save = dataset.groupby(Genums.DATASET_SOURCE.value).size()
        dropped = self.grouped_save - new_save
        for group, counts in zip(dropped.index, dropped.values):
            print(f'Dropped {counts} variants from {group}')
        self.grouped_save = new_save

    def print_final_shape(self):
        """
        Method to print out the final sample sizes of each of the dataset sources.
        """
        for group, counts in zip(self.grouped_save.index, self.grouped_save.values):
            print(f'Final number of samples in {group}: {counts}')
