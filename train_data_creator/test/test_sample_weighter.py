import unittest

import numpy as np
import pandas as pd

from src.main.sample_weighter import SampleWeighter


class TestSampleWeighter(unittest.TestCase):
    def test_sample_weighter(self):
        dataset = pd.DataFrame(
            {
                'review': [3, 4, 1, 2]
            }
        )
        copy_dataset = dataset.copy(deep=True)
        observed = SampleWeighter().apply_sample_weight(dataset)
        expected = pd.concat(
            [
                copy_dataset,
                pd.DataFrame(
                    {
                        'sample_weight': [1.0, 1.0, 0.8, 0.9]
                    }
                )
            ], axis=1
        )
        pd.testing.assert_frame_equal(observed, expected)


if __name__ == '__main__':
    unittest.main()
