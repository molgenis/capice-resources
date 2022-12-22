from molgenis.capice_resources.core import ExtendedEnum, GlobalEnums


class TrainDataCreatorEnums(ExtendedEnum):
    CHROMOSOME = 'chromosome'
    CLASSIFICATION = 'classification'
    SUPPORT = 'support'
    START = 'start'
    CLASS = 'class'
    VKGL = 'VKGL'
    CLINVAR = 'CLINVAR'
    REVIEW = 'review'
    GENE = 'gene'

    @classmethod
    def columns_of_interest(cls):
        return [
            GlobalEnums.VCF_CHROM.value,
            GlobalEnums.POS.value,
            GlobalEnums.REF.value,
            GlobalEnums.ALT.value,
            TrainDataCreatorEnums.GENE.value,
            TrainDataCreatorEnums.CLASS.value,
            TrainDataCreatorEnums.REVIEW.value,
            GlobalEnums.DATASET_SOURCE.value
        ]
