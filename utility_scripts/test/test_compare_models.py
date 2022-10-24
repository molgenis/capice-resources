import unittest

import pandas as pd
import utility_scripts.compare_models as compare


class TestCompareModelsExplain(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame(data={
            'score': [0.000013, 0.097279, 0.000550, 0.007370],
            'Consequence': ['synonymous_variant', 'missense_variant', 'synonymous_variant',
                            'intron_variant'],
            'binarized_label': [1.0, 1.0, 0.0, 1.0]
        })

    def test_validator_validate_score_files_length_valid(self):
        """
        df2 is equal in both total length & size per consequence, so should not cause any errors.
        """
        df2 = pd.DataFrame(data={
            'score': [0.000154, 0.086213, 0.008621, 0.006832],
            'Consequence': ['synonymous_variant', 'missense_variant', 'synonymous_variant',
                            'intron_variant'],
            'binarized_label': [1.0, 1.0, 0.0, 1.0]
        })
        compare.Validator.validate_score_files_length(self.df, df2, per_consequence=True)

    def test_validator_validate_score_files_length_invalid(self):
        """
        Per-consequence check is turned on & 1 of the synonymous_variant was changed into
        missense_variant, so an error should be thrown that both these column counts are unequal.
        """
        df2 = pd.DataFrame(data={
            'score': [0.000154, 0.086213, 0.008621, 0.006832],
            'Consequence': ['synonymous_variant', 'missense_variant', 'missense_variant',
                            'intron_variant'],
            'binarized_label': [1.0, 1.0, 0.0, 1.0]
        })

        with self.assertWarns(UserWarning) as context:
            compare.Validator.validate_score_files_length(self.df, df2, per_consequence=True)
        msg = "The score files contain a different number of variants for the consequences: " \
              "['missense_variant', 'synonymous_variant']"
        self.assertEqual(str(context.warning), msg)

    def test_validator_validate_score_files_length_invalid_ignore_consequence(self):
        """
        While df2 has differing consequence, as per consequence check is turned off does not
        cause an error.
        """
        df2 = pd.DataFrame(data={
            'score': [0.000154, 0.086213, 0.008621, 0.006832],
            'Consequence': ['synonymous_variant', 'missense_variant', 'missense_variant',
                            'intron_variant'],
            'binarized_label': [1.0, 1.0, 0.0, 1.0]
        })

        compare.Validator.validate_score_files_length(self.df, df2, per_consequence=False)

    def test_validator_validate_score_files_length_invalid_total_length(self):
        """
        Total length differs so should always throw an error. If per consequence is True,
        the total length error should take priority over any consequence-specific validation.
        """
        df2 = pd.DataFrame(data={
            'score': [0.000154, 0.086213, 0.008621],
            'Consequence': ['synonymous_variant', 'missense_variant', 'missense_variant'],
            'binarized_label': [1.0, 1.0, 0.0]
        })

        with self.assertWarns(UserWarning) as context:
            compare.Validator.validate_score_files_length(self.df, df2, per_consequence=True)
        msg = "The score files contain a different number of variants."
        self.assertEqual(str(context.warning), msg)
