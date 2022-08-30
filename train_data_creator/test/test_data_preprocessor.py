import os
import unittest

import numpy as np
import pandas as pd

from train_data_creator.test import get_project_root_dir
from train_data_creator.src.main.data_preprocessor import VKGL, ClinVar


class TestDataProcessor(unittest.TestCase):
    __CHROM__ = '#CHROM'

    def setUp(self) -> None:
        self.vkgl = os.path.join(get_project_root_dir(), 'test', 'resources', 'smol_vkgl.tsv.gz')
        self.clinvar = os.path.join(get_project_root_dir(), 'test', 'resources',
                                   'smol_clinvar.vcf.gz')
        self.dataset = pd.DataFrame(
            {
                'INFO': [
                    'SOMEVALUE=1003;CLNSIG=VUS;SOMEOTHERVALUE=103438;'
                    'CLNREVSTAT=no_assertion_provided;GENEINFO=foo:10051',
                    'SOMEVALUE=1243;CLNSIG=Likely_pathogenic;SOMEOTHERVALUE=8864389;'
                    'CLNREVSTAT=reviewed_by_expert_panel;GENEINFO=baz:509709'
                ]
            }
        )

    def test_vkgl(self):
        vkgl = VKGL()
        observed = vkgl.parse(self.vkgl)
        expected = pd.DataFrame(
            {self.__CHROM__: {0: 2, 1: 2, 2: 2, 3: 7, 4: 7, 5: 7, 6: 7, 7: 10,
                              8: 11, 9: 11, 10: 11, 11: 11, 12: 11, 13: 11,
                              14: 11, 15: 12, 16: 13, 17: 13, 18: 13, 19: 13,
                              20: 13, 21: 13, 22: 13, 23: 13, 24: 13, 25: 13,
                              26: 13, 27: 13, 28: 13, 29: 13, 30: 13, 31: 13,
                              32: 13, 33: 13, 34: 13, 35: 13, 36: 14, 37: 16,
                              38: 17, 39: 17, 40: 17, 41: 17, 42: 17, 43: 17,
                              44: 17, 45: 17, 46: 17, 47: 17, 48: 17, 49: 17,
                              50: 17, 51: 17, 52: 17, 53: 17, 54: 17, 55: 17,
                              56: 17, 57: 17, 58: 17, 59: 17, 60: 19},
             'POS': {0: 47600591, 1: 47614114, 2: 47698179, 3: 6026708,
                     4: 6029452, 5: 6043386, 6: 124475296, 7: 89623860,
                     8: 108119615, 9: 108119615, 10: 108121410,
                     11: 108178738, 12: 108183385, 13: 108188266,
                     14: 108202260, 15: 133249166, 16: 32900363,
                     17: 32900930, 18: 32910891, 19: 32911703,
                     20: 32912007, 21: 32913055, 22: 32913196,
                     23: 32913609, 24: 32913760, 25: 32914196,
                     26: 32914349, 27: 32914489, 28: 32914815,
                     29: 32915135, 30: 32929360, 31: 32937429,
                     32: 32944628, 33: 32971235, 34: 32972380,
                     35: 32972695, 36: 65550984, 37: 68771372,
                     38: 7578457, 39: 41209068, 40: 41215954,
                     41: 41226601, 42: 41228668, 43: 41243190,
                     44: 41244122, 45: 41244481, 46: 41245136,
                     47: 41245237, 48: 41245900, 49: 41246092,
                     50: 41246483, 51: 41249263, 52: 41251752,
                     53: 41256074, 54: 41256266, 55: 41258361,
                     56: 56780540, 57: 56801451, 58: 59924505,
                     59: 59926423, 60: 11169097},
             'REF': {0: 'T', 1: 'A', 2: 'A', 3: 'C', 4: 'GCTGA', 5: 'G',
                     6: 'TAAACA', 7: 'CT', 8: 'CAA', 9: 'CA', 10: 'CT',
                     11: 'G', 12: 'G', 13: 'AT', 14: 'A', 15: 'C',
                     16: 'C', 17: 'A', 18: 'G', 19: 'C', 20: 'C',
                     21: 'A', 22: 'G', 23: 'A', 24: 'A', 25: 'G',
                     26: 'G', 27: 'G', 28: 'G', 29: 'TACTC', 30: 'T',
                     31: 'G', 32: 'G', 33: 'G', 34: 'G', 35: 'A',
                     36: 'C', 37: 'C', 38: 'C', 39: 'C', 40: 'A',
                     41: 'G', 42: 'C', 43: 'T', 44: 'T', 45: 'C',
                     46: 'C', 47: 'A', 48: 'T', 49: 'A', 50: 'C',
                     51: 'G', 52: 'G', 53: 'CA', 54: 'T', 55: 'T',
                     56: 'G', 57: 'C', 58: 'A', 59: 'A', 60: 'G'},
             'ALT': {0: 'A', 1: 'G', 2: 'G', 3: 'A', 4: 'G', 5: 'A',
                     6: 'T', 7: 'C', 8: 'C', 9: 'C', 10: 'C', 11: 'A',
                     12: 'A', 13: 'A', 14: 'G', 15: 'T', 16: 'CT',
                     17: 'G', 18: 'A', 19: 'T', 20: 'T', 21: 'G',
                     22: 'C', 23: 'C', 24: 'G', 25: 'A', 26: 'T',
                     27: 'A', 28: 'A', 29: 'T', 30: 'G', 31: 'A',
                     32: 'A', 33: 'A', 34: 'A', 35: 'G', 36: 'T',
                     37: 'T', 38: 'T', 39: 'T', 40: 'G', 41: 'C',
                     42: 'T', 43: 'G', 44: 'C', 45: 'T', 46: 'G',
                     47: 'G', 48: 'G', 49: 'G', 50: 'T', 51: 'A',
                     52: 'T', 53: 'C', 54: 'C', 55: 'C', 56: 'T',
                     57: 'T', 58: 'G', 59: 'G', 60: 'A'},
             'gene': {0: 'EPCAM', 1: 'EPCAM', 2: 'MSH2', 3: 'PMS2',
                      4: 'PMS2', 5: 'PMS2', 6: 'POT1', 7: 'PTEN',
                      8: 'ATM', 9: 'ATM', 10: 'ATM', 11: 'ATM',
                      12: 'ATM', 13: 'ATM', 14: 'ATM', 15: 'POLE',
                      16: 'BRCA2', 17: 'BRCA2', 18: 'BRCA2',
                      19: 'BRCA2', 20: 'BRCA2', 21: 'BRCA2',
                      22: 'BRCA2', 23: 'BRCA2', 24: 'BRCA2',
                      25: 'BRCA2', 26: 'BRCA2', 27: 'BRCA2',
                      28: 'BRCA2', 29: 'BRCA2', 30: 'BRCA2',
                      31: 'BRCA2', 32: 'BRCA2', 33: 'BRCA2',
                      34: 'BRCA2', 35: 'BRCA2', 36: 'MAX', 37: 'CDH1',
                      38: 'TP53', 39: 'BRCA1', 40: 'BRCA1', 41: 'BRCA1',
                      42: 'BRCA1', 43: 'BRCA1', 44: 'BRCA1',
                      45: 'BRCA1', 46: 'BRCA1', 47: 'BRCA1',
                      48: 'BRCA1', 49: 'BRCA1', 50: 'BRCA1',
                      51: 'BRCA1', 52: 'BRCA1', 53: 'BRCA1',
                      54: 'BRCA1', 55: 'BRCA1', 56: 'RAD51C',
                      57: 'RAD51C', 58: 'BRIP1', 59: 'BRIP1',
                      60: 'SMARCA4'},
             'class': {0: 'LB', 1: 'LB', 2: 'LB', 3: 'LB', 4: 'P',
                       5: 'LB', 6: 'LB', 7: 'LB', 8: 'B', 9: 'LB',
                       10: 'LB', 11: 'LB', 12: 'LB', 13: 'LB', 14: 'LB',
                       15: 'LB', 16: 'LB', 17: 'LB', 18: 'LB', 19: 'LB',
                       20: 'LB', 21: 'LB', 22: 'LB', 23: 'LB', 24: 'LB',
                       25: 'LB', 26: 'LP', 27: 'LB', 28: 'LB', 29: 'LP',
                       30: 'LB', 31: 'LB', 32: 'LB', 33: 'LB', 34: 'LB',
                       35: 'LB', 36: 'LB', 37: 'LB', 38: 'LP', 39: 'LP',
                       40: 'LP', 41: 'LB', 42: 'LB', 43: 'LB', 44: 'LB',
                       45: 'LB', 46: 'LB', 47: 'LB', 48: 'LB', 49: 'LB',
                       50: 'LB', 51: 'LB', 52: 'LB', 53: 'LB', 54: 'LB',
                       55: 'LB', 56: 'LB', 57: 'LP', 58: 'LB', 59: 'B',
                       60: 'LB'},
             'review': {0: 2, 1: 1, 2: 2, 3: 2, 4: 1, 5: 2, 6: 2, 7: 2,
                        8: 1, 9: 2, 10: 2, 11: 2, 12: 1, 13: 2, 14: 1,
                        15: 1, 16: 2, 17: 1, 18: 2, 19: 1, 20: 2, 21: 2,
                        22: 1, 23: 2, 24: 2, 25: 2, 26: 2, 27: 1, 28: 2,
                        29: 2, 30: 2, 31: 2, 32: 2, 33: 1, 34: 2, 35: 2,
                        36: 1, 37: 2, 38: 2, 39: 2, 40: 2, 41: 2, 42: 1,
                        43: 2, 44: 2, 45: 1, 46: 2, 47: 2, 48: 2, 49: 2,
                        50: 2, 51: 2, 52: 1, 53: 2, 54: 2, 55: 1, 56: 2,
                        57: 2, 58: 2, 59: 1, 60: 1},
             'source': {0: 'VKGL', 1: 'VKGL', 2: 'VKGL', 3: 'VKGL',
                        4: 'VKGL', 5: 'VKGL', 6: 'VKGL', 7: 'VKGL',
                        8: 'VKGL', 9: 'VKGL', 10: 'VKGL', 11: 'VKGL',
                        12: 'VKGL', 13: 'VKGL', 14: 'VKGL', 15: 'VKGL',
                        16: 'VKGL', 17: 'VKGL', 18: 'VKGL', 19: 'VKGL',
                        20: 'VKGL', 21: 'VKGL', 22: 'VKGL', 23: 'VKGL',
                        24: 'VKGL', 25: 'VKGL', 26: 'VKGL', 27: 'VKGL',
                        28: 'VKGL', 29: 'VKGL', 30: 'VKGL', 31: 'VKGL',
                        32: 'VKGL', 33: 'VKGL', 34: 'VKGL', 35: 'VKGL',
                        36: 'VKGL', 37: 'VKGL', 38: 'VKGL', 39: 'VKGL',
                        40: 'VKGL', 41: 'VKGL', 42: 'VKGL', 43: 'VKGL',
                        44: 'VKGL', 45: 'VKGL', 46: 'VKGL', 47: 'VKGL',
                        48: 'VKGL', 49: 'VKGL', 50: 'VKGL', 51: 'VKGL',
                        52: 'VKGL', 53: 'VKGL', 54: 'VKGL', 55: 'VKGL',
                        56: 'VKGL', 57: 'VKGL', 58: 'VKGL', 59: 'VKGL',
                        60: 'VKGL'},
             'binarized_label': {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 1.0,
                                 5: 0.0, 6: 0.0, 7: 0.0, 8: 0.0, 9: 0.0,
                                 10: 0.0, 11: 0.0, 12: 0.0, 13: 0.0,
                                 14: 0.0, 15: 0.0, 16: 0.0, 17: 0.0,
                                 18: 0.0, 19: 0.0, 20: 0.0, 21: 0.0,
                                 22: 0.0, 23: 0.0, 24: 0.0, 25: 0.0,
                                 26: 1.0, 27: 0.0, 28: 0.0, 29: 1.0,
                                 30: 0.0, 31: 0.0, 32: 0.0, 33: 0.0,
                                 34: 0.0, 35: 0.0, 36: 0.0, 37: 0.0,
                                 38: 1.0, 39: 1.0, 40: 1.0, 41: 0.0,
                                 42: 0.0, 43: 0.0, 44: 0.0, 45: 0.0,
                                 46: 0.0, 47: 0.0, 48: 0.0, 49: 0.0,
                                 50: 0.0, 51: 0.0, 52: 0.0, 53: 0.0,
                                 54: 0.0, 55: 0.0, 56: 0.0, 57: 1.0,
                                 58: 0.0, 59: 0.0, 60: 0.0}})
        pd.testing.assert_frame_equal(observed, expected)

    def test_clinvar(self):
        clinvar = ClinVar()
        observed = clinvar.parse(self.clinvar)
        expected = pd.DataFrame(
            {self.__CHROM__: {0: 1, 1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1,
                              11: 1,
                              12: 1, 13: 1, 14: 1, 15: 1, 16: 1, 17: 1, 18: 1, 19: 1, 20: 1, 21: 1,
                              22: 1,
                              23: 1, 24: 1, 25: 1, 26: 1, 27: 1, 28: 1, 29: 1, 30: 1, 31: 1, 32: 1,
                              33: 1,
                              34: 1, 35: 1, 36: 1, 37: 1, 38: 1, 39: 1, 40: 1, 41: 1, 42: 1, 43: 1},
             'POS': {0: 865519, 1: 865545, 2: 865567, 3: 865579, 4: 865584, 5: 865625, 6: 865627,
                     7: 865628, 8: 865662, 9: 865665, 10: 865694, 11: 865700, 12: 865705,
                     13: 865723, 14: 865726, 15: 866404, 16: 866422, 17: 866431, 18: 866438,
                     19: 866461, 20: 866478, 21: 871143, 22: 871143, 23: 871146, 24: 871155,
                     25: 871158, 26: 871159, 27: 871173, 28: 871176, 29: 871192, 30: 871206,
                     31: 871215, 32: 871215, 33: 871219, 34: 871229, 35: 871230, 36: 871239,
                     37: 871252, 38: 874410, 39: 874415, 40: 874416, 41: 874451, 42: 874456,
                     43: 874457},
             'REF': {0: 'C', 1: 'G', 2: 'C', 3: 'C', 4: 'G', 5: 'G', 6: 'T', 7: 'G', 8: 'G', 9: 'G',
                     10: 'C', 11: 'C', 12: 'C', 13: 'G', 14: 'C', 15: 'C', 16: 'C', 17: 'C',
                     18: 'G', 19: 'G', 20: 'C', 21: 'G', 22: 'G', 23: 'C', 24: 'G', 25: 'C',
                     26: 'G', 27: 'C', 28: 'C', 29: 'C', 30: 'C', 31: 'C', 32: 'C', 33: 'C',
                     34: 'G', 35: 'C', 36: 'C', 37: 'C', 38: 'C', 39: 'C', 40: 'G', 41: 'C',
                     42: 'G', 43: 'T'},
             'ALT': {0: 'T', 1: 'A', 2: 'T', 3: 'T', 4: 'A', 5: 'A', 6: 'C', 7: 'A', 8: 'A', 9: 'A',
                     10: 'T', 11: 'T', 12: 'T', 13: 'T', 14: 'G', 15: 'T', 16: 'T', 17: 'T',
                     18: 'A', 19: 'A', 20: 'T', 21: 'A', 22: 'T', 23: 'T', 24: 'A', 25: 'T',
                     26: 'A', 27: 'T', 28: 'T', 29: 'T', 30: 'T', 31: 'G', 32: 'T', 33: 'T',
                     34: 'C', 35: 'T', 36: 'T', 37: 'T', 38: 'T', 39: 'T', 40: 'A', 41: 'T',
                     42: 'A', 43: 'C'},
             'gene': {0: 'SAMD11', 1: 'SAMD11', 2: 'SAMD11', 3: 'SAMD11', 4: 'SAMD11', 5: 'SAMD11',
                      6: 'SAMD11', 7: 'SAMD11', 8: 'SAMD11', 9: 'SAMD11', 10: 'SAMD11',
                      11: 'SAMD11', 12: 'SAMD11', 13: 'SAMD11', 14: 'SAMD11', 15: 'SAMD11',
                      16: 'SAMD11', 17: 'SAMD11', 18: 'SAMD11', 19: 'SAMD11', 20: 'SAMD11',
                      21: 'SAMD11', 22: 'SAMD11', 23: 'SAMD11', 24: 'SAMD11', 25: 'SAMD11',
                      26: 'SAMD11', 27: 'SAMD11', 28: 'SAMD11', 29: 'SAMD11', 30: 'SAMD11',
                      31: 'SAMD11', 32: 'SAMD11', 33: 'SAMD11', 34: 'SAMD11', 35: 'SAMD11',
                      36: 'SAMD11', 37: 'SAMD11', 38: 'SAMD11', 39: 'SAMD11', 40: 'SAMD11',
                      41: 'SAMD11', 42: 'SAMD11', 43: 'SAMD11'},
             'class': {0: 'LB', 1: 'B', 2: 'LB', 3: 'LB', 4: 'B', 5: 'LB', 6: 'LB', 7: 'LB',
                       8: 'LB', 9: 'B', 10: 'B', 11: 'LB', 12: 'B', 13: 'LB', 14: 'LB', 15: 'LB',
                       16: 'B', 17: 'LB', 18: 'LB', 19: 'LB', 20: 'LB', 21: 'LB', 22: 'LB', 23: 'B',
                       24: 'LB', 25: 'LB', 26: 'B', 27: 'LB', 28: 'B', 29: 'LB', 30: 'LB', 31: 'B',
                       32: 'B', 33: 'LB', 34: 'LB', 35: 'LB', 36: 'B', 37: 'LB', 38: 'LB', 39: 'B',
                       40: 'LB', 41: 'LB', 42: 'LB', 43: 'LB'},
             'review': {0: 1, 1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1, 11: 1,
                        12: 1, 13: 1, 14: 1, 15: 1, 16: 1, 17: 1, 18: 1, 19: 1, 20: 1, 21: 1, 22: 1,
                        23: 1, 24: 1, 25: 1, 26: 1, 27: 1, 28: 1, 29: 1, 30: 1, 31: 1, 32: 1, 33: 1,
                        34: 1, 35: 1, 36: 1, 37: 1, 38: 1, 39: 1, 40: 1, 41: 1, 42: 1, 43: 1},
             'source': {0: 'ClinVar', 1: 'ClinVar', 2: 'ClinVar', 3: 'ClinVar', 4: 'ClinVar',
                        5: 'ClinVar', 6: 'ClinVar', 7: 'ClinVar', 8: 'ClinVar', 9: 'ClinVar',
                        10: 'ClinVar', 11: 'ClinVar', 12: 'ClinVar', 13: 'ClinVar', 14: 'ClinVar',
                        15: 'ClinVar', 16: 'ClinVar', 17: 'ClinVar', 18: 'ClinVar', 19: 'ClinVar',
                        20: 'ClinVar', 21: 'ClinVar', 22: 'ClinVar', 23: 'ClinVar', 24: 'ClinVar',
                        25: 'ClinVar', 26: 'ClinVar', 27: 'ClinVar', 28: 'ClinVar', 29: 'ClinVar',
                        30: 'ClinVar', 31: 'ClinVar', 32: 'ClinVar', 33: 'ClinVar', 34: 'ClinVar',
                        35: 'ClinVar', 36: 'ClinVar', 37: 'ClinVar', 38: 'ClinVar', 39: 'ClinVar',
                        40: 'ClinVar', 41: 'ClinVar', 42: 'ClinVar', 43: 'ClinVar'},
             'binarized_label': {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0, 7: 0.0,
                                 8: 0.0, 9: 0.0, 10: 0.0, 11: 0.0, 12: 0.0, 13: 0.0, 14: 0.0,
                                 15: 0.0, 16: 0.0, 17: 0.0, 18: 0.0, 19: 0.0, 20: 0.0, 21: 0.0,
                                 22: 0.0, 23: 0.0, 24: 0.0, 25: 0.0, 26: 0.0, 27: 0.0, 28: 0.0,
                                 29: 0.0, 30: 0.0, 31: 0.0, 32: 0.0, 33: 0.0, 34: 0.0, 35: 0.0,
                                 36: 0.0, 37: 0.0, 38: 0.0, 39: 0.0, 40: 0.0, 41: 0.0, 42: 0.0,
                                 43: 0.0}}
        )
        pd.testing.assert_frame_equal(observed, expected)

    def test_vgkl__apply_review_status(self):
        dataset = pd.DataFrame(
            {
                'labs': [1, 2, 3, 4, 1]
            }
        )
        observed = VKGL()._apply_review_status(dataset)
        expected = pd.DataFrame(
            {
                'labs': [1, 2, 3, 4, 1],
                'review': [1, 2, 2, 2, 1]
            }
        )
        pd.testing.assert_frame_equal(observed, expected)

    def test_vkgl__correct_single_consensus(self):
        one_lab = 'Classified by one lab'
        link_column = ['A_link', 'Some_other_link', 'A_third_link', 'A_forth_link']
        likely_benign = '(Likely) Benign'
        dataset = pd.DataFrame(
            {
                'foo': [np.nan, likely_benign, np.nan, np.nan],
                'foo_link': link_column,
                'bar': ['Benign', np.nan, np.nan, np.nan],
                'bar_link': link_column,
                'baz': [np.nan, np.nan, 'Pathogenic', np.nan],
                'baz_link': link_column,
                'class': [one_lab, one_lab, one_lab, 'foo']
            }
        )
        observed = VKGL()._correct_single_consensus(dataset)
        expected = pd.DataFrame(
            {
                'foo': ['', likely_benign, '', ''],
                'foo_link': link_column,
                'bar': ['Benign', '', '', ''],
                'bar_link': link_column,
                'baz': ['', '', 'Pathogenic', ''],
                'baz_link': link_column,
                'class': ['Benign', likely_benign, 'Pathogenic', 'foo'],
                'labs': [1, 1, 1, 2]
            }
        )
        pd.testing.assert_frame_equal(observed, expected)

    def test_vkgl__correct_column_names(self):
        dataset = pd.DataFrame(
            columns=['chromosome', 'start', 'ref', 'alt', 'consensus_classification', 'foo', 'bar']
        )
        observed = VKGL()._correct_column_names(dataset)
        expected = pd.DataFrame(
            columns=[self.__CHROM__, 'POS', 'REF', 'ALT', 'class', 'foo', 'bar']
        )
        pd.testing.assert_frame_equal(observed, expected)

    def test_clinvar__get_n_header(self):
        file = os.path.join(get_project_root_dir(), 'test', 'resources', 'hashtag_file.txt')
        observed = ClinVar()._get_n_header(file)
        self.assertEqual(observed, 14)

    def test_clinvar__obtain_class(self):
        expected = pd.concat(
            [
                self.dataset,
                pd.DataFrame(
                    {
                        'class': ['VUS', 'Likely_pathogenic']
                    }
                )
            ], axis=1
        )
        observed = ClinVar()._obtain_class(self.dataset)
        pd.testing.assert_frame_equal(observed, expected)

    def test_clinvar__obtain_gene(self):
        expected = pd.concat(
            [
                self.dataset,
                pd.DataFrame(
                    {
                        'gene': ['foo', 'baz']
                    }
                )
            ], axis=1
        )
        observed = ClinVar()._obtain_gene(self.dataset)
        pd.testing.assert_frame_equal(observed, expected)

    def test_clinvar__obtain_review(self):
        # Slightly modified expected since review status 0 is dropped
        expected = pd.concat(
            [
                pd.DataFrame(data=self.dataset.iloc[1, :].values, columns=['INFO'], index=[1]),
                pd.DataFrame(
                    {
                        'review': [3]
                    }, index=[1]
                )
            ], axis=1
        )
        observed = ClinVar()._obtain_review(self.dataset)
        pd.testing.assert_frame_equal(observed, expected)

    def test_clinvar_review_unknown(self):
        pseudo_clinvar_data = pd.DataFrame(
            {
                'INFO': ['CLNREVSTAT=some_unknown_status;', 'CLNREVSTAT=practice_guideline;',
                         'CLNREVSTAT=reviewed_by_expert_panel;']
            }
        )
        expected_out = pd.DataFrame(
            {
                'INFO': ['CLNREVSTAT=practice_guideline;',
                         'CLNREVSTAT=reviewed_by_expert_panel;'],
                'review': [4, 3]
            }
        )
        with self.assertWarns(UserWarning) as cm:
            ClinVar()._obtain_review(pseudo_clinvar_data)
        self.assertEqual('Found unknown review status: some_unknown_status', str(cm.warning))
        pd.testing.assert_frame_equal(pseudo_clinvar_data.reset_index(drop=True), expected_out)


if __name__ == '__main__':
    unittest.main()
