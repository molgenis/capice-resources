class VerbosityPrinter:
    def __init__(self, verbose: bool = False):
        """
        Class to house the default "print" statement of Python,
        with account to the CLI "verbose" flag.

        Args:
            verbose:
                Boolean for verbose printing (True) or not (False).
        """
        self.verbose = verbose

    def print(self, message, *args, **kwargs):
        """
        The default Python print statement, taking into account the verbose boolean when
        initializing.
        """
        if self.verbose:
            print(message, *args, **kwargs)
