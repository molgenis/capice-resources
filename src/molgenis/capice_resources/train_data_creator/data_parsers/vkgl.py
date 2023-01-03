import pandas as pd

from molgenis.capice_resources.core import add_dataset_source
from molgenis.capice_resources.core import GlobalEnums as Genums
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
        add_dataset_source(vkgl_frame, Menums.VKGL.value)
        vkgl_frame = vkgl_frame[Menums.columns_of_interest()]
        apply_binarized_label(vkgl_frame)
        return vkgl_frame

    @staticmethod
    def _correct_column_names(vkgl_frame: pd.DataFrame) -> None:
        """
        Function to rename and equalize the column names of VKGL data.

        Args:
            vkgl_frame:
                The VKGL dataframe.
                Performed inplace.

        """
        vkgl_frame.rename(
            columns={
                Menums.CHROMOSOME.value: Genums.VCF_CHROM.value,
                Menums.START.value: Genums.POS.value,
                Genums.REF.value.lower(): Genums.REF.value,
                Genums.ALT.value.lower(): Genums.ALT.value,
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
        ].str.split(' ', expand=True)[0].astype(int)

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
