from molgenis.core import ExtendedEnum


class VEPFileEnum(ExtendedEnum):
    """
    Enum dedicated to columns that are already (should be) present in the VEP file.
    """
    GNOMAD_HN = 'gnomAD_HN'
    SYMBOL = 'SYMBOL'
    ID = 'ID'
    CHROM = 'CHROM'


class VEPProcessingEnum(ExtendedEnum):
    """
    Enum dedicated to columns created during the processing of the VEP file.
    """
    BINARIZED_LABEL = 'binarized_label'
    SAMPLE_WEIGHT = 'sample_weight'
    SOURCE = 'dataset_source'
    SAMPLE_WEIGHTS = [0.0, 1.0]
    TRAIN_TEST = 'train_test'
    VALIDATION = 'validation'


class CGDEnum(ExtendedEnum):
    """
    Enum dedicated to columns that are already (should be) present in the CGD file.
    """
    GENE = '#GENE'
    INHERITANCE = 'INHERITANCE'
