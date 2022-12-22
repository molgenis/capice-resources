import pandas as pd

from molgenis.capice_resources.core import GlobalEnums
from molgenis.capice_resources.train_data_creator import TrainDataCreatorEnums
from molgenis.capice_resources.train_data_creator.utilities import correct_order_vcf_notation, \
    apply_binarized_label


class VKGLParser:
    def parse(self, vkgl_frame: pd.DataFrame) -> pd.DataFrame:
        self._correct_column_names(vkgl_frame)
        self._correct_support(vkgl_frame)
        correct_order_vcf_notation(vkgl_frame)
        self._apply_review_status(vkgl_frame)
        self._apply_dataset_source(vkgl_frame)
        vkgl_frame = vkgl_frame[TrainDataCreatorEnums.columns_of_interest()]
        apply_binarized_label(vkgl_frame)
        return vkgl_frame

    @staticmethod
    def _correct_column_names(vkgl_frame) -> None:
        vkgl_frame.rename(
            columns={
                TrainDataCreatorEnums.CHROMOSOME.value: GlobalEnums.VCF_CHROM.value,
                TrainDataCreatorEnums.START.value: GlobalEnums.POS.value,
                GlobalEnums.REF.value.lower(): GlobalEnums.REF.value,
                GlobalEnums.ALT.value.lower(): GlobalEnums.ALT.value,
                TrainDataCreatorEnums.CLASSIFICATION.value: TrainDataCreatorEnums.CLASS.value
            }, inplace=True
        )

    @staticmethod
    def _correct_support(vkgl_frame) -> None:
        vkgl_frame[TrainDataCreatorEnums.SUPPORT.value] = vkgl_frame[
            TrainDataCreatorEnums.SUPPORT.value
        ].str.split(' ', expand=True)[0].astype(int)

    @staticmethod
    def _apply_review_status(vkgl_frame) -> None:
        vkgl_frame[TrainDataCreatorEnums.REVIEW.value] = 2
        vkgl_frame.loc[
            vkgl_frame[vkgl_frame[TrainDataCreatorEnums.SUPPORT.value] == 1].index,
            TrainDataCreatorEnums.REVIEW.value
        ] = 1

    @staticmethod
    def _apply_dataset_source(vkgl_frame) -> None:
        vkgl_frame[GlobalEnums.DATASET_SOURCE.value] = TrainDataCreatorEnums.VKGL.value
