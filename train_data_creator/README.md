# Train data creator
###### Resource module for CAPICE to create new train-test and validation datasets

## Usage
`python3 main.py -iv path/to/vkgl_consensus.tsv.gz -ic path/to/clinvar.vcf.gz -o path/to/existing/output/directory`

_Note: -iv needs to be the non-public VKGL, public will throw an FileNotFoundError_

## What it does

### Train_data_creator module

(data_preprocessor.py)

Step 1 is to load in the different type datasets, which is not all that easy.

VCF files have headers that can't be directly parsed into VCF. The amount of lines are obtained and provided to the pandas parser.

The VKGL TSV is easier to parse since that doesn't require extra skips.

After that the files are validated.

For VKGL the file follows the following path:
- Correcting the TSV to VCF-like column names.
- Correcting the consensus-classification of "Classified by one lab" to the actual classification of the lab (also setting the amount of labs for that variant to 1 for review status).
- Ordering according to VCF standards.
- Applying the ClinVar review status to their Gold Star Description.
- Equalizing the (likely) benign and (likely) pathogenic (also VUS) classifications (and dropping everything else).
- Applying a binarized label (0.0 for (likely) benign and 1.0 for (likely) pathogenic).

For ClinVar the file follows the following (similar) path:
- (Before the file gets even loaded) obtaining the amount of header lines
- Obtaining the classification from the INFO field.
- Obtaining the gene from the INFO field.
- Obtaining the review status from the INFO field.
- Equalizing the (likely) benign and (likely) pathogenic (also VUS) classifications (and dropping everything else).
- Applying a binarized label (0.0 for (likely) benign and 1.0 for (likely) pathogenic).

After that, both files are equal in terms of columns, column types and variables within the columns.

(main.py)

Both datasets are merged, with the column "source" indicating their true origin and the originally loaded datasets are deleted to preserve RAM usage.

(duplicate_processor.py)

Once merged, duplicates have to be removed since it is possible that VKGL samples are present within ClinVar. 
Duplicates are dropped if all of the following columns are duplicates:
- CHROM
- POS
- REF
- ALT
- gene
- class

Since the keep in pandas.DataFrame.drop_duplicates() is not defined, the first duplicate will remain present while the rest are dropped.
_Note: it might be possible that duplicate variants are still present with conflicting classes, since those do not count as duplicates. We don't think this will be an issue due to the amount of samples._

Now that we have an assembled large dataset, we can start building the train-test and validation datasets. __But be fore we can do that__, it is useful to apply the sample weights already.
Sample weights is what tells XGBoost (and other machine learning algorithms) how well it should trust the particular sample.
As of current, the following ClinVar Gold Star ratings are used to apply the following sample weights:

| Gold star rating | Sample weight |
|:----------------:|:-------------:|
|         0        |      Removed      |
|         1        |      0.8      |
|         2        |      0.9      |
|         3        |      1.0      |
|         4        |      1.0      |

Now that sample weights have been mapped and applied, the large dataset can be split into the train-test and validation datasets.

(split_datasets.py)

The most important part about the splitting of the large dataset into the train-test and validation datasets is that the validation dataset is of high quality.
This is done by randomly sampling 20% of high quality pathogenic variants (review score 2 or higher / originated from VKGL).
Then the same amount of high quality benign variants (same requirements) is sampled.

To remove the randomly sampled validation dataset variants from the train-test dataset,
the validation variants are added back to the train-test dataset and then the drop_duplicates() pandas method is called with the keep parameter set to False,
this means that any and all duplicates are thrown away.

This results in the train-test and validation datasets, that are exported to the output argument.

### Making Pseudo-VCF and VEP annotation

Now it is important to convert the generated TSV to a VEP interpretable VCF. 
For this, load in the dataset into an interactive python shell using pandas.

Add the following columns to make the TSV a "Pseudo VCF":

```

x['QUAL'] = '.'
x['FILTER'] = 'PASS'
x['INFO'] = '.'
x['ID'] = x[['#CHROM', 'POS', 'REF', 'ALT', 'gene', 'binarized_label', 'sample_weight']].astype(str).agg('_'.join, axis=1)

# Reorder
x = x[['#CHROM', 'POS', 'ID', 'REF', 'ALT', 'QUAL', 'FILTER', 'INFO']]
# Make sure it isn't a copy or a weakref
x._is_copy = None

```

_Note: the ID column is specifically designed this way so you can easily map back the original sample weight and binarized_label._

VEP does require header fields for the contig, use the following pseudo header to trick VEP into thinking it is an actual VCF:

```
pseudo_header = ['##fileformat=VCFv4.2',
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
                 '##fileDate=20200320']
```

Your interactive Python shell look something similar to this (variable names can vary):

```

import gzip

file = '/path/to/some/file.vcf.gz'

with gzip.open(file, 'wt') as pseudo_vcf:
    for line in pseudo_header:
        pseudo_vcf.write(f'{line}\n')

x.to_csv(file, sep='\t', na_rep='.', index=False, mode='a', compression='gzip')
```

Perform the same steps for both datasets. 

Now that you have made your pseudo-vcf from the train-test and validation datasets, it's time to annotate through VEP.

A shell script is supplied within "utility_scripts" that requires an input, output and assembly argument. 
It is essentially a script to make calling VEP consistent, you may use a manual method too, whatever suits your fancy. 
Just make sure the VEP arguments are the same in the script as your manual call. 
To convert over the GRCh37 variants to GRCh38, I've supplied a conversion script within "utility_scripts". 
This script uses picard to liftover GRCh37 variants to GRCh38.

### Post-VEP (GRCh37)

Now that you have your post-VEP train-test and validation VCF datasets, it is time to use the `vep_to_tsv.sh` script in utility_scripts to convert the VEP VCF back to TSV.
Once that is done, you're not done yet, since the CAPICE train protocol still requires some columns that are not present (binarized_label and sample_weight).
This is done by expanding the originally created ID column.

Expanding can be performed in multiple ways, the way I like to do it is as follows:

```python
import pandas as pd

x = pd.read_csv('/path/to/vep_converted.tsv.gz', sep='\t', na_values='.')
# Dropping the variants that are intergenic
x.drop(index=x[x['%SYMBOL'].isnull()].index, inplace=True)

# Making sure that the label is representative for the gene it was originally for
x.drop(index=x[x['%SYMBOL'] != x['%ID'].str.split('_', expand=True)[4]].index, inplace=True)

# Make sure that you've followed the instructions and the binarized label should be on the 6th element of ID
x['binarized_label'] = x['%ID'].str.split('_', expand=True)[5].astype(float)

# Make sure that sample_weight is the last element in ID
x['sample_weight'] = x['%ID'].str.split('_', expand=True)[6].astype(float)

# Drop everything that doesn't have a binarized_label, also drop unused columns
x.drop(index=x[x['binarized_label'].isnull()].index, columns=['%ID', '%gnomAD_AF'], inplace=True)

x.to_csv('/path/to/merge_output.tsv.gz', sep='\t', index=False, compression='gzip', na_rep='.')

```

_OPTIONAL: you can check statistics of your samples by performing something as simple as `merge[['binarized_label', 'sample_weight']].value_counts()`_

Now your dataset is ready to be used in training. The validation dataset also requires these steps to map the original binarized_label back to the dataset.

### Post-VEP (GRCh38)

Mapping back the Genome build 38 variants is a bit of a hassle, as you can no longer map back variants based on CHROM, POS, REF, and ALT. 
This is why we use the ID column to map back. However, still some additional steps are required.

```python

import numpy as np
import pandas as pd

x = pd.read_csv('/path/to/vep_converted_grch38.tsv.gz', sep='\t', na_values='.')
# Dropping the variants that are intergenic
x.drop(index=x[x['%SYMBOL'].isnull()].index, inplace=True)

# Clearning the TSV chromosomes
x['%CHROM'] = x['%CHROM'].str.split('chr', expand=True)[1]
y = np.append(np.arange(1, 23).astype(str), ['X', 'Y', 'MT'])
x.drop(x[~x['%CHROM'].isin(y)].index, inplace=True)

# Cleaning up LOC genes
x.drop(index=x[x['%ID'].str.split('_', expand=True)[4] != x['%SYMBOL']].index, inplace=True)

# Make sure that you've followed the instructions and the binarized label should be on the 6th element of ID
x['binarized_label'] = x['%ID'].str.split('_', expand=True)[5].astype(float)

# Make sure that sample_weight is the last element in ID
x['sample_weight'] = x['%ID'].str.split('_', expand=True)[6].astype(float)

# As of current, the gnomad allele frequency is not used and still in development. It will likely be used in balancing.
x.drop(columns=['%ID', '%gnomAD_AF'], inplace=True)

# Drop duplicate entries
x.drop_duplicates(inplace=True)

x.to_csv('/path/to/merge_output.tsv.gz', sep='\t', index=False, compression='gzip', na_rep='.')

```

### Training

Training is quite simple. I would highly suggest starting it as a job on a cluster, as it takes a while to train. 
I'd suggest starting the job with a runtime of 2 days.

For the JSON, the example json can be used in the CAPICE_example folder of CAPICE itself.

Just run the training protocol of CAPICE through `python3 -v capice.py train -i /path/to/train.tsv.gz -m /path/to/impute.json -o /path/to/output/`.


### Performance measurements

