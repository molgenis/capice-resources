import unittest

import pandas as pd

from molgenis.capice_resources.compare_model_performance.consequence_tools import ConsequenceTools


class TestCompareModelsExplain(unittest.TestCase):
    def setUp(self):
        self.consequences = ['synonymous_variant', 'missense_variant', 'synonymous_variant',
                            'intron_variant']
        self.df = pd.DataFrame(data={
            'score': [0.000013, 0.097279, 0.000550, 0.007370],
            'Consequence': self.consequences,
            'binarized_label': [1.0, 1.0, 0.0, 1.0]
        })
        self.consequence_tools = ConsequenceTools()

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
        self.consequence_tools.validate_consequence_samples_equal(self.df, df2, self.consequences)

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
            self.consequence_tools.validate_consequence_samples_equal(
                self.df, df2, self.consequences
            )
        msg = "Model files differ in sample size for consequence(s): " \
              "synonymous_variant, missense_variant"
        self.assertEqual(str(context.warning), msg)

    def test_validator_validate_score_files_length_invalid_total_length(self):
        """
        Total length differs so should always throw a warning. If per consequence is True,
        the total length error should take priority over any consequence-specific validation.
        """
        df2 = pd.DataFrame(data={
            'score': [0.000154, 0.086213, 0.008621],
            'Consequence': ['synonymous_variant', 'missense_variant', 'missense_variant'],
            'binarized_label': [1.0, 1.0, 0.0]
        })

        with self.assertWarns(UserWarning) as context:
            self.consequence_tools.validate_consequence_samples_equal(
                self.df, df2, self.consequences
            )
        msg = "The score files contain a different number of variants."
        self.assertEqual(str(context.warning), msg)

    def test_has_consequence_df1_df2_equal(self):
        df2 = pd.DataFrame(data={
            'Consequence': self.consequences
        })
        observed = self.consequence_tools.has_consequence(self.df, df2)
        self.assertListEqual(observed, ['intron_variant', 'missense_variant', 'synonymous_variant'])

    def test_has_consequence_df1_df2_nonequal(self):
        """
        Since df1 is leading, I do not expect frame_shift_variant to be returned
        """
        df2 = pd.DataFrame(data={
            'Consequence': ['intron_variant', 'frame_shift_variant', 'synonymous_variant']
        })
        observed = self.consequence_tools.has_consequence(self.df, df2)
        self.assertListEqual(observed, ['intron_variant', 'missense_variant', 'synonymous_variant'])

    def test_has_consequence_false(self):
        df2 = pd.DataFrame(data={
            'Some_other_column': self.consequences
        })
        with self.assertWarns(UserWarning) as w:
            observed = self.consequence_tools.has_consequence(
                self.df.drop(columns=['Consequence']),
                df2
            )
        self.assertFalse(observed)
        self.assertEqual(
            str(w.warning),
            'Missing consequence column. Disabling per-consequence performance metrics.'
        )

    def test_has_consequence_df2_only(self):
        """
        Since the comparison module requires Consequence for both models, I expect a user warning
        and False to be returned
        """
        df2 = pd.DataFrame(data={
            'Consequence': ['frameshift_variant', 'intron_variant', '3_prime_utr_variant',
                            'synonymous_variant']
        })
        with self.assertWarns(UserWarning) as w:
            observed = self.consequence_tools.has_consequence(
                self.df.drop(columns='Consequence'),
                df2
            )
        self.assertFalse(observed)
        self.assertEqual(
            str(w.warning),
            'Missing consequence column. Disabling per-consequence performance metrics.'
        )
