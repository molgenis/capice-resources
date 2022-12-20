from pathlib import Path

import pandas as pd


class Exporter:
    @staticmethod
    def export_pandas_file(path: Path, pandas_object: pd.DataFrame) -> None:
        pandas_object.to_csv(path, sep='\t', index=False)
