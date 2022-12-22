import pandas as pd

from molgenis.capice_resources.core import GlobalEnums
from molgenis.capice_resources.train_data_creator import TrainDataCreatorEnums


class VKGLParser:
    def parse(self, vkgl_frame: pd.DataFrame) -> None:
        self._correct_column_names(vkgl_frame)

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
