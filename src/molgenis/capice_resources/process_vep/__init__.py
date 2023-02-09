from enum import Enum


class ProcessVEPEnums(Enum):
    """
    Enums dedicated to the module Process VEP.
    """
    GNOMAD_HN = 'gnomAD_HN'
    SAMPLE_WEIGHTS = [0.8, 0.9, 1.0]


class CGDColumnEnums(Enum):
    """
    Enum dedicated to columns that are already (should be) present in the CGD file.
    """
    GENE = '#GENE'
    INHERITANCE = 'INHERITANCE'
