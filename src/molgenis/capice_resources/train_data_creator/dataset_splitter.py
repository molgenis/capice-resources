import gc

import pandas as pd

from molgenis.capice_resources.core import GlobalEnums
from molgenis.capice_resources.utilities import merge_dataset_rows


class SplitDatasets:
    def __init__(self):
        self.frac = 0.5

    def split(self, merged_frame: pd.DataFrame):
        print('Splitting into validation and training.')
        pathogenic_set = merged_frame[merged_frame[GlobalEnums.BINARIZED_LABEL.value] == 1]
        print(f'Amount of pathogenic variants:{pathogenic_set.shape[0]}')
        benign_set = merged_frame[merged_frame[GlobalEnums.BINARIZED_LABEL.value] == 0]
        print(f'Amount of benign variants:{benign_set.shape[0]}')
        validation = pathogenic_set[
            pathogenic_set[GlobalEnums.SAMPLE_WEIGHT.value] >= 0.9
            ].sample(frac=self.frac)
        print(f'Sampled: {validation.shape[0]} high confidence pathogenic variants.')
        if benign_set[
            benign_set[GlobalEnums.SAMPLE_WEIGHT.value] >= 0.9
        ].shape[0] < validation.shape[0]:
            raise ValueError(
                f'Not enough benign variants to match pathogenic variants, unable to create '
                f'validation set.'
            )
        validation = merge_dataset_rows(
            validation,
            benign_set[
                benign_set[GlobalEnums.SAMPLE_WEIGHT.value] >= 0.9
                ].sample(n=validation.shape[0])
        )

        print(f'Validation dataset made, number of samples: {validation.shape[0]}')
        del pathogenic_set, benign_set
        gc.collect()

        # Creating train_test dataset
        train_test = merged_frame.copy(deep=True)
        train_test = merge_dataset_rows(train_test, validation)
        train_test.drop_duplicates(keep=False, inplace=True)
        print(f'Train dataset made, number of samples: {train_test.shape[0]}')

        return train_test, validation
