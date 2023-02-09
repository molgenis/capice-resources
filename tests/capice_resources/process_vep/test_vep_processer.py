import unittest

import pandas as pd

from molgenis.capice_resources.process_vep.vep_processer import VEPProcesser


class TestVepProcesser(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.processor = VEPProcesser()  # type: ignore

    def test_drop_duplicates(self):
        """
        Test to check if a duplicate, according to a list of features, is dropped properly.
        """
        test_case = pd.DataFrame(
            [
                ['variant_1', 'value_1', 'value_2', 'value_3'],
                ['variant_2', 'value_4', 'value_5', 'value_6'],
                ['variant_3', 'value_1', 'value_2', 'value_9'],  # Duplicate of 1
                ['variant_4', 'value_10', 'value_11', 'value_12'],
                ['variant_5', 'value_13', 'value_14', 'value_15'],
                ['variant_6', 'value_16', 'value_17', 'value_18']
            ], columns=['variant', 'feature_1', 'feature_2', 'feature_3']
        )
        self.processor.drop_duplicates(test_case, ['feature_1', 'feature_2'])
        self.assertNotIn('variant_3', test_case['variant'].values)
        for variant in ['variant_1', 'variant_2', 'variant_4', 'variant_5', 'variant_6']:
            self.assertIn(variant, test_case['variant'].values)

    def test_drop_genes_empty(self):
        """
        Test to check if a sample that does not have a "SYMBOL" (VEP gene name) is dropped properly.
        """
        test_case = pd.DataFrame(
            [
                ['variant_1', 'gene_1', 'train_test'],
                ['variant_2', None, 'train_test'],
                ['variant_3', 'gene_2', 'train_test']
            ], columns=['variant', 'SYMBOL', 'dataset_source']
        )
        self.processor.drop_genes_empty(test_case)
        self.assertNotIn('variant_2', test_case['variant'].values)

    def test_process_grch38(self):
        """
        Test to check if GRCh38 contigs are properly processed. Expected is that all "exotic"
        contigs (for example chr1_contig114860489) are dropped for consistency reasons.
        """
        test_case = pd.DataFrame(
            {
                'CHROM': ['chr1', 'chr2', 'chr3_foobar', 'chrX', 'chrY_fake'],
                'variant': ['var1', 'var2', 'var3', 'var4', 'var5']
            }
        )
        self.processor.process_grch38(test_case)
        self.assertNotIn('var3', test_case['variant'].values)
        self.assertNotIn('var5', test_case['variant'].values)
        expected = ['var1', 'var2', 'var4']
        for e in expected:
            self.assertIn(e, test_case['variant'].values)

    def test_drop_duplicate_entries(self):
        """
        Test that checks if full on duplicates (unlike test_drop_duplicates that subsets a
        feature list) are dropped properly.
        """
        # Possible since VEP can output the same variant twice, or more
        test_case = pd.DataFrame(
            {
                'variant': ['variant_1', 'variant_2', 'variant_2', 'variant_3', 'variant_3'],
                'transcript': ['t1', 't2', 't1', 't1', 't1'],
                'feature_1': [1, 2, 3, 5, 5]
            }
        )
        expected = pd.DataFrame(
            {
                'variant': ['variant_1', 'variant_2', 'variant_2', 'variant_3'],
                'transcript': ['t1', 't2', 't1', 't1'],
                'feature_1': [1, 2, 3, 5]
            }
        )
        self.processor.drop_duplicate_entries(test_case)
        pd.testing.assert_frame_equal(test_case, expected)

    def test_mismatching_genes(self):
        """
        Test that checks if a sample is dropped properly when a gene-name from the ID column
        mismatches with the SYMBOL column.
        """
        test_case = pd.DataFrame(
            {
                'ID': ['1!1!A!G!foo', '1!1!A!G!bar', '1!1!A!G!baz'],
                'SYMBOL': ['foo', 'bar', 'foobaz'],
                'variant': ['var1', 'var2', 'var3']
            }
        )
        self.processor.drop_mismatching_genes(test_case)
        self.assertNotIn('var3', test_case['variant'].values)

    def test_drop_heterozygous_variants_in_ar_genes(self):
        """
        Test that checks if a variant is properly dropped when it only has been observed as
        "heterozygous" (so homozygous counts is 0, not NaN) in Autosomal Recessive observed genes.
        """
        test_case = pd.DataFrame(
            {
                'variant': ['var1', 'var2', 'var3'],
                'SYMBOL': ['foo', 'bar', 'baz'],
                'gnomAD_HN': [None, 0, 0]
            }
        )
        self.processor.drop_heterozygous_variants_in_ar_genes(
            test_case,
            ['foo', 'bar', 'gene1']
        )
        self.assertNotIn('var2', test_case['variant'].values)
        for variant in ['var1', 'var3']:
            self.assertIn(variant, test_case['variant'].values)

    def test_drop_variants_incorrect_label_or_weight(self):
        """
        Test that ensures that the binarized_label and sample_weight are set to proper standards.
        In the past (due to incorrect ID column split) it was possible for binarized_label to
        become an incorrect label.
        """
        test_case = pd.DataFrame(
            {
                'ID': [None, 'foo', 'bar', 'baz'],
                'binarized_label': [None, 0.1, 0, 1],
                'sample_weight': [0.8, 0.9, 1.0, 0.7],
                'variant': ['var1', 'var2', 'var3', 'var4']
            }
        )
        self.processor.drop_variants_incorrect_label_or_weight(test_case)
        self.assertNotIn('ID', test_case.columns)
        self.assertIn('var3', test_case['variant'].values)
        for notin in ['var1', 'var2', 'var4']:
            self.assertNotIn(notin, test_case['variant'].values)


if __name__ == '__main__':
    unittest.main()
