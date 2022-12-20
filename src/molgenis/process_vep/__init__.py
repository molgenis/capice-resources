from molgenis.core import ExtendedEnum


class VEPEnum(ExtendedEnum):
    GNOMAD_HN = 'gnomAD_HN'
    SYMBOL = 'SYMBOL'
    ID = 'ID'
    CHROM = 'CHROM'


class VEPProcessingEnum(VEPEnum):
    BINARIZED_LABEL = 'binarized_label'
    SAMPLE_WEIGHT = 'sample_weight'
    SOURCE = 'dataset_source'
    SAMPLE_WEIGHTS = [0.0, 1.0]
    TRAIN_TEST = 'train_test'
    VALIDATION = 'validation'


class CGDEnum(ExtendedEnum):
    GENE = '#GENE'
    INHERITANCE = 'INHERITANCE'
