import pandas as pd


class SampleWeighter:
    @staticmethod
    def apply_sample_weight(dataset: pd.DataFrame):
        print('Applying sample weights')
        sample_weights = {
            4: 1.0,
            3: 1.0,
            2: 0.9,
            1: 0.8
        }
        dataset['sample_weight'] = dataset['review'].map(sample_weights)
        return dataset
