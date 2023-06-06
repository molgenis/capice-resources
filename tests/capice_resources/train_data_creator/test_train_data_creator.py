import os
import gzip
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

import pandas as pd
import pandas.testing

from molgenis.capice_resources import __version__
from tests.capice_resources.testing_utilities import get_testing_resources_dir, \
    check_and_remove_directory
from molgenis.capice_resources.train_data_creator.__main__ import TrainDataCreator
from molgenis.capice_resources.train_data_creator import TrainDataCreatorEnums
from molgenis.capice_resources.train_data_creator.utilities import correct_order_vcf_notation


class TestTrainDataCreator(unittest.TestCase):
    output_directory = os.path.join(
        get_testing_resources_dir(),
        'train_data_creator',
        'output'
        )

    @classmethod
    def tearDownClass(cls) -> None:
        check_and_remove_directory(os.path.join(cls.output_directory, 'train_test.vcf.gz'))
        check_and_remove_directory(os.path.join(cls.output_directory, 'validation.vcf.gz'))

    def test_classmethod_list_columns_of_interest(self):
        """
        Test to check if the classmethod columns_of_interest list is returned properly.
        """
        self.assertListEqual(
            TrainDataCreatorEnums.columns_of_interest(),
            [
                '#CHROM',
                'POS',
                'REF',
                'ALT',
                'gene',
                'class',
                'review',
                'dataset_source'
            ]
        )

    def test_classmethod_list_further_processing_columns(self):
        """
        Test to check if the classmethod further_processing_columns list is returned properly.
        """
        self.assertListEqual(
            TrainDataCreatorEnums.further_processing_columns(),
            [
                '#CHROM',
                'POS',
                'REF',
                'ALT',
                'gene',
            ]
        )

    def subtest_vcf_header(self, vcf_header: list[str]) -> None:
        """
        Subtest to the component test of train-data-creator, to test if the VCF header contains
        the proper information.
        """
        self.subtest_vcf_header_datetime(vcf_header)
        self.subtest_vcf_header_version(vcf_header)
        self.subtest_vcf_header_filenames(vcf_header)

    def subtest_vcf_header_datetime(self, vcf_header: list[str]) -> None:
        """
        Test to ensure the date is set correctly.
        Testing with today and tomorrow to prevent errors to be raised during midnight testing
        """
        today = datetime.now()
        time_format = '%Y%m%d'
        possible_dates = [
            f'##fileDate={today.strftime(time_format)}',
            f'##fileDate={(today + timedelta(days=1)).strftime(time_format)}'
        ]
        intersect = set(vcf_header).intersection(set(possible_dates))
        self.assertEqual(len(intersect), 1)

    def subtest_vcf_header_version(self, vcf_header: list[str]) -> None:
        """
        Test to ensure the CAPICE-resources metadata line is set correctly
        """
        self.assertIn(f'##CAPICE-Resources_version={__version__}', vcf_header)

    def subtest_vcf_header_filenames(self, vcf_header: list[str]) -> None:
        """
        Test to ensure that proper filenames are set within the VCF metadata.
        """
        files = [
            '##Used_VKGL_File=smol_vkgl_may2023.tsv.gz',
            '##Used_ClinVar_File=smol_clinvar_20230508.vcf.gz'
        ]
        intersect = set(vcf_header).intersection(set(files))
        self.assertEqual(len(intersect), 2, msg=f'Present files in header: {intersect}')

    @patch(
        'sys.argv',
        [
            __file__,
            '-v', os.path.join(
                        get_testing_resources_dir(),
                        'train_data_creator',
                        'smol_vkgl_may2023.tsv.gz'
                        ),
            '-c', os.path.join(
                        get_testing_resources_dir(),
                        'train_data_creator',
                        'smol_clinvar_20230508.vcf.gz'
                        ),
            '-o', output_directory
        ]
    )
    def test_component(self):
        """
        Full component testing of the train-data-creator module. Tests from CLI to export,
        including reading back in the train-test and validation datasets, assuming a hardcoded
        amount of headers (if the amount of headers change, that is not intended behaviour).
        Also checks if a considerable amount of samples is present within train-test and
        validation, and that train-test sample size is greater than validation.
        """
        TrainDataCreator().run()
        filepath_train_test = os.path.join(self.output_directory, 'train_test.vcf.gz')
        filepath_validation = os.path.join(self.output_directory, 'validation.vcf.gz')
        vcf_file_header = []
        for i, file in enumerate([filepath_train_test, filepath_validation]):
            filename = os.path.basename(file)
            self.assertIn(
                filename,
                os.listdir(self.output_directory),
                msg=f'{filename} not found in {self.output_directory}'
            )
            count = 0
            with gzip.open(file, 'rt') as fh:
                for line in fh:
                    if line.startswith('##'):
                        if i == 0:
                            vcf_file_header.append(line.strip())
                        count += 1
                    else:
                        break
            self.assertEqual(count, 31)

        self.subtest_vcf_header(vcf_file_header)

        tt = pd.read_csv(  # type: ignore
            filepath_train_test,
            sep='\t',
            skiprows=31,
            na_values='.'
        )
        self.assertGreaterEqual(
            tt.shape[0],
            90
        )
        # Testing if output is ordered
        tt_output = tt.copy(deep=True)
        # Works if train_data_creator.test_utilities.TestUtilities.test_correct_order_vcf_notation
        # passes
        correct_order_vcf_notation(tt)
        pandas.testing.assert_frame_equal(tt, tt_output)

        val = pd.read_csv(  # type: ignore
            filepath_validation,
            sep='\t',
            skiprows=31,
            na_values='.'
        )
        self.assertGreaterEqual(
            val.shape[0],
            6
        )
        self.assertGreater(
            tt.shape[0],
            val.shape[0]
        )

        val_output = val.copy(deep=True)
        correct_order_vcf_notation(val)
        pandas.testing.assert_frame_equal(val, val_output)

    def test_vkgl_date_incorrect(self):
        module = TrainDataCreator()
        module.input_vkgl_filename = 'vkgl_public_consensus_2022may.tsv.gz'
        self.assertRaises(IOError, module._validate_vkgl_date)

    def test_vkgl_date_missing(self):
        module = TrainDataCreator()
        module.input_vkgl_filename = 'vkgl_public_consensus.tsv.gz'
        self.assertRaises(IOError, module._validate_vkgl_date)

    def test_vkgl_date_old_correct(self):
        module = TrainDataCreator()
        module.input_vkgl_filename = 'vkgl_public_consensus_may2023.tsv'
        module._validate_vkgl_date()

    def test_vkgl_date_new_correct(self):
        module = TrainDataCreator()
        module.input_vkgl_filename = 'vkgl_public_consensus_202305.tsv'
        module._validate_vkgl_date()

    def test_clinvar_date_incorrect(self):
        module = TrainDataCreator()
        module.input_clinvar_filename = 'clinvar_08052023.vcf.gz'
        self.assertRaises(IOError, module._validate_clinvar_date)

    def test_clinvar_date_missing(self):
        module = TrainDataCreator()
        module.input_clinvar_filename = 'clinvar.vcf.gz'
        self.assertRaises(IOError, module._validate_clinvar_date)


if __name__ == '__main__':
    unittest.main()
