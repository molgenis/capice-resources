import os


class InputValidator:
    def validate_data(self, file_path):
        self._validate_file_exist(file_path)
        if not file_path.endswith('.tsv.gz'):
            raise FileNotFoundError(f'File {file_path} is not a pickled model file!')

    @staticmethod
    def validate_output(output_path):
        if not os.path.isdir(output_path):
            raise OSError('Given output argument is not a directory!')
        if not os.access(output_path, os.W_OK):
            raise OSError('Given output directory is not writable!')

    @staticmethod
    def _validate_file_exist(path):
        if not os.path.isfile(path):
            raise FileNotFoundError(f'File {path} not found!')
