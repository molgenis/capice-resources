class SampleSizeMismatchError(Exception):
    """
    Error to be raised when a mismatch in sample size (pandas.DataFrame.shape[0]) occurs between
    2 datasets.
    """
    pass
