import pandas as pd


class DuplicateProcessor:
    @staticmethod
    def process(data: pd.DataFrame):
        print('Dropping duplicates.')
        data.drop_duplicates(
            subset=['#CHROM', 'POS', 'REF', 'ALT', 'gene', 'class'], inplace=True
        )
        return data
