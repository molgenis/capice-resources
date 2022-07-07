import os
import gzip
import pandas as pd

ID_SEPARATOR = '!'


class Exporter:
    def __init__(self, output):
        self.output = output
        self.vcf_header = [
            '##fileformat=VCFv4.2',
            '##contig=<ID=1,length=249250621,assembly=b37>',
            '##contig=<ID=2,assembly=b37,length=243199373>',
            '##contig=<ID=3,assembly=b37,length=198022430>',
            '##contig=<ID=4,length=191154276,assembly=b37>',
            '##contig=<ID=5,length=180915260,assembly=b37>',
            '##contig=<ID=6,length=171115067,assembly=b37>',
            '##contig=<ID=7,length=159138663,assembly=b37>',
            '##contig=<ID=8,length=146364022,assembly=b37>',
            '##contig=<ID=9,length=141213431,assembly=b37>',
            '##contig=<ID=10,length=135534747,assembly=b37>',
            '##contig=<ID=11,length=135006516,assembly=b37>',
            '##contig=<ID=12,length=133851895,assembly=b37>',
            '##contig=<ID=13,length=115169878,assembly=b37>',
            '##contig=<ID=14,length=107349540,assembly=b37>',
            '##contig=<ID=15,length=102531392,assembly=b37>',
            '##contig=<ID=16,length=90354753,assembly=b37>',
            '##contig=<ID=17,length=81195210,assembly=b37>',
            '##contig=<ID=18,length=78077248,assembly=b37>',
            '##contig=<ID=19,length=59128983,assembly=b37>',
            '##contig=<ID=20,length=63025520,assembly=b37>',
            '##contig=<ID=21,length=48129895,assembly=b37>',
            '##contig=<ID=22,length=51304566,assembly=b37>',
            '##contig=<ID=X,assembly=b37,length=155270560>',
            '##contig=<ID=Y,length=59373566,assembly=b37>',
            '##contig=<ID=MT,length=16569,assembly=b37>',
            '##fileDate=20200320'
        ]

    def export_validation_dataset(self, data: pd.DataFrame):
        self._export(data, dataset_type='validation')

    def export_train_test_dataset(self, data: pd.DataFrame):
        self._export(data, dataset_type='train_test')

    def _export(self, data: pd.DataFrame, dataset_type: str):
        export_loc = os.path.join(self.output, dataset_type + '.vcf.gz')
        with gzip.open(export_loc, 'wt') as pseudo_vcf:
            for line in self.vcf_header:
                pseudo_vcf.write(f'{line}\n')

        # Adding required columns
        data['QUAL'] = '.'
        data['FILTER'] = 'PASS'
        data['INFO'] = '.'

        # Making sure that the variant can be mapped back after VEP
        data['ID'] = data[
            [
                '#CHROM',
                'POS',
                'REF',
                'ALT',
                'gene',
                'binarized_label',
                'sample_weight'
            ]
        ].astype(str).agg(ID_SEPARATOR.join, axis=1)
        data[
            ['#CHROM', 'POS', 'ID', 'REF', 'ALT', 'QUAL', 'FILTER', 'INFO']
        ].to_csv(export_loc, mode='a', sep='\t', index=False, compression='gzip', na_rep='.')
        print(f'Export to {export_loc} successful.')
