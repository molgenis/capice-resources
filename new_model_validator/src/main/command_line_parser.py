import argparse


class CommandLineParser:
    def __init__(self):
        parser = self._create_argument_parser()
        self.arguments = parser.parse_args()

    def _create_argument_parser(self):
        parser = argparse.ArgumentParser(
            prog='Compare models',
            description='Final stage of creating a new CAPICE models to see how the model performs'
                        'compared to the last generation of published CAPICE models.'
        )
        required = parser.add_argument_group('Required arguments')

        required.add_argument(
            '-i_old',
            '--input_old_model_data',
            nargs=1,
            type=str,
            required=True,
            help='The merged output validation data model of the old (last generation) published '
                 'CAPICE model. Merged with their true binarized labels and consequence.'
        )

        required.add_argument(
            '-i_new',
            '--input_new_model_data',
            nargs=1,
            type=str,
            required=True,
            help='The merged output validation data model of the new CAPICE model. '
                 'Merged with their true binarized labels and consequence.'
        )

        required.add_argument(
            '-o',
            '--output',
            nargs=1,
            type=str,
            required=True,
            help='The output directory of where the generated pictures should be placed.'
        )

        return parser

    def get_argument(self, argument):
        value = None
        if self.arguments is not None and argument in self.arguments:
            # Element 0 since the arguments are packed in a list
            value = getattr(self.arguments, argument)[0]
        return value
