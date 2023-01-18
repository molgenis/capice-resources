import unittest

import pandas as pd

from molgenis.capice_resources.compare_model_performance.consequence_tools import ConsequenceTools


class TestConsequenceTools(unittest.TestCase):
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
        Test to see if 2 different (equally sized) frames, each containing an equal amount of
        samples per consequence, does not raise any errors.
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
        Test to see if a warning is raised when 2 equally sized frames, but containing a
        different amount of samples per consequence, is supplied.
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
        Test to see if a warning is thrown when 2 different sample size frames are supplied.
        Since 2 different sample size frames are supplied, the "_merge_scores_and_labels" method
        of compare-model-performance should have kicked in, but if a frame passes to
        ConsequenceTools a warning should be raised anyway.
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
        msg = "Model files differ in sample size for consequence(s): " \
              "synonymous_variant, missense_variant, intron_variant"
        self.assertEqual(str(context.warning), msg)

    def test_has_consequence_df1_df2_equal(self):
        """
        Test to see if an expected list of consequences is returned when both frame 1 and frame 2
        contain the exact same consequences.
        """
        df2 = pd.DataFrame(data={
            'Consequence': self.consequences
        })
        observed = self.consequence_tools.has_consequence(self.df, df2)
        self.assertListEqual(observed, ['intron_variant', 'missense_variant', 'synonymous_variant'])

    def test_has_consequence_df1_df2_nonequal(self):
        """
        Test to see if an expected list of consequences is returned when frame 1 and frame 2
        contain an equal amount of consequences, but the consequences are not exactly equal.
        Since frame 1 is leading, frame_shift_variant is not expected to be returned.
        """
        df2 = pd.DataFrame(data={
            'Consequence': ['intron_variant', 'frame_shift_variant', 'synonymous_variant']
        })
        observed = self.consequence_tools.has_consequence(self.df, df2)
        self.assertListEqual(observed, ['intron_variant', 'missense_variant', 'synonymous_variant'])

    def test_has_consequence_df1_only(self):
        """
        Test to see that "has_consequence" returns False if frame 2 does not contain the
        Consequence column (but frame 1 does), as compare-model-performance can not map a variant
        to a consequence for model 2.
        """
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
        Test to see that "has_consequence" returns False if frame 1 does not contain the
        Consequence column (but frame 2 does), as compare-model-performance can not map a variant
        to a consequence for model 1.
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


if __name__ == '__main__':
    unittest.main()
