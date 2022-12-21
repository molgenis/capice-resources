from molgenis.capice_resources.core import ExtendedEnum


class CMPMinimalFeats(ExtendedEnum):
    GNOMAD_AF = 'gnomAD_AF'
    SCORE = 'score'


class CMPExtendedFeats(ExtendedEnum):
    CHR = 'chr'
    POS = 'pos'
    REF = 'ref'
    ALT = 'alt'
    GENE_NAME = 'gene_name'
    MERGE_COLUMN = 'merge_column'
