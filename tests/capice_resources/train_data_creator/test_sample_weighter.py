import unittest

import numpy as np
import pandas as pd

from molgenis.capice_resources.core import GlobalEnums as Genums
from molgenis.capice_resources.train_data_creator import TrainDataCreatorEnums as Menums
from molgenis.capice_resources.train_data_creator.sample_weighter import SampleWeighter


class TestSampleWeighter(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.weighter = SampleWeighter()  # type: ignore

    def test_sample_weighter(self):
        """
        Tests proper function of the SampleWeighter in a very simple condition.
        """
        dataset = pd.DataFrame(
            {
                Menums.REVIEW.value: [3, 4, 1, 2]
            }
        )
        self.weighter.apply_sample_weight(dataset)
        self.assertIn(Genums.SAMPLE_WEIGHT.value, dataset.columns)
        self.assertListEqual(
            list(dataset[Genums.SAMPLE_WEIGHT.value].values),
            [1.0, 1.0, 0.8, 0.9]
        )

    def test_sample_weighter_unknown_score(self):
        """
        Tests proper function of the SampleWeighter when "unknown" review scores are present.
        """
        dataset = pd.DataFrame(
            {
                Menums.REVIEW.value: [3, 4, 5, 0]
            }
        )
        self.weighter.apply_sample_weight(dataset)
        self.assertIn(Genums.SAMPLE_WEIGHT.value, dataset.columns)
        np.testing.assert_array_equal(
            dataset[Genums.SAMPLE_WEIGHT.value],
            np.array([1.0, 1.0, np.nan, np.nan])
        )


if __name__ == '__main__':
    unittest.main()
