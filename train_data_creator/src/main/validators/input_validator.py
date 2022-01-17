import os
from pathlib import Path


class InputValidator:
    def validate_vkgl(self, input_path):
        self._validate_file_exist(input_path, 'VKGL')
        if not input_path.endswith(('.tsv.gz', '.tsv')):
            raise FileNotFoundError('Input VKGL is not a (gzipped) tsv!')

    def validate_clinvar(self, input_path):
        self._validate_file_exist(input_path, 'ClinVar')
        if not input_path.endswith(('.vcf', '.vcf.gz')):
            raise FileNotFoundError('Input ClinVar is not a (gzipped) vcf!')

    @staticmethod
    def _validate_file_exist(input_path, file_type):
        if not os.path.isfile(input_path):
            raise FileNotFoundError(f'Input for {file_type}: {input_path} is not a file!')

    @staticmethod
    def validate_output(output_path):
        makedir = False
        if not os.path.isdir(output_path):
            path_parent = str(Path(output_path).parent)
            if not os.path.isdir(path_parent):
                raise OSError(f'Output {output_path} cannot be made because parent does not exist!')
            elif not os.access(path_parent, os.W_OK):
                raise OSError(f'Output path {output_path} is not writable!')
            else:
                makedir = True
        if makedir:
            os.makedirs(output_path)
        return output_path
