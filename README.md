# capice-resources

Repository for resource files for CAPICE and updating CAPICE model. It contains serveral modules listed below. Each
module contains their own README (if applicable) describing how to use them.

## Installation

Install should be as easy as `pip install -e '.[test]'`. 
To test the individual modules, change directory to the specific module and run `pytest`.

## Modules:

### validation

Validation is not really a module, but more a folder to contain plots of supporting evidence of a model's performance
per GitHub release.

### train_data_creator

The module train_data_creator is here to create new CAPICE train-test and validation datasets. For more information,
refer to the readme within the module.

### utility_scripts

utility_scripts contains a couple of bash scripts for ease of use, which include but are not limited to lifting over
variants to GRCh38, running VEP104 and converting a VEP VCF output to TSV. 
It is advised to use these scripts as they maintain a level of consistency throughout the lifespan of CAPICE.

- liftover_variants.sh:

The script liftover_variants.sh converts a VCF containing GRCh37 variants to GRCh38 variants.

- vep_to_tsv.sh:

The vep_to_tsv.sh converts the VEP output VCF back to TSV with all required columns.
If features are added/removed, be sure to adjust the `pre_header` variable within this bash script accordingly.
For instance, if feature `CADD_score` is added, within pre_header `\tCADD_score` has to be added.

## Usage

### TLDR

_(For a more detailed explanation on creating the train-test and validation datasets, please see the README in
[train_data_creator](./train_data_creator/README.md))_

1. Make new [CAPICE](https://github.com/molgenis/capice) release, containing added or removed processors and/or code changes supporting a new model.
2. Download latest non-public GRCh37 VKGL (`/apps/data/VKGL/GRCh37`)
   and [Clinvar](https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh37/) datasets.
3. Use [train_data_creator](./train_data_creator/README.md) to create a train-test and validation VCFs.
   1. `python3 ./train_data_creator/main.py --input_input_vkgl </path/to/vkgl_nonpublic.tsv> --input_clinvar </path/to/clinvar.vcf.gz> -o </path/to/output>`
4. Make [capice-resources](https://github.com/molgenis/capice-resources) GitHub release, matching the CAPICE release in step 1. 
5. Attach both train-test and validation VCFs to [capice-resources](https://github.com/molgenis/capice-resources) release.
6. Download the latest VEP release from the [Molgenis Cloud](https://download.molgeniscloud.org/downloads/vip/images/)
7. Use the VEP singularity image, combined with the latest VEP cache to annotate the VCF files.
   1. `singularity exec --bind /apps,/groups,/tmp vep <command>` (See [VEP](#VEP) for the command)
8. (Optional for XGBoost 0.72.1 models) Upload the validation.vcf to [CADD1.4-GRCh37](https://cadd.gs.washington.edu/score) for annotation.
9. Lift over not-annotated VCFs to GRCh38 using `lifover_variants.sh`. 
   1. `sbatch lifover_variants.sh -i </path/to/step3.vcf.gz> -o </path/to/output/directory/file>` (please note: do not supply an extension as it doesn't produce a single file)
10. Use the VEP singularity image to annotate the GRCh38 VCF files.
11. (Optional when new feature is introduced or removed) Add (or remove) feature to PRE_HEADER in bash
    script `vep_to_tsv.sh`.
12. Convert VEP annotated VCFs back to TSV using `vep_to_tsv.sh`
    1. `./utility_scripts/vep_to_tsh.sh -i </path/to/vep.vcf.gz> -o </path/to/vep.tsv.gz>`
13. Process GRCH37 TSV 
    1. `python3 ./utility_scripts/vep_to_train.py -i /path/to/vep.tsv.gz -o /path/to/vep_processed.tsv.gz`
14. Repeat for GRCh37 validation (see step 13)
15. Repeat steps 12 and 13 for train-test and validation for GRCh38 (add the `-a` flag to the `vep_to_train.py`).
16. Update imputing JSON accordingly to the newly features added and/or removed.
17. Make sure the latest release of CAPICE made in step 1 is available on the GCC cluster
    1. `pip install capice` (be sure to install within a virtual environment or use the singularity image)
18. Use the JSON made in step 16 and the train-test TSV made in step 12 to start the train protocol of CAPICE
    1. You may want to use a custom script that loads the latest Python module, activates the virtual environment and activates the and then activates the train protocol. It can take 5 hours for a new model to train.
    2. `module load <python>`
    3. `source ./capice/venv/bin/activate`
    4. `capice train -i </path/to/train-test.tsv.gz> -m </path/to/impute.json> -o </path/to/output>` 
19. Attach new models to [CAPICE](https://github.com/molgenis/capice) and [capice-resources](https://github.com/molgenis/capice-resources) releases.
20. Use new model generated in step 20 to generate CAPICE results file of the validation TSV.
21. Use latest non `Release Candidate` model to generate CAPICE results file of the same validation TSV.
22. Merge old results with new results, in combination with their true original binarized label and Consequence (true original label and Consequence can be obtained from the VEP output VCF/TSV, combination of the ID column and Consequence column). 
    1. Steps 22 through 25 are shown in [Validate](#Validate).
23. Plot global AUC comparison between old and new results and violinplot comparison between old and new scores.
24. Repeat step 23 but for each and every Consequence.
25. Export plots to the validation directory, following the release structure. 

## Making train-test and validation VCF files

Download the latest non-public GRCh37 VKGL (GCC `/apps/data/VKGL/GRCh37/vkgl_consensus_*.tsv`)
and [Clinvar](https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh37/) datasets and simply supply them to main.py within
train_data_creator. For further details, use `python3 main.py -h` or refer to the README in the train_data_creator
module.

## VEP

VEP is used to add annotations to the train-test and validation files. The following command is a good representation of what VEP command should be called:
```commandline
vep --input_file <path to your input file> --format vcf --output_file <path to your output file> --vcf --compress_output gzip --regulatory --sift s --polyphen s --domains --numbers --canonical --symbol --shift_3prime 1 --allele_number --no_stats --offline --cache --dir_cache */path/to/latest/vep/cache* --species "homo_sapiens" --assembly *GRCh37 or GRCh38* --refseq --use_given_ref --exclude_predicted --use_given_ref --flag_pick_allele --force_overwrite --fork 4 --dont_skip --allow_non_variant --per_gene
```
_(--input_file, --output_file and --assembly have to be manually altered)_

_Command can vary based on the training features._

**Comparing an XGBoost 0.72.1 (CAPICE 2.0.0 or lower) to a new XGBoost 1.4.2 model, upload the validation.vcf.gz to [CADD](https://cadd.gs.washington.edu/score) for annotation.** (set "INCLUDE ANNOTATIONS" to True)

## Post-VEP processing

First convert the VEP output VCF back to TSV using the `vep_to_tsv.sh` _(Note: pre_header must be altered according to the new features or removed features)_.
**WARNING: Drop all columns that are not wanted within training, such as the ID column.** This step can be performed for all train-test and validation VCFs for both GRCh37 and 38.

Making the converted VEP TSV train-ready requires use of the `vep_to_train.py` in `utility_scripts`. This works for both GRCh37 and GRCh38 (GRCh38 only when the `-a` flag is supplied.)

This script makes sure that variants with the correct labels are preserved, so that the labels remains accurate for the variant.

## Training

Before the training module of CAPICE can be called, make sure your impute JSON used within training is up to date on your newly added and/or removed features.

Training a new model is rather easy, but takes quite a bit of time. It is recommended to start a slurm job on the GCC cluster and to let it run overnight.

The training module can be activated with the following command (assuming you have installed CAPICE the way it is supposed to be: `pip install .` or `pip install capice`):

`capice -v train -i /path/to/processed/train_test.tsv.gz -m /path/to/up/to/date/impute.json -o /path/to/output.pickle.dat`

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
import numpy as np
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
fig_box = plt.figure(figsize=(20, 40))
fig_box.suptitle('Old model vs new model score closeness (difference to true label)')

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

# Plotting the score differences to the true label
merge['score_diff_old'] = abs(merge['binarized_label'] - merge['score_old'])
merge['score_diff_new'] = abs(merge['binarized_label'] - merge['score_new'])
ax_box = fig_box.add_subplot(nrows, ncols, index)
ax_box.boxplot(
    [
        merge[merge['binarized_label'] == 0]['score_diff_old'],
        merge[merge['binarized_label'] == 0]['score_diff_new'],
        merge[merge['binarized_label'] == 1]['score_diff_old'],
        merge[merge['binarized_label'] == 1]['score_diff_new']
    ], labels=['B_old', 'B_new', 'P_old', 'P_new']
)
ax_box.set_title(f'Global (n={merge.shape[0]})')

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

    # Plotting boxplots
    ax_box = fig_box.add_subplot(nrows, ncols, index)
    ax_box.boxplot(
        [
            subset[subset['binarized_label'] == 0]['score_diff_old'],
            subset[subset['binarized_label'] == 0]['score_diff_new'],
            subset[subset['binarized_label'] == 1]['score_diff_old'],
            subset[subset['binarized_label'] == 1]['score_diff_new']
        ], labels=['B_old', 'B_new', 'P_old', 'P_new']
    )
    ax_box.set_title(f'{consequence} (n={subset.shape[0]})')

    index += 1

fig_auc.savefig('/path/to/save/directory/aucs.png')
fig_vio.savefig('/path/to/save/directory/violins.png')
fig_box.savefig('/path/to/save/directory/box.png')
```

Compare the results of Old vs New and discus within the team, decide on next steps.


## Common issues

- Training with my generated dataset causes warning ValueError: multiclass format is not supported, resulting in average
  CV performance of NaN.

This one is a bit tricky, but it comes down with a bug somewhere within creating the ID column. One of the binarized
labels is set to 2, origin is unknown. Is fixed as per CAPICE 3.0.0-beta2.

## FAQ

- I'm getting an `ValueError: invalid literal for int() with base 10: 'chr1'`, what's wrong?

You've likely downloaded a genome build 38, which has a different annotation for the chromosome. 
`train_data_creator` only supports build 37.
