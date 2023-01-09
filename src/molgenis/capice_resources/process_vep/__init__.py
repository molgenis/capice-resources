from molgenis.capice_resources.core import ExtendedEnum


class ProcessVEPEnums(ExtendedEnum):
    """
    Enums dedicated to the module Process VEP.
    """
    GNOMAD_HN = 'gnomAD_HN'
    SAMPLE_WEIGHTS = [0.8, 0.9, 1.0]


class CGDEnum(ExtendedEnum):
    """
    Enum dedicated to columns that are already (should be) present in the CGD file.
    """
    GENE = '#GENE'
    INHERITANCE = 'INHERITANCE'
