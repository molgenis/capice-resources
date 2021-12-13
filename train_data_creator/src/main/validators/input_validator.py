import os


class InputValidator:
    def validate_vkgl(self, input_path):
        self._validate_file_exist(input_path, 'VKGL')
        if not input_path.endswith('.tsv.gz'):
            raise FileNotFoundError('Input VKGL is not the gzipped consensus tsv!')

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
        if not os.path.isdir(output_path):
            raise OSError('Given output path does not exist!')
        if not os.access(output_path, os.W_OK):
            raise OSError('Output path is not writable!')
