#!/usr/bin/env python3

import argparse

import pandas as pd


class CommandLineParser:
    def __init__(self):
        parser = self._create_argument_parser()
        self.arguments = parser.parse_args()

    @staticmethod
    def _create_argument_parser():
        parser = argparse.ArgumentParser(
            prog='Compare models explain',
            description=''
        )
        required = parser.add_argument_group('Required arguments')

        required.add_argument(
            '-e1',
            '--explain_1',
            type=str,
            required=True,
            help=''
        )

        required.add_argument(
            '-e2',
            '--explain_2',
            type=str,
            required=True,
            help=''
        )

        required.add_argument(
            '-o',
            '--output',
            type=str,
            required=True,
            help=''
        )

        return parser

    def get_argument(self, argument_key):
        value = None
        if argument_key in self.arguments:
            value = getattr(self.arguments, argument_key)
        return value


def load_pandas_file(filepath):
    return pd.read_csv(filepath, sep='\t', compression='gzip')


def join_tables(table1: pd.DataFrame, table2: pd.DataFrame):
    return pd.merge(table1, table2, on='feature', how='outer', suffixes=['_e1', '_e2'])


def normalize_column(table: pd.DataFrame, column_name):
    """
    Adds a normalized column for given column_name directly after it within the table
    (so is not appended at the end!). New column uses format: <column_name>_normalized
    """
    column_index = table.columns.get_loc(column_name)
    normalized_values = (table[column_name] - table[column_name].mean()) / table[column_name].std()
    table.insert(column_index+1, column_name + '_normalized', normalized_values)
    return table


def add_column_ranking(table: pd.DataFrame, column_name):
    """
    Adds a normalized column for given column_name directly after it within the table
    (so is not appended at the end!). Original row order is maintained.
    New column uses format: <column_name>_rank
    """
    column_index = table.columns.get_loc(column_name)
    table.sort_values(by=column_name, ascending=False, inplace=True)
    table.insert(column_index+1, column_name + '_rank', range(1, table.shape[0]+1))
    table.sort_index(axis=0, inplace=True)
    return table


def process_table(table: pd.DataFrame):
    return add_column_ranking(
        normalize_column(table,
                         column_name='gain'),
        column_name='gain_normalized')


def reorder_columns(merged_table):
    """
    Ensures the "rank" columns appear directly after the feature column.
    """
    col_names = merged_table.columns
    front_columns = []
    other_columns = []
    for name in col_names[1:]:
        if "rank" in name:
            front_columns.append(name)
        else:
            other_columns.append(name)
    front_columns.sort()
    return merged_table.loc[:, [col_names[0], *front_columns, *other_columns]]


def main():
    parsed_args = CommandLineParser()

    merged_tables = reorder_columns(join_tables(
        process_table(load_pandas_file(parsed_args.get_argument('explain_1'))),
        process_table(load_pandas_file(parsed_args.get_argument('explain_2')))
    ))

    merged_tables.to_csv(parsed_args.get_argument('output'), sep='\t', compression='gzip',
                         index=False)


if __name__ == '__main__':
    main()
