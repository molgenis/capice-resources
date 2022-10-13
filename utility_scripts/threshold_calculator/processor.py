from validator import Validator


class DataMerger:
    @staticmethod
    def merge(dataset_1, dataset_2):
        Validator.validate_sample_size_match(dataset_1, dataset_2)

