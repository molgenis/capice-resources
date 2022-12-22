from molgenis.capice_resources.core import ExtendedEnum


class VEPFileEnum(ExtendedEnum):
    """
    Enum dedicated to columns that are already (should be) present in the VEP file.
    """
    GNOMAD_HN = 'gnomAD_HN'
    ID = 'ID'
    # TODO: merge VEPProccessingEnum and VEPFileEnum


class VEPProcessingEnum(ExtendedEnum):
    """
    Enum dedicated to columns created during the processing of the VEP file.
    """
    SAMPLE_WEIGHTS = [0.0, 1.0]


class CGDEnum(ExtendedEnum):
    """
    Enum dedicated to columns that are already (should be) present in the CGD file.
    """
    GENE = '#GENE'
    INHERITANCE = 'INHERITANCE'
