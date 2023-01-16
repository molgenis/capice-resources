from molgenis.capice_resources.core import ExtendedEnum


class CompareModelPerformanceEnums(ExtendedEnum):
    """
    Enums specific to CompareModelPerformance, not including the enums that are specific to
    plotting the actual performance.
    """
    CHR = 'chr'
    GENE_NAME = 'gene_name'
    MERGE_COLUMN = 'merge_column'
    SCORE_DIFF = 'score_diff'
    IMPUTED = 'is_imputed'
    MODEL_IDENTIFIER = 'model_identifier'
    MODEL_1 = 'model_1'
    MODEL_2 = 'model_2'


class PlottingEnums(ExtendedEnum):
    """
    Enums specific to the plotting process of CompareModelPerformance.
    """
    GLOBAL = 'Global'
    LOC = 'upper left'
    FIG_AUC = 'auc'
    FIG_ROC = 'roc'
    FIG_AF = 'allele_frequency'
    FIG_B_DIST = 'score_distributions_box'
    FIG_V_DIST = 'score_distributions_vio'
    FIG_V_DIFF = 'score_differences_vio'
    FIG_B_DIFF = 'score_differences_box'
