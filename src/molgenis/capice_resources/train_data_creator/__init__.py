from enum import Enum

from molgenis.capice_resources.core import VCFEnums, ColumnEnums


class TrainDataCreatorEnums(Enum):
    """
    Enums specific to the Train Data Creator
    """
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
    def columns_of_interest(cls) -> list[str]:
        """
        Class method within the Enums to return a list of all Enums that are deemed interesting
        after parsing a data file such as the VKGL.

        Returns:
            list:
                List containing the Enums of: Chrom (including the # for VCF notation), Pos, Ref,
                Alt, Gene, Class(ification), Review score and the source of the data.
        """
        return [
            VCFEnums.CHROM.vcf_name,
            VCFEnums.POS.value,
            VCFEnums.REF.value,
            VCFEnums.ALT.value,
            TrainDataCreatorEnums.GENE.value,  # type: ignore
            TrainDataCreatorEnums.CLASS.value,  # type: ignore
            TrainDataCreatorEnums.REVIEW.value,  # type: ignore
            ColumnEnums.DATASET_SOURCE.value
        ]

    @classmethod
    def further_processing_columns(cls) -> list[str]:
        """
        Class method within the Enums to return a list of the Enums that are used to determine a
        unique variant.

        Returns:
            list:
                List containing the Enums of: Chrom (including the # for VCF notation), Pos, Ref,
                Alt and Gene.
        """
        return [
            VCFEnums.CHROM.vcf_name,
            VCFEnums.POS.value,
            VCFEnums.REF.value,
            VCFEnums.ALT.value,
            TrainDataCreatorEnums.GENE.value  # type: ignore
        ]
