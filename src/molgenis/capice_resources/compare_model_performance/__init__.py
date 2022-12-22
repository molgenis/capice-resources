from molgenis.capice_resources.core import ExtendedEnum


class CMPMinimalFeats(ExtendedEnum):
    GNOMAD_AF = 'gnomAD_AF'


class CMPExtendedFeats(ExtendedEnum):
    CHR = 'chr'
    POS = 'pos'
    REF = 'ref'
    ALT = 'alt'
    GENE_NAME = 'gene_name'
    MERGE_COLUMN = 'merge_column'
    CONSEQUENCE = 'Consequence'
    SCORE_DIFF = 'score_diff'
    IMPUTED = 'is_imputed'
    MODEL_IDENTIFIER = 'model_identifier'


class PlottingEnums(ExtendedEnum):
    GLOBAL = 'Global'
    LOC = 'upper left'
    FIG_AUC = 'auc'
    FIG_ROC = 'roc'
    FIG_AF = 'allele_frequency'
    FIG_B_DIST = 'score_distributions_box'
    FIG_V_DIST = 'score_distributions_vio'
    FIG_V_DIFF = 'score_differences_vio'
    FIG_B_DIFF = 'score_differences_box'
