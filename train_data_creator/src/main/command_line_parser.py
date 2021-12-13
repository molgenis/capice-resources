import argparse


class CommandLineParser:
    def __init__(self):
        parser = self._create_argument_parser()
        self.arguments = parser.parse_args()

    def _create_argument_parser(self):
        parser = argparse.ArgumentParser(
            prog='CAPICE-resources',
            description='Resource files for CAPICE to train new CAPICE models'
        )
        required = parser.add_argument_group('Required arguments')

        required.add_argument(
            '-iv',
            '--input_vkgl',
            nargs=1,
            type=str,
            required=True,
            help='Input location of the VKGL dataset (consensus, not public)'
        )
        required.add_argument(
            '-ic',
            '--input_clinvar',
            nargs=1,
            type=str,
            required=True,
            help='Input location of the ClinVar dataset.'
        )
        required.add_argument(
            '-o',
            '--output',
            nargs=1,
            type=str,
            required=True,
            help='Output directory where the files should be placed.'
        )
        return parser

    def get_argument(self, argument_key):
        value = None
        if self.arguments is not None and argument_key in self.arguments:
            value = getattr(self.arguments, argument_key)
        return value
