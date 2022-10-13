import argparse


class CommandLineParser:
    def __init__(self):
        parser = self._create_argument_parser()
        self.arguments = parser.parse_args()

    def _create_argument_parser(self):
        parser = argparse.ArgumentParser(
            prog='Calculate thresholds',
            description='Calculate thresholds based on Li et al. (2020), which is'
                        'based on a recall score between 94 to 96%.'
        )
        required = parser.add_argument_group('Required arguments')

        required.add_argument(
            '--validation',
            type=str,
            action='store',
            required=True,
            help='Input location of the initial validation dataset.'
        )

        required.add_argument(
            '--score_validation',
            type=str,
            action='store',
            required=True,
            help='Input location of the scores dataset.'
        )

        required.add_argument(
            '--output',
            type=str,
            action='store',
            required=True,
            help='Output path and filename to store the output recall score threshold tsv. '
                 'Has to have the .tsv.gz extension! Plot figure will also be placed in this directory.'
        )
        return parser

    def get_argument(self, argument_key):
        value = None
        if argument_key in self.arguments:
            value = getattr(self.arguments, argument_key)
        return value
