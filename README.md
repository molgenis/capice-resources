# capice-resources

Repository for resource files for CAPICE and updating CAPICE model. It contains serveral modules listed below. Each
module contains their own README (if applicable) describing how to use them.

## Installation

Install should be as easy as `pip install .`. If not, please refer to manual install of the virtual environment and the
required packages defined within setup.py.

## Modules:

### validation

Validation is not really a module, but more a folder to contain plots of supporting evidence of a model's performance
per GitHub release.

### train_data_creator

The module train_data_creator is here to create new CAPICE train-test and validation datasets. For more information,
refer to the readme within the module.

### new_model_validator (**currently still WIP**)

WIP till CAPICE 3.0.0 is released, then newer generation CAPICE models can be compared with each other with relative
ease.

### utility_scripts

utility_scripts contains a couple of bash scripts for ease of use, which include but are not limited to lifting over
variants to GRCh38, running VEP104 and converting a VEP VCF output to TSV. 
It is advised to use these scripts as they maintain a level of consistency throughout the lifespan of CAPICE.

- liftover_variants.sh:

The script liftover_variants.sh converts a VCF containing GRCh37 variants to GRCh38 variants.

- vep_to_tsv.sh:

The vep_to_tsv.sh converts the VEP output VCF back to TSV with all required columns 
(added features or removed features have to be manually added and/or removed according to the decisions made.
For instance, if feature `CADD_score` is added, within the pre_header `\tCADD_score` has to be added, according to the column name the new feature has.).

## Usage

### TLDR

_(For a more detailed explanation on creating the train-test and validation datasets, please see the REAMDE in
train_data_creator)_

1. Make new CAPICE release, containing added or removed processors and/or code changes supporting a new model.
2. Download latest non-public GRCh37 VKGL (GCC cluster `/apps/data/VKGL`)
   and [Clinvar](https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh37/) datasets.
3. Use [train_data_creator](./train_data_creator/README.md) to create a train-test and validation VCFs.
4. Make capice-resources GitHub release. 
5. Attach both train-test and validation VCFs to capice-resources release.
6. Download the latest VEP release from the [Molgenis Cloud](https://download.molgeniscloud.org/downloads/vip/images/)
7. Use the singularity image, combined with the latest VEP cache to annotate the VCF files.
8. (Optional for XGBoost 0.72.1 models) Upload the validation.vcf to CADD1.4-GRCh37 for annotation.
9. Lift over not-annotated VCFs to GRCh38.
10. Use the VEP singularity image to annotate the GRCh38 VCF files.
11. (Optional for XGBoost 0.71.1 models) Upload the validation.vcf to CADD1.4-GRCh38 for annotation.
12. (Optional when new feature is introduced or removed) Add (or remove) feature to pre_header in bash
    script `vep_to_tsv.sh`.
13. Convert VEP annotated VCFs back to TSV.
14. Process TSV (GRCh37):
15. Dropping duplicates (duplicated over all columns).
16. Dropping variants without genes.
17. Dropping variants where the genes from ID and SYMBOL mismatch.
18. Add back binarized_label and sample_weight from ID.
19. Drop variants without binarized_label (sample_weight is not necessary).
20. Drop variants that do not have a binarized_label of either 0.0 or 1.0.
21. Drop variants that do not have a sample_weight of 0.8, 0.9 or 1.0.
22. Drop the ID and (if present) gnomAD_AF columns.
23. Export to TSV.
24. Repeat for validation (GRCh37).
25. Repeat for train-test and validation (GRCh38), __but__ additionally process the chromosome column to have the column
    only contain 1 through 22, X, Y and MT.
26. Update imputing JSON accordingly to the newly features added and/or removed.
27. Train new model with processed train-test TSV.
28. Attach new models to CAPICE release.
29. Use new model to generate CAPICE results file of the validation TSV.
30. Use old model to generate CAPICE results file of the same validation TSV.
31. Merge old results with new results, in combination with their true original binarized label and Consequence (true original label and Consequence can be obtained from the VEP output VCF/TSV, combination of the ID column and Consequence column).
32. Plot global AUC comparison between old and new results and violinplot comparison between old and new scores.
33. Repeat step 23 but for each and every Consequence.
34. Export plots to the validation directory, following the release structure.

## Making train-test and validation VCF files

Download the latest non-public GRCh37 VKGL (GCC `/apps/data/VKGL/GRCh37/vkgl_consensus_*.tsv`)
and [Clinvar](https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh37/) datasets and simply supply them to main.py within
train_data_creator. For further details, use `python3 main.py -h` or refer to the README in the train_data_creator
module.

## VEP

VEP is used to add annotations to the train-test and validation files. The following command is a good representation of what VEP command should be called:
```commandline
vep --input_file *path to your input file* --format vcf --output_file *path to your output file* --vcf --compress_output gzip --regulatory --sift s --polyphen s --domains --numbers --canonical --symbol --shift_3prime 1 --allele_number --no_stats --offline --cache --dir_cache */path/to/cache/104* --species "homo_sapiens" --assembly *GRCh37 or GRCh38* --refseq --use_given_ref --exclude_predicted --use_given_ref --flag_pick_allele --force_overwrite --fork 4 --dont_skip --allow_non_variant --per_gene
```
_(--input_file, --output_file and --assembly have to be manually altered)_

_Command can vary based on the training features._

**Comparing an XGBoost 0.72.1 (CAPICE 2.0.0 or lower) to a new XGBoost 1.4.2 model, upload the validation.vcf.gz to [CADD](https://cadd.gs.washington.edu/score) for annotation.** (set "INCLUDE ANNOTATIONS" to True)

## Post-VEP processing

First convert the VEP output VCF back to TSV using the `vep_to_tsv.sh` _(Note: pre_header must be altered according to the new features or removed features)_.
**WARNING: Drop all columns that are not wanted within training, such as the ID column.** This step can be performed for all train-test and validation VCFs for both GRCh37 and 38.

### GRCh37

Then process the TSV to remove duplicates and variants that are not really within the initial train-test or validation datasets, as following:

```python
import pandas as pd

x = pd.read_csv('/path/to/vep_converted.tsv.gz', sep='\t', na_values='.')

# Dropping full on duplicates
x.drop_duplicates(inplace=True)

# Dropping the variants that are intergenic
x.drop(index=x[x['%SYMBOL'].isnull()].index, inplace=True)

# Making sure that the label is representative for the gene it was originally for
x.drop(index=x[x['%SYMBOL'] != x['%ID'].str.split('_', expand=True)[4]].index, inplace=True)

# Make sure that you've followed the instructions and the binarized label should be on the 6th element of ID
x['binarized_label'] = x['%ID'].str.split('_', expand=True)[5].astype(float)

# Make sure that sample_weight is the last element in ID
x['sample_weight'] = x['%ID'].str.split('_', expand=True)[6].astype(float)

# Drop everything that doesn't have a binarized_label, also drop unused columns
x.drop(index=x[x['binarized_label'].isnull()].index, columns=['%ID'], inplace=True)

# CAPICE 3.0.0-beta1 iteration 1 and 2, and beta 2 iteration 1 contains a bug that causes a binarized label to become 2. Dropping it.
x.drop(index=x[~x['binarized_label'].isin([0.0, 1.0])].index, inplace=True)

# Also do the same for the sample weights (WARNING: these have to match the initially set sample weights as displayed in the one table at the start of the README.md)
x.drop(index=x[~x['sample_weight'].isin([0.8, 0.9, 1.0])].index, inplace=True)

x.to_csv('/path/to/vep_converted_processed.tsv.gz', sep='\t', index=False, compression='gzip', na_rep='.')

# (optional) show statistics on your dataset
x[['binarized_label', 'sample_weight']].value_counts()
```

Now your TSV is ready for training.

### GRCh38

GRCh38 requires a bit more processing, specifically on the chromosome column, as following:

```python

import numpy as np
import pandas as pd

# Reading in data
x = pd.read_csv('/path/to/vep_converted_grch38.tsv.gz', sep='\t', na_values='.')

# Drop duplicate entries
x.drop_duplicates(inplace=True)

# Dropping the variants that are intergenic
x.drop(index=x[x['%SYMBOL'].isnull()].index, inplace=True)

# Cleaning the TSV chromosomes
x['%CHROM'] = x['%CHROM'].str.split('chr', expand=True)[1]
y = np.append(np.arange(1, 23).astype(str), ['X', 'Y', 'MT'])
x.drop(x[~x['%CHROM'].isin(y)].index, inplace=True)

# Cleaning up mismatched genes
x.drop(index=x[x['%ID'].str.split('_', expand=True)[4] != x['%SYMBOL']].index, inplace=True)

# Make sure that you've followed the instructions and the binarized label should be on the 6th element of ID
x['binarized_label'] = x['%ID'].str.split('_', expand=True)[5].astype(float)

# Make sure that sample_weight is the last element in ID
x['sample_weight'] = x['%ID'].str.split('_', expand=True)[6].astype(float)

# Drop everything that doesn't have a binarized_label, also drop unused columns
x.drop(index=x[x['binarized_label'].isnull()].index, columns=['%ID'], inplace=True)

# CAPICE 3.0.0-beta1 iteration 1 and 2, and beta 2 iteration 1 contains a bug that causes a binarized label to become 2. Dropping it.
x.drop(index=x[~x['binarized_label'].isin([0.0, 1.0])].index, inplace=True)

# Also do the same for the sample weights (WARNING: these have to match the initially set sample weights as displayed in the one table at the start of the README.md)
x.drop(index=x[~x['sample_weight'].isin([0.8, 0.9, 1.0])].index, inplace=True)

x.to_csv('/path/to/vep_converted_grch38_processed.tsv.gz', sep='\t', index=False, compression='gzip', na_rep='.')

# (optional) show statistics on your dataset
x[['binarized_label', 'sample_weight']].value_counts()
```
## Training

Before the training module of CAPICE can be called, make sure your impute JSON used within training is up to date on your newly added and/or removed features.

Training a new model is rather easy, but takes quite a bit of time. It is recommended to start a slurm job on the GCC cluster and to let it run overnight.

The training module can be activated with the following command:

`python3 capice.py -v train -i /path/to/processed/train_test.tsv.gz -m /path/to/up/to/date/impute.json -o /path/to/output.pickle.dat`

_(Make sure that your (virtual) environment contains the right Python version and packages.)_

## Generating results

### XGBoost 0.90 vs XGBoost 1.4.2 models

By now, you should already have a CADD 1.4 annotated output file for "old" CAPICE to score. 
Get the CAPICE result file for both old generation and new generation. 
I prefer to use CAPICE 1.3.1 for "old" CAPICE. For "new" CAPICE, use your latest release, as the model file will try and match the
version to the CAPICE version. 

### XGBoost 1.4.2 vs XGBoost 1.4.2 models

Work in Progress

## Validate

The 2 old and new result files have to be merged back together, combined with their true original binarized_label and the variant Consequence.
Both binarized_label and Consequence can be found in the VEP output VCF or TSV (if it still contains the ID column).

Clean up the variants that can't be merged with their true binarized_label or to their new label.

Then use matplotlib (or seaborn, or whatever) to plot the "old" AUC vs the "new" AUC, combined with Violinplots of the distribution of the score values of the old model, new model and their true labels.
Do the same on a per Consequence level.

Comparing an "old" model (generated with CAPICE 1.3.1) to a new model (CAPICE-3.0.0-beta1) will look something like this:

```python3
from matplotlib import pyplot as plt
from sklearn.metrics import roc_auc_score
import pandas as pd
import math

# Reading in data
cadd = pd.read_csv('/path/to/old_capice_output.txt', sep='\t')
original_labels = pd.read_csv('/path/to/vep_output_validation.tsv.gz', sep='\t')
vep = pd.read_csv('/path/to/new_capice_output.tsv.gz', sep='\t')

# Making merge column
cadd['ID'] = cadd[['chr_pos_ref_alt', 'GeneName']].astype(str).agg('_'.join, axis=1)
vep['ID'] = vep[['chr', 'pos', 'ref', 'alt', 'gene_name']].astype(str).agg('_'.join, axis=1)

# Getting the true original labels
original_labels['binarized_label'] = original_labels['%ID'].str.split('_', expand=True)[5].astype(float)
original_labels['ID'] = original_labels['%ID'].str.split('_', expand=True)[:5].astype(str).agg('_'.join, axis=1)

# Preparing all datasets
vep = vep[['ID', 'score']]
vep._is_copy = None
vep.rename(columns={'score': 'score_new'}, inplace=True)
cadd.rename(columns={'probabilities': 'score_old'})
original_labels = original_labels[['ID', 'binarized_label']]
original_labels._is_copy = None

# Merging
merge = cadd.merge(original_labels, on='ID', how='left')
merge.drop(index=merge[merge['binarized_label'].isnull()].index, inplace=True)
merge = merge.merge(vep, on='ID', how='left')
merge.drop(index=merge[merge['score_new'].isnull()].index, inplace=True)

# Preparing plots
consequences = merge['Consequence'].unique()
ncols = 4
nrows = math.ceil((consequences.size / ncols) + 1)
index = 1
fig_auc = plt.figure(figsize=(20, 40))
fig_auc.suptitle('Old model vs new model AUC comparison.')
fig_vio = plt.figure(figsize=(20, 40))
fig_vio.suptitle('Old model vs new model score distributions.')

# Calculating global AUC
auc_old = round(roc_auc_score(merge['binarized_label'], merge['score_old']), 4)
auc_new = round(roc_auc_score(merge['binarized_label'], merge['score_new']), 4)

# Plotting global AUC
ax_auc = fig_auc.add_subplot(nrows, ncols, index)
ax_auc.bar(1, auc_old, color='red', label=f'Old: {auc_old}')
ax_auc.bar(2, auc_new, color='blue', label=f'New: {auc_new}')
ax_auc.set_title(f'Global (n={merge.shape[0]})')
ax_auc.set_xticks([1, 2], ['Old', 'New'])
ax_auc.set_xlim(0.0, 3.0)
ax_auc.set_ylim(0.0, 1.0)
ax_auc.legend(loc='lower right')

# Plotting Violinplot for global
ax_vio = fig_vio.add_subplot(nrows, ncols, index)
ax_vio.violinplot(merge[['score_old', 'binarized_label', 'score_new']])
ax_vio.set_title(f'Global (n={merge.shape[0]})')
ax_vio.set_xticks([1, 2, 3], ['Old', 'True', 'New'])
ax_vio.set_xlim(0.0, 4.0)
ax_vio.set_ylim(0.0, 1.0)

# Global plots have been made, now for each consequence
index = 2
for consequence in consequences:
    print(f'Currently processing: {consequence}')
    # Subsetting
    subset = merge[merge['Consequence'] == consequence]

    # Calculating
    # Try except because when an consequence is encountered with only 1 label, roc_auc_score will throw an error
    try:
        auc_old = round(roc_auc_score(subset['binarized_label'], subset['score_old']), 4)
    except ValueError:
        print(f'For consequence {consequence}, AUC old could not be calculated.')
        continue
    try:
        auc_new = round(roc_auc_score(subset['binarized_label'], subset['score_new']), 4)
    except ValueError:
        print(f'For consequence {consequence}, AUC new could not be calculated.')
        continue

    # Plotting auc
    ax_auc = fig_auc.add_subplot(nrows, ncols, index)
    ax_auc.bar(1, auc_old, color='red', label=f'Old: {auc_old}')
    ax_auc.bar(2, auc_new, color='blue', label=f'New: {auc_new}')
    ax_auc.set_title(f'{consequence} (n={subset.shape[0]})')
    ax_auc.set_xticks([1, 2], ['Old', 'New'])
    ax_auc.set_xlim(0.0, 3.0)
    ax_auc.set_ylim(0.0, 1.0)
    ax_auc.legend(loc='lower right')

    # Plotting Violinplot for global
    ax_vio = fig_vio.add_subplot(nrows, ncols, index)
    ax_vio.violinplot(subset[['score_old', 'binarized_label', 'score_new']])
    ax_vio.set_title(f'{consequence} (n={subset.shape[0]})')
    ax_vio.set_xticks([1, 2, 3], ['Old', 'True', 'New'])
    ax_vio.set_xlim(0.0, 4.0)
    ax_vio.set_ylim(0.0, 1.0)

    index += 1

fig_auc.savefig('/path/to/save/directory/aucs.png')
fig_vio.savefig('/path/to/save/directory/violins.png')
```

Compare the results of Old vs New and discus within the team, decide on next steps.


## Common issues

- Training with my generated dataset causes warning ValueError: multiclass format is not supported, resulting in average
  CV performance of NaN.

This one is a bit tricky, but it comes down with a bug somewhere within creating the ID column. One of the binarized
labels is set to 2, origin is unknown. Is fixed as per CAPICE 3.0.0-beta2.