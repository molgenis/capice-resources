import pandas as pd

from molgenis.capice_resources.core import GlobalEnums as Genums
from molgenis.capice_resources.utilities import split_consequences
from molgenis.capice_resources.balance_dataset import BalanceDatasetEnums as Menums
from molgenis.capice_resources.balance_dataset.verbosity_printer import VerbosityPrinter


class Balancer:
    def __init__(self, verbose: bool):
        self.printer = VerbosityPrinter(verbose)
        self.bins = [pd.IntervalIndex]
        self.columns = []
        self.drop_benign = pd.Index([])
        self.drop_pathogenic = pd.Index([])

    @staticmethod
    def _mark_and_impute(dataset: pd.DataFrame) -> None:
        dataset[Genums.IMPUTED.value] = 0
        dataset.loc[dataset[Genums.GNOMAD_AF.value].isnull(), Genums.IMPUTED.value] = 1
        dataset[Genums.GNOMAD_AF.value].fillna(0, inplace=True)

    @staticmethod
    def _reset_impute(dataset: pd.DataFrame) -> None:
        dataset.loc[dataset[Genums.IMPUTED.value] == 1, Genums.IMPUTED.value] = None
        dataset.drop(columns=[Genums.IMPUTED.value], inplace=True)

    def _set_bins(self, gnomad_af: pd.Series) -> None:
        self.bins = pd.cut(
                gnomad_af,
                bins=Genums.AF_BINS.value,
                right=False,
                include_lowest=True
            ).dropna().unique()
        self.printer.print(f'Bins set: {self.bins}')

    def _set_columns(self, columns: pd.DataFrame.columns):
        self.columns = columns.append(pd.Index([Menums.BALANCED_ON.value]))

    def balance(self, dataset: pd.DataFrame):
        self._set_columns(dataset.columns)
        self._mark_and_impute(dataset)
        self._set_bins(dataset[Genums.GNOMAD_AF.value])
        pathogenic = dataset.loc[dataset[dataset[Genums.BINARIZED_LABEL.value] == 1].index, :]
        benign = dataset.loc[dataset[dataset[Genums.BINARIZED_LABEL.value] == 0].index, :]
        return_dataset = pd.DataFrame(columns=self.columns)
        consequences = split_consequences(dataset[Genums.CONSEQUENCE.value])
        return None, None
