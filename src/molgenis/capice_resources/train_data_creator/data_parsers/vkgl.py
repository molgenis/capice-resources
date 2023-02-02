import numpy as np
import pandas as pd

from molgenis.capice_resources.core import VCFEnums
from molgenis.capice_resources.utilities import add_dataset_source
from molgenis.capice_resources.train_data_creator import TrainDataCreatorEnums as Menums
from molgenis.capice_resources.train_data_creator.utilities import correct_order_vcf_notation, \
    apply_binarized_label


class VKGLParser:
    def parse(self, vkgl_frame: pd.DataFrame) -> pd.DataFrame:
        """
        Main parsing function of the VKGL data parser.

        Args:
            vkgl_frame:
                The loaded in dataframe of the VKGL tsv.

        Returns:
            frame:
                Fully parsed and processed VKGL dataframe, adhering to all the standard
                columns and equalized to ClinVar.
        """
        self._correct_column_names(vkgl_frame)
        self._correct_support(vkgl_frame)
        correct_order_vcf_notation(vkgl_frame)
        self._apply_review_status(vkgl_frame)
        add_dataset_source(vkgl_frame, Menums.VKGL.value)  # type: ignore
        vkgl_frame_interest = vkgl_frame.loc[:, Menums.columns_of_interest()]
        del vkgl_frame  # freeing up memory
        apply_binarized_label(vkgl_frame_interest)
        return vkgl_frame_interest

    @staticmethod
    def _correct_column_names(vkgl_frame: pd.DataFrame) -> None:
        """
        Function to rename and equalize the column names of VKGL data.

        Args:
            vkgl_frame:
                The VKGL dataframe.
                Performed inplace.

        """
        vkgl_frame.rename(  # type: ignore
            columns={
                Menums.CHROMOSOME.value: VCFEnums.VCF_CHROM.value,
                Menums.START.value: VCFEnums.POS.value,
                VCFEnums.REF.value.lower(): VCFEnums.REF.value,
                VCFEnums.ALT.value.lower(): VCFEnums.ALT.value,
                Menums.CLASSIFICATION.value: Menums.CLASS.value
            }, inplace=True
        )

    @staticmethod
    def _correct_support(vkgl_frame) -> None:
        """
        Method to correct the VKGL support (thus by proxy review) column.

        Args:
            vkgl_frame:
                The VKGL dataframe.
                Performed inplace.

        """
        vkgl_frame[Menums.SUPPORT.value] = vkgl_frame[
            Menums.SUPPORT.value
        ].str.split(' ', expand=True)[0].astype(np.int64)

    @staticmethod
    def _apply_review_status(vkgl_frame) -> None:
        """
        Method to apply the review status to VKGL samples.

        Applies review status 1 for single consensi, 2 for multiple consensi.

        Args:
            vkgl_frame:
                The VKGL dataframe.
                Performed inaplace.

        """
        vkgl_frame[Menums.REVIEW.value] = 2
        vkgl_frame.loc[
            vkgl_frame[vkgl_frame[Menums.SUPPORT.value] == 1].index,
            Menums.REVIEW.value
        ] = 1
