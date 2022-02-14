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
   1. Steps:
   2. Newly added features have been added to the [impute json](https://github.com/molgenis/capice/blob/master/CAPICE_example/example_impute_values.json) and/or deprecated features have been removed.
   3. Apply changes in features to PRE_HEADER in the [CAPICE conversion tool](https://github.com/molgenis/capice/blob/master/scripts/convert_vep_vcf_to_tsv_capice.sh).
   4. Annotate new training VCF using VEP and convert the VCF using the [CAPICE conversion tool](https://github.com/molgenis/capice/blob/master/scripts/convert_vep_vcf_to_tsv_capice.sh) (raw file: <PLACEHOLDER_LINK_train_example_raw.vcf.gz>) (note: use `-t` when using the conversion tool)
   5. Make training TSV train ready using <PLACEHOLDER_LINK_vep_to_train.py>.
   6. Use newly generated training TSV to create new [PoC](https://github.com/molgenis/capice/blob/master/tests/resources/xgb_booster_poc.pickle.dat) model.
   7. Update <PLACEHOLDER_LINK_capice_input.tsv.gz> (raw file: <PLACEHOLDER_LINK_capice_input_raw.vcf.gz>) with altered features.
   8. Update [breakends_vep.tsv.gz](https://github.com/molgenis/capice/blob/master/tests/resources/breakends_vep.tsv.gz) (raw file: [breakends.vcf.gz](https://github.com/molgenis/capice/blob/master/tests/resources/breakends.vcf.gz)) with altered features.
   9. Update [edge_cases_vep.tsv.gz](https://github.com/molgenis/capice/blob/master/tests/resources/edge_cases_vep.tsv.gz) (raw file: [edge_cases.vcf.gz](https://github.com/molgenis/capice/blob/master/tests/resources/edge_cases.vcf.gz)) with altered features.
   10. Update [symbolic_alleles_vep.tsv.gz](https://github.com/molgenis/capice/blob/master/tests/resources/symbolic_alleles_vep.tsv.gz) (raw file: [symbolic_alleles.vcf.gz](https://github.com/molgenis/capice/blob/master/tests/resources/symbolic_alleles.vcf.gz)) with altered features.
   11. Run [CAPICE](https://github.com/molgenis/capice) tests.
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
11. Convert VEP annotated VCFs back to TSV using [CAPICE conversion tool](https://github.com/molgenis/capice/blob/master/scripts/convert_vep_vcf_to_tsv_capice.sh) (using `-t`)
    1. `capice/scripts/convert_vep_vcf_to_tsv_capice.sh -i </path/to/vep.vcf.gz> -o </path/to/vep.tsv.gz> -t`
12. Process GRCH37 TSV 
    1. `python3 ./utility_scripts/vep_to_train.py -i /path/to/vep.tsv.gz -o /path/to/vep_processed.tsv.gz`
13. Repeat for GRCh37 validation (see step 12)
14. Repeat steps 11 and 12 for train-test and validation for GRCh38 (add the `-a` flag to the `vep_to_train.py`).
15. Update imputing JSON accordingly to the newly features added and/or removed.
16. Make sure the latest release of CAPICE made in step 1 is available on the GCC cluster
    1. `pip install capice` (be sure to install within a virtual environment or use the singularity image)
17. Use the JSON made in step 16 and the train-test TSV made in step 12 to start the train protocol of CAPICE
    1. You may want to use a custom script that loads the latest Python module, activates the virtual environment and activates the and then activates the train protocol. It can take 5 hours for a new model to train.
    2. `module load <python>`
    3. `source ./capice/venv/bin/activate`
    4. `capice train -i </path/to/train-test.tsv.gz> -m </path/to/impute.json> -o </path/to/output>` 
18. Attach new models to [CAPICE](https://github.com/molgenis/capice) and [capice-resources](https://github.com/molgenis/capice-resources) releases.
19. Use new model generated in step 20 to generate CAPICE results file of the validation TSV.
20. Use latest non `Release Candidate` model to generate CAPICE results file of the same validation TSV.
21. Use `compare_old_model.py` in `utility_scripts` to compare performance of an old model to a new model.
    1. `compare_old_model.py --old_model_results </path/to/old_capice_results.tsv> --vep_processed_capice_input </path/to/validation_vep.tsv.gz> --new_model_results </path/to/validation_vep_capice.tsv.gz> --output </path/to/rcX>`

## Making train-test and validation VCF files

Download the latest non-public GRCh37 VKGL (GCC `/apps/data/VKGL/GRCh37/vkgl_consensus_*.tsv`)
and [Clinvar](https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh37/) datasets and simply supply them to main.py within
train_data_creator. For further details, use `python3 main.py -h` or refer to the README in the train_data_creator
module.

## VEP

VEP is used to add annotations to the train-test and validation files. The following command is a good representation of what VEP command should be called:
```commandline
vep --input_file <path to your input file> --format vcf --output_file <path to your output file> --vcf --compress_output gzip --sift s --polyphen s --numbers --symbol --shift_3prime 1 --allele_number --no_stats --offline --cache --dir_cache */path/to/latest/vep/cache* --species "homo_sapiens" --assembly *GRCh37 or GRCh38* --refseq --use_given_ref --exclude_predicted --use_given_ref --flag_pick_allele --force_overwrite --fork 4 --dont_skip --allow_non_variant --per_gene
```
_(`--input_file`, `--output_file` and `--assembly` have to be manually altered)_

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

Merging the old and new validation datafiles happens within `utility_scripts/compare_old_model.py`. 
This script merges the old results file with a file containing the original labels (the direct output of a TSV converted VEP output using the `-t` flag of `conver_vep_vcf_to_tsv_capice.sh` of [CAPICE](https://github.com/molgenis/capice/blob/master/scripts/convert_vep_vcf_to_tsv_capice.sh) is perfect). 
After that merge and some cleanup of columns that are not going to be used anymore, 
the new results file is merged on top of the old results merged with their original true labels.

After this merge, AUC is calculated globally, as well as an absolute score difference between the predicted score and the true label.
These global results are then plotted, and AUC calculations are performed over all consequences present within the **old capice** datafile, as well as the absolute score difference.

This absolute score difference tells us something of how close the scores are to the true label, where 1 means the score is far off from the true label and 0 means the score matches the label. We want 0.

Furthermore, a table of the feature importances of the new model is plotted aswell, so you can see what is and what is not important.

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
