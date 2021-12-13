import os
import unittest

import pandas as pd

from train_data_creator.src.main.utilities import project_root_dir
from train_data_creator.src.main.validators.dataset_validator import DatasetValidator


class TestDatasetValidator(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.vkgl = pd.read_csv(
            os.path.join(project_root_dir, 'test', 'resources', 'smol_vkgl.tsv.gz'),
            sep='\t'
        )
        cls.clinvar = pd.read_csv(
            os.path.join(project_root_dir, 'test', 'resources', 'smol_clinvar.vcf.gz'),
            sep='\t',
            skiprows=27
        )
        cls.validator = DatasetValidator()

    def test_validate_vkgl_corr(self):
        self.validator.validate_vkgl(self.vkgl)

    def test_validate_clinvar_corr(self):
        self.validator.validate_clinvar(self.clinvar)

    def test_validate_vkgl_incorr(self):
        # Mimicking what happens when the public consensus is used.
        self.assertRaises(
            KeyError,
            self.validator.validate_vkgl,
            self.vkgl.rename(columns={'consensus_classification': 'classification'})
        )

    def test_validate_clinvar_incorr(self):
        # Mimicking what happens when the amount of comment lines are incorrect.
        self.assertRaises(
            KeyError,
            self.validator.validate_clinvar,
            pd.read_csv(
                os.path.join(project_root_dir, 'test', 'resources', 'smol_clinvar.vcf.gz'),
                sep='\t',
                skiprows=26
            )
        )


if __name__ == '__main__':
    unittest.main()
