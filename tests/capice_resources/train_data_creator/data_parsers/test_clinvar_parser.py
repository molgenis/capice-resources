import os
import unittest

import pandas as pd

from tests.capice_resources.testing_utilities import get_testing_resources_dir
from molgenis.capice_resources.train_data_creator.data_parsers.clinvar import ClinVarParser


class TestClinvarParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dataset = pd.read_csv(  # type: ignore
            os.path.join(get_testing_resources_dir(), 'train_data_creator', 'smol_clinvar.vcf.gz'),
            sep='\t',
            skiprows=27,
            low_memory=False
        )
        cls.parser = ClinVarParser()  # type: ignore

    def setUp(self) -> None:
        self.specific_testing_frame = pd.DataFrame(
            {
                'INFO': [
                    'FIRSTCOL=value1;CLNSIG=LP;GENEINFO=foo:69;'
                    'CLNREVSTAT=criteria_provided,_conflicting_interpretations;LASTCOL=value1',
                    'FIRSTCOL=value2;CLNSIG=P;GENEINFO=bar:42030;'
                    'CLNREVSTAT=reviewed_by_expert_panel;LASTCOL=value2',
                    'FIRSTCOL=value3;CLNSIG=B;GENEINFO=baz:6969420;'
                    'CLNREVSTAT=criteria_provided,_single_submitter;LASTCOL=value3'
                ]
            }
        )

    def test_component_parser(self):
        """
        Component test of the ClinVar parser.
        Tests if the ModuleEnums.columns_of_interest() are all present, binarized_label and if
        the source is set correctly.
        """
        observed = self.parser.parse(self.dataset)
        self.assertIsNone(observed._is_copy)
        for col in [
            '#CHROM',
            'POS',
            'REF',
            'ALT',
            'gene',
            'class',
            'review',
            'dataset_source'
        ]:
            self.assertIn(col, observed.columns)
        self.assertIn('binarized_label', observed.columns)
        self.assertListEqual(
            list(observed['dataset_source'].unique()),
            ['CLINVAR']
        )

    def test_obtain_class(self):
        """
        Tests if the classification is correctly obtained from the INFO field.
        """
        self.assertNotIn('class', self.specific_testing_frame.columns)
        self.parser._obtain_class(self.specific_testing_frame)
        self.assertIn('class', self.specific_testing_frame.columns)
        self.assertListEqual(
            list(self.specific_testing_frame['class'].values),
            ['LP', 'P', 'B']
        )

    def test_obtain_gene(self):
        """
        Tests if the gene name is correctly obtained from the INFO field.
        """
        self.assertNotIn('gene', self.specific_testing_frame.columns)
        self.parser._obtain_gene(self.specific_testing_frame)
        self.assertIn('gene', self.specific_testing_frame.columns)
        self.assertListEqual(
            list(self.specific_testing_frame['gene'].values),
            ['foo', 'bar', 'baz']
        )

    def test_obtain_review(self):
        """
        Tests if the ClinVar review status is correctly obtained from the INFO field and
        correctly parsed into a numerical value.
        """
        self.assertNotIn('review', self.specific_testing_frame.columns)
        self.parser._obtain_review(self.specific_testing_frame)
        self.assertIn('review', self.specific_testing_frame.columns)
        # baz falls off since that will result in a -1 review score
        self.assertListEqual(
            list(self.specific_testing_frame['review'].values),
            [3, 1]
        )

    def test_obtain_review_unknown_review(self):
        """
        Tests if an UserWarning is raised when an unknown review status is encountered in the
        review INFO field.
        """
        test_case = pd.DataFrame(
            {
                'INFO': [
                    'CLNREVSTAT=some_other_value;',
                    'CLNREVSTAT=no_assertion_provided'
                ]
            }
        )
        with self.assertWarns(UserWarning) as w:
            self.parser._obtain_review(test_case)
        self.assertEqual('Found unknown review status: some_other_value', str(w.warning))
        self.assertEqual(test_case.shape[0], 0)


if __name__ == '__main__':
    unittest.main()
