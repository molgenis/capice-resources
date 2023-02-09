import os
from pathlib import Path


def get_testing_resources_dir() -> Path:
    """
    Utility function for tests to obtain the path to the tests/resources.

    Returns:
        path:
            Absolute pathlib.Path object of the tests/resources directory.
    """
    return Path(os.path.join(Path(__file__).absolute().parent.parent.parent, 'resources'))


def temp_output_file_path_and_name() -> Path:
    """
    Utility function to get the absolute path and filename to any temporary export TSV created in
    tests.

    Returns:
        path:
            Absolute path of get_testing_resources_dir() including a temporary file name.
    """
    return Path(os.path.join(get_testing_resources_dir(), 'temporary_file.tsv.gz'))


def check_and_remove_directory(path: str | Path | os.PathLike) -> None:
    """
    Utility function to check if a directory (or file) exists and if so, remove it.
    """
    if os.path.exists(path):
        if os.path.isdir(path):
            os.rmdir(path)
        else:
            os.remove(path)
