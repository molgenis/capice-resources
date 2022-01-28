import gc

import pandas as pd


class SplitDatasets:
    def __init__(self):
        self.frac = 0.5

    def split(self, data: pd.DataFrame):
        print('Splitting into validation and training.')
        pathogenic_set = data[data['binarized_label'] == 1]
        print(f'Amount of pathogenic variants:{pathogenic_set.shape[0]}')
        benign_set = data[data['binarized_label'] == 0]
        print(f'Amount of benign variants:{benign_set.shape[0]}')
        validation = pathogenic_set[pathogenic_set['sample_weight'] >= 0.9].sample(frac=self.frac)
        print(f'Sampled: {validation.shape[0]} high confidence pathogenic variants.')
        if benign_set[benign_set['sample_weight'] >= 0.9].shape[0] < validation.shape[0]:
            raise ValueError(
                f'Not enough benign variants to match pathogenic variants, unable to create '
                f'validation set.'
            )
        validation = validation.append(
            benign_set[
                benign_set['sample_weight'] >= 0.9].sample(n=validation.shape[0]), ignore_index=True
        )
        print(f'Validation dataset made, number of samples: {validation.shape[0]}')
        del pathogenic_set, benign_set
        gc.collect()

        # Creating train_test dataset
        train_test = data.copy(deep=True)
        train_test = train_test.append(validation, ignore_index=True)
        train_test.drop_duplicates(keep=False, inplace=True)
        print(f'Train dataset made, number of samples: {train_test.shape[0]}')

        return train_test, validation
