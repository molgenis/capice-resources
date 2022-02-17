# Train data creator

###### Resource module for CAPICE to create new train-test and validation datasets

## Usage

`python3 main.py -iv path/to/vkgl_consensus.tsv.gz -ic path/to/clinvar.vcf.gz -o path/to/existing/output/directory`

_Note: -iv needs to be the non-public VKGL, public will throw an KeyNotFoundError._

_Note 2: the parent of the output directory has to exist. train_data_creator will, at most, create only 1 new directory._

## Theory

(data_preprocessor.py)

Step 1 is to load in the different type datasets, which is not all that easy.

VCF files have headers that can't be directly parsed into VCF. The amount of lines are obtained and provided to the
pandas parser.

The VKGL TSV is easier to parse since that doesn't require extra skips.

After that the files are validated.

For VKGL the file follows the following path:

- Correcting the TSV to VCF-like column names.
- Correcting the consensus-classification of "Classified by one lab" to the actual classification of the lab (also
  setting the amount of labs for that variant to 1 for review status).
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

Both datasets are merged, with the column "source" indicating their true origin and the originally loaded datasets are
deleted to preserve RAM usage.

(duplicate_processor.py)

Once merged, duplicates have to be removed since it is possible that VKGL samples are present within ClinVar. Duplicates
are dropped if all of the following columns are duplicates:

- CHROM
- POS
- REF
- ALT
- gene
- class

Since the keep in pandas.DataFrame.drop_duplicates() is not defined, the first duplicate will remain present while the
rest are dropped. Since VKGL is appended to the ClinVar dataset, the ClinVar variant will be kept.
_Note: it might be possible that duplicate variants are still present with conflicting classes, since those do not count
as duplicates. We don't think this will be an issue due to the amount of samples._

Now that we have an assembled large dataset, we can start building the train-test and validation datasets. __But before
we can do that__, it is useful to apply the sample weights already. Sample weights is what tells XGBoost (and other
machine learning algorithms) how well it should trust the particular sample. As of current, the following ClinVar Gold
Star ratings are used to apply the following sample weights:

| Gold star rating | Sample weight |
|:----------------:|:-------------:|
|         0        |      Removed      |
|         1        |      0.8      |
|         2        |      0.9      |
|         3        |      1.0      |
|         4        |      1.0      |

These sample weights follow the idea that [Li et al.](https://genomemedicine.biomedcentral.com/articles/10.1186/s13073-020-00775-w) originally had for the initial model.
Applying sample weights that are lower than 0.8 have the chance to influence the end score too much in such a way that scores will not reach 0.0 for benign and 1.0 for pathogenic (beta1 iteration 1). 
Higher quality variants (2 labs or more confirming the consensus) should be rewarded with a higher sample weight.

Now that sample weights have been mapped and applied, the large dataset can be split into the train-test and validation
datasets.

(split_datasets.py)

The most important part about the splitting of the large dataset into the train-test and validation datasets is that the
validation dataset is of high quality. This is done by randomly sampling 50% of high quality pathogenic variants (review
score 2 or higher, which means at least 2 labs have confirmed the consensus). 
Once 50% of high quality pathogenic variants have been sampled, an equal amount of benign samples of the same quality is sampled.
These sampled variants now form the validation dataset. 
These validation samples are then merged back to the training dataset, after which an `pd.drop_duplicates(keep=False)` is performed, 
so all validation samples that were still in the train-test dataset are removed (since `sample` does not remove the dataframe entries).

This results in the train-test and validation datasets, 
that are exported to the output argument after adding a pseudo-vcf header and pseudo-vcf columns (and merging critical information to the ID column).
