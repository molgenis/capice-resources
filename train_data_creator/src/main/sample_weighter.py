import pandas as pd


class SampleWeighter:
    @staticmethod
    def apply_sample_weight(dataset: pd.DataFrame):
        sample_weights = {
            4: 1.0,
            3: 0.9,
            2: 0.8,
            1: 0.6,
            0: 0.2
        }
        dataset['sample_weight'] = dataset['review'].map(sample_weights)
        return dataset
