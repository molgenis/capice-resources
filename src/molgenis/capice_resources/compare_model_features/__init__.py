from molgenis.capice_resources.core import ExtendedEnum


class CompareModelFeaturesEnum(ExtendedEnum):
    """
    Enum specific to Compare Model Features
    """
    FEATURE = 'feature'
    GAIN = 'gain'
    TOTAL_GAIN = 'total_gain'
    WEIGHT = 'weight'
    COVER = 'cover'
    TOTAL_COVER = 'total_cover'
