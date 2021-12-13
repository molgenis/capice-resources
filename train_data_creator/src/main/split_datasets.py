import gc

import pandas as pd


class SplitDatasets:
    def __init__(self):
        self.frac = 0.2

    def split(self, data: pd.DataFrame):
        print('Splitting into validation and training.')
        pathogenic_set = data[data['binarized_label'] > 0]
        benign_set = data[data['binarized_label'] < 1]
        validation = pathogenic_set[
            (pathogenic_set['review'] >= 2) | (pathogenic_set['source'] == 'VKGL')
            ].sample(frac=self.frac)
        validation = validation.append(
            benign_set[
                (benign_set['review'] >= 2) | (benign_set['source'] == 'VKGL')
                ].sample(n=validation.shape[0]), ignore_index=True
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
