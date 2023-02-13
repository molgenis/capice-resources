from pathlib import Path

import pandas as pd


class Exporter:
    def __init__(self, pandas_sep_flag: str):
        # Required this way otherwise it is going to be a circular import
        self.sep = pandas_sep_flag

    def export_pandas_file(self, path: Path, pandas_object: pd.DataFrame, **kwars) -> None:
        """
        Primary exporting function of capice-resources.

        Args:
            path:
                Full pathlike object, including the absolute path and the filename of the output.
                Filename should include either ".tsv.gz" or ".tsv", as the separator is set to \t.
            pandas_object:
                The pandas.DataFrame that should be exported to path.
            **kwars:
                Additional arguments to be supplied to pandas.DataFrame.to_csv(). Should not
                include: path_or_buff, sep or index.

        """
        pandas_object.to_csv(path, sep=self.sep, index=False, **kwars)
