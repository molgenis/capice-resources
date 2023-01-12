from argparse import ArgumentParser

import pandas as pd

from molgenis.capice_resources.core import Module, CommandLineInterface
from molgenis.capice_resources.core import GlobalEnums as Genums


class BalanceDataset(Module):
    def __init__(self):
        super(BalanceDataset, self).__init__(
            program='Balance dataset',
            description='foobar'
        )

    @staticmethod
    def _create_module_specific_arguments(parser: ArgumentParser) -> ArgumentParser:
        pass

    def _validate_module_specific_arguments(self, parser: CommandLineInterface) -> dict[
        str, str | object]:
        pass

    def run_module(self, arguments: dict[str, str | object]) -> dict:
        pass

    def export(self, output: dict[object, object]) -> None:
        pass


def main():
    BalanceDataset().run()


if __name__ == '__main__':
    main()
