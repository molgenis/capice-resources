# Train data creator
######Resource module for CAPICE to create new train-test and validation datasets

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
|         0        |      0.2      |
|         1        |      0.6      |
|         2        |      0.8      |
|         3        |      0.9      |
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

### Follow up steps to train a new CAPICE model


