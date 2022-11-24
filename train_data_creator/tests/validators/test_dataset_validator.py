import os
import unittest

import pandas as pd

from train_data_creator.tests import get_project_root_dir
from train_data_creator.src.main.validators.dataset_validator import DatasetValidator


class TestDatasetValidator(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.vkgl = pd.read_csv(
            os.path.join(get_project_root_dir(), 'tests', 'resources', 'smol_vkgl.tsv.gz'),
            sep='\t'
        )
        cls.clinvar = pd.read_csv(
            os.path.join(get_project_root_dir(), 'tests', 'resources', 'smol_clinvar.vcf.gz'),
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
            self.vkgl.rename(columns={'classification': 'consensus_classification'})
        )

    def test_validate_clinvar_incorr(self):
        # Mimicking what happens when the amount of comment lines are incorrect.
        self.assertRaises(
            KeyError,
            self.validator.validate_clinvar,
            self.clinvar.rename(columns={'#CHROM': 'chr', 'INFO': 'something_not_info'})
        )

    def test_raise_no_variants(self):
        # No variants in the file raise EOFError
        vkgl_novars = pd.read_csv(
            os.path.join(get_project_root_dir(), 'tests', 'resources', 'smol_vkgl_novars.tsv.gz')
        )
        self.assertRaises(
            EOFError,
            self.validator.validate_vkgl,
            vkgl_novars
        )


if __name__ == '__main__':
    unittest.main()
