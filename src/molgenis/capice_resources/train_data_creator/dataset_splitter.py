import gc

import pandas as pd

from molgenis.capice_resources.core import ColumnEnums
from molgenis.capice_resources.utilities import merge_dataset_rows
from molgenis.capice_resources.train_data_creator.utilities import correct_order_vcf_notation


class SplitDatasets:
    FRACTION_TO_VALIDATION = 0.5
    HIGH_QUALITY_WEIGHT = 0.9

    def split(self, merged_frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Main splitting function of the train-test and validation datasets splitter.

        Samples self.frac percentage of high quality pathogenic variants, then samples an equal
        amount of benign samples.

        To then remove the random sampled variants from train-test, the indexes of the newly
        created validation dataframe are used to drop from the input merged_frame. train_test is
        copied because otherwise pandas might throw SettingWithCopy warnings.

        Args:
            merged_frame:
                The merged dataframe between VKGL and Clinvar of which a train-test and
                validation dataset should be made.

        Returns:
            tuple:
                Tuple containing the [0] train-test dataframe and [1] validation dataframe.
        """
        print('Splitting into validation and training.')
        pathogenic_set = merged_frame[merged_frame[ColumnEnums.BINARIZED_LABEL.value] == 1]
        print(f'Amount of pathogenic variants:{pathogenic_set.shape[0]}')
        benign_set = merged_frame[merged_frame[ColumnEnums.BINARIZED_LABEL.value] == 0]
        print(f'Amount of benign variants:{benign_set.shape[0]}')
        validation = pathogenic_set[
            pathogenic_set[ColumnEnums.SAMPLE_WEIGHT.value] >= self.HIGH_QUALITY_WEIGHT
            ].sample(frac=self.FRACTION_TO_VALIDATION)
        print(f'Sampled: {validation.shape[0]} high confidence pathogenic variants.')
        if benign_set[
            benign_set[ColumnEnums.SAMPLE_WEIGHT.value] >= self.HIGH_QUALITY_WEIGHT
        ].shape[0] < validation.shape[0]:
            raise ValueError(
                'Not enough benign variants to match pathogenic variants, unable to create '
                'validation set.'
            )
        validation = merge_dataset_rows(
            validation,
            benign_set[
                benign_set[ColumnEnums.SAMPLE_WEIGHT.value] >= self.HIGH_QUALITY_WEIGHT
                ].sample(n=validation.shape[0]),
            ignore_index=False
        )

        print(f'Validation dataset made, number of samples: {validation.shape[0]}')
        del pathogenic_set, benign_set
        gc.collect()

        # Creating train_test dataset
        train_test = merged_frame.copy(deep=True)
        train_test.drop(index=validation.index, inplace=True)
        validation.reset_index(drop=True, inplace=True)
        print(f'Train dataset made, number of samples: {train_test.shape[0]}')

        correct_order_vcf_notation(train_test)
        correct_order_vcf_notation(validation)

        return train_test, validation
