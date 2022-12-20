import argparse


class CommandLineInterface:
    def __init__(self):
        self.arguments = argparse.Namespace()

    @staticmethod
    def create_initial(program: str, description: str):
        """
        Creates an initial argparse.ArgumentParser() object with correctly set program and
        description.

        Args:
            program:
                String of the program name (such as process_vep).
            description:
                String of a somewhat larger description of what "program" is supposed to do.

        Returns:
            argparse.ArgumentParser:
                Initialized argparse.ArgumentParser() object ready for program specific arguments.
        """
        return argparse.ArgumentParser(prog=program, description=description)

    def parse_args(self, argument_parser: argparse.ArgumentParser) -> None:
        """
        Accepts the module specific argument parser argparse.ArgumentParser() object with set
        arguments that are required to run the program.

        Args:
            argument_parser:
                The argparse.ArgumentParser() object set with "program" specific arguments created
                from set_initial().
        """
        self.arguments = argument_parser.parse_args()

    def get_argument(self, argument_key: str) -> dict[str, object]:
        """
        Getter for the argparse.ArgumentParser() instance to get the value for a given argument_key.

        Args:
            argument_key:
                String of the long flag of the argument that you wish to get the value of.
        Returns:
            dict:
                Dictionary of {argument_key: argument_value}.
        """
        value = None
        if argument_key in self.arguments:
            value = getattr(self.arguments, argument_key)
        return {argument_key: value}
