[![Build Status](https://app.travis-ci.com/molgenis/capice-resources.svg?branch=main)](https://app.travis-ci.com/molgenis/capice-resources)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=molgenis_capice-resources&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=molgenis_capice-resources)

# capice-resources

Repository for resource files for CAPICE and updating CAPICE model. It contains several modules listed below. 

## Requirements
- CAPICE (personal git branch for development)
- [VIP](https://github.com/molgenis/vip) v7.4.0
- Python 3.10 or higher
- [Apptainer](https://apptainer.org/)

## Installation

1. Download/git clone the source code.
2. Run `pip --no-cache-dir install -e '.[test]'`

_Please note that for each module to properly function, the installation has to be completed._

To test the individual modules, change directory to the specific module and run `pytest`.

## Modules:

### balance_dataset

balance_dataset is a module dedicated to balancing out a CAPICE train-test and/or validation on a per-consequence per-allele frequency bin level.

Will output 2 TSV files: one dataset file that is balanced and a remainder dataset file.

For usage details, use `balance-dataset -h` or `python3 ./src/molgenis/capice_resources/balance_dataset -h`

### compare_model_features

compare_model_features is a module dedicated to compare 2 `capice explain` outputs.

Will output a file containing the normalized "gain" score and the feature ranking according to this normalized gain.

For usage details, use: `compare-model-features -h` or `python3 ./src/molgenis/capice_resources/compare_model_features -h`

### compare_model_performance

The module `compare_model_performance` is a module dedicated to obtain the difference in performance between 2 CAPICE models.

It takes the "validation" dataset (or benchmark dataset, containing "binarized labels") and the `capice predict` output files of 2 different models and measures the performance differences between them. 
Output plots to show the user the differences in performance between "model 1" and "model 2".

_Note that the filename of the score and "label" datasets will be displayed within the plots. It is up to the user to define easily distinguishable filenames._

For usage details, use: `compare-model-performance -h` or `python3 ./src/molgenis/capice_resources/compare_model_performance -h`

### process_vep

The module `process_vep` is a module available to process the `train-test` and `validation` VEP output TSVs (VCF to TSV using BCFTools, see usage of BCFTools below) back to usable files for the CAPICE training process.
The reason that this module requires both `train-test` and `validation` is so that duplicate entries between the supposed independently datasets are filtered out.
Please note that the input supplied to VEP is created using module `train_data_creator`, as this module adds additional information required by this module.

Use [this script](https://github.com/molgenis/capice/blob/main/scripts/convert_vep_vcf_to_tsv_capice.sh) to convert the VEP output VCF back to TSV.
What this script does is it creates a temporary output file using `bcftools +split-vep`, duplicating each entry if more entries exist for that variant (for example due to transcripts) and separating by a tab.
Then the `echo` call adds back the header to this temporary file and creates the final file.

For usage details, use: `process_vep -h` or `python3 ./src/molgenis/capice_resources/process_vep -h`

### threshold_calculator

The module `threshold_calculator` is a module that uses the "validation" (or benchmark dataset, containing "binarized labels") and a `capice predict` output file to find an optimal threshold according to the [CAPICE publication](https://genomemedicine.biomedcentral.com/articles/10.1186/s13073-020-00775-w#Sec2) (see: Methods: Threshold selection strategies).
It outputs both a plot with an overview of the supplied variants and the optimal recall threshold and a TSV containing all attempted thresholds with their performance metrics.

For usage details, use: `threshold-calculator -h` or `python3 ./src/molgenis/capice_resources/threshold_calculator -h`

### train_data_creator

The module `train_data_creator` is a module dedicated to creating `train-test` and independent `validation` datasets to be used in creating a new CAPICE model.
It uses as input the most recent [ClinVar](https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh37/) and [VKGL](https://vkgl.molgeniscloud.org/menu/main/background) to create these datasets.
For the validation dataset, only "high-quality" samples are randomly obtained from both files. All other samples are put into `train-test`. 

For usage details, see: `train-data-creator -h` or `python3 ./src/molgenis/capice_resources/train_data_creator -h`

## Additional scripts:

### slurm_run_vep.sh

Template sbatch script to run VEP on a Slurm cluster. Ensure it is up-to-date and paths (and the `bind` argument within `args`) are adjusted accordingly before
using!

### liftover_variants.sh

The script liftover_variants.sh converts a VCF containing GRCh37 variants to GRCh38 variants.
For this script the user must ensure paths and variables are set correctly!

## Usage

1. Update the CAPICE tool: 
   1. Make new branch for [CAPICE](https://github.com/molgenis/capice) and checkout this branch locally.
   2. Determine feature to add and check whether a VEP processor should be written for it (VEP processors usually don't
      have to be written for int/float values).
   3. Add feature to `capice/resources/train_features.json`.
   Make new branch for [CAPICE](https://github.com/molgenis/capice-resources) and checkout this branch locally.
   4. Update VEP command in the `capice-resources/src/utility_scripts/slurm_run_vep.sh`.
   5. Use `<capice-resources>/utility_scripts/create_poc.sh`
   ```shell
    APPTAINER_BIND=/groups sbatch \
    --output=<workdir>/poc.log \
    --error=<workdir>/poc.err \
    --export=APPTAINER_BIND create_poc.sh \
    -a "<bind>" \
    -n automate \
    -b "<path_to/bcftools-<version>.sif>" \
    -w "<workdir>" \
    -r "<path_to/capice-resources/>" \
    -p "<path_to/vip/>"
   ```
   1. Check the output log for test failures.
   2. Commit the updated slurm_run_vep.sh
   3. Update VEP command in the `capice/README.md` (Requirements & Usage -> VEP).
   4. Update the README regarding [VEP plugins](https://github.com/molgenis/capice#requirements) and
   the [VEP command](https://github.com/molgenis/capice#vep) if needed.
   5. commit capice files
2. 
   1. Obtain the latest GRCh38 VKGL release from the cluster
   2. Download the latest public GRCh38 [Clinvar](https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/) datasets (please note that these filenames are stored in the train-test and validation VCF, so file dates in the name of the files improves reproducibility). 
      ```shell
      wget https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/clinvar_<date>.vcf.gz
      ```
3. if not continuing in the folder used in step 1: checkout the new branch of capice-resources
4. Use `<capice-resources>/utility_scripts/create_and_train.sh` to create a train-test and validation files (workdir should already exist if SLURM output and error logs are to be written here):
   ```shell
   mkdir <workdir>
   APPTAINER_BIND=<bind> sbatch \
    --output=<workdir>/create_and_train.log \
    --error=<workdir>/create_and_train.err \
    --export=APPTAINER_BIND \ 
   <path_to/capice-resources/>/create_and_train.sh \
    -p "<path_to/vip/>" \
    -b "<path_to/bcftools-<version>.sif>" \
    -w "<workdir>" \
    -c "<path_to/clinvar_<date>.vcf.gz>" \
    -v "<path_to/vkgl_public_consensus_hg38_<date>.tsv>" \
    -g "<path_to/capice/>" \
    -r "<path_to/capice-resources/>" \
    -t
   ```
   - Omitting -t will generate new train and validation data and the train script without running it.
   - `<workdir>/train/train.sh` can be used to train a new model on the generated train_test data:
   ```shell
      sbatch <workdir>/train/train.sh <path_to/new_model_name.ubj>
   ```
5. Make [capice-resources](https://github.com/molgenis/capice-resources) GitHub release draft and add
      the `<workdir>/train/train_test.vcf.gz`, `<workdir>/train/validation.vcf.gz` and the new model.
6. Run CAPICE on the newly created models:
   ```shell
   module load Python/3.10.4-GCCcore-11.3.0-bare
   source capice/venv/bin/activate
   capice predict -i </path/to/validation_grch38_vep_processed.tsv.gz> -m </path/to/capice_model_grch38.ubj> -o </path/to/validation_grch38_pedicted.tsv.gz>
   deactivate
   ```
   (Note: `module purge` is not required as `Python/3.10.4-GCCcore-11.3.0-bare` is required for the next steps too)
7. Use the latest stable release model to generate CAPICE results file of the same validation TSV:
   ```shell
   python3 -m venv capice-v<version>/venv
   source capice-v<version>/venv/bin/activate
   pip --no-cache-dir install capice==<version>
   wget https://github.com/molgenis/capice/releases/download/v<version>/v<version>-v<model_version>_grch38.ubj
   capice predict -i </path/to/validation_grch38_vep_processed.tsv.gz> -m </path/to/v<version>>-v<model_version>_grch38.ubj> -o </path/to/validation_grch38_pedicted_old_model.tsv.gz>
   deactivate
   ```
8. Use module `compare-model-performance` to compare performance of two models: (`capice_predict_input.tsv` is the validation TSV used in the 2 steps above):  
   ```shell
   source capice-resources/venv/bin/activate
   compare-model-performance -a </path/to/validation_grch38_pedicted.tsv.gz> -l </path/to/validation_grch38_vep_processed.tsv.gz> -b </path/to/validation_grch38_pedicted_old_model.tsv.gz> -o </output/dir/path/grch38/>
   deactivate
   ```
9. Create a capice-resources pull-request.
10. Create a capice pull-request.
11. Once the pull-request is merged, create a new release:
     1. Tag master with `v<major>.<minor>.<patch>-rc<cadidate_version>`.
     2. create a release on GitHub.
12. Create new Apptainer image of the pre-release:
     1. Copy [this def file](https://github.com/molgenis/vip/blob/main/utils/apptainer/def/capice-5.1.1.def)
     2. Update the defined capice version & filename.
     3. Run `sudo apptainer build sif/capice-<version>.sif def/capice-<version>.def`

Optional:
1. Run CAPICE explain tool on generated models:
   ```shell
   source capice/venv/bin/activate
   capice explain -i </path/to/capice_model_grch38.ubj> -o </path/to/capice_model_grch38_explain.tsv.gz>
   capice explain -i </path/to/v<version>-v<model_version>_grch38.ubj> -o </path/to/v<version>-v<model_version>_grch38_explain.tsv.gz>
   deactivate
   ```
2. Merge/rank explain tool output:
   ```shell
   source capice-resources/venv/bin/activate
   compare-model-features -a </path/to/capice_model_grch38_explain.tsv.gz> -b </path/to/v<version>-v<model_version>_grch38_explain.tsv.gz> -o </path/to/merged_grch38.tsv.gz>
   deactivate
   module purge
   ```

## Making train-test and validation VCF files

Obtain the latest public GRCh38 VKGL (from the cluster) and [Clinvar](https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh37/) datasets and simply supply them to `train-data-creator`. 
For further details, use `trian-data-creator -h`.

## VEP

VEP is used to add annotations to the train-test and validation files. The following command is a good representation of
what VEP command should be called:

```commandline
vep --input_file <path to your input file> --format vcf --output_file <path to your output file> --vcf --compress_output gzip --sift s --polyphen s --numbers --symbol --shift_3prime 1 --allele_number --no_stats --offline --cache --dir_cache */path/to/latest/vep/cache* --species "homo_sapiens" --assembly *GRCh37 or GRCh38* --refseq --use_given_ref --exclude_predicted --use_given_ref --flag_pick_allele --force_overwrite --fork 4 --dont_skip --allow_non_variant --per_gene
```

_(`--input_file`, `--output_file` and `--assembly` have to be manually altered)_

For the most accurate VEP command, see the [CAPICE README.md](https://github.com/molgenis/capice#vep). 

_Command can vary based on the training features._

**Comparing an XGBoost 0.72.1 (CAPICE 2.0.0 or lower) to a new XGBoost 1.4.2 model, upload the validation.vcf.gz
to [CADD](https://cadd.gs.washington.edu/score) for annotation.** (set "INCLUDE ANNOTATIONS" to True)

Currently, there is no automated script in place to perform this check, since with CAPICE 4.0.0 the performance has been equalized.

## Post-VEP processing

First convert the VEP output VCF back to TSV using the [conversion tool](https://github.com/molgenis/capice/blob/main/scripts/convert_vep_vcf_to_tsv_capice.sh).

Making the converted VEP TSV train-ready requires use of the `process-vep` module. This works for both GRCh37 and GRCh38 (GRCh38 only when the `-a` flag is supplied.)

This script makes sure that variants with the correct labels are preserved (so that the labels remains accurate for the
variant) and duplicate entries between train-test and validation are removed.

## Training

Before the training module of CAPICE can be called, make sure your train_features JSON used within training is up-to-date on
your newly added and/or removed features.

Training a new model is rather easy, but takes quite a bit of time. It is recommended to start a slurm job on the GCC
cluster and to let it run overnight.

The training module can be activated with the following command (assuming you have installed CAPICE the way it is
supposed to be: `pip install .` or `pip install capice`):

`capice -v train -i /path/to/processed/train_test.tsv.gz -e /path/to/up/to/date/features.json -o /path/to/output.ubj`

## Visualizing the XGBoost tree

Visualizing the XGBoost tree is a useful tool to see how each and every individual sample is scored. To use this
functionality, one must load in the pickled model. Also import matplotlib pyplot and plot_tree from xgboost. Then use
matplotlib to make a very high resolution figure, use plot_tree to visualize the tree and then matplotlib again to
export the figure. You will get some code that is similar to this:

```python
from matplotlib import pyplot as plt
import xgboost as xgb

model = xgb.XGBClassifier()
model.load_model('/path/to/model.ubj')

fig, ax = plt.subplots(figsize=(160, 160))  # Note: (160,160) might still be too low of a resolution
# Note: the num_trees=model.best_iteration is still in concept till I figure out that XGBoost always uses the best model, or all models (there could easily be 300+ booster objects within an XGBClassifier class).
xgb.plot_tree(model, num_trees=model.best_iteration, ax=ax)  # If this says that the object is too large, adjust resolution
fig.savefig('/path/to/save_fig.png')
```

## FAQ

- I'm getting an `ValueError: invalid literal for int() with base 10: 'chr1'`, what's wrong?

You've likely downloaded a genome build 38, which has a different annotation for the chromosome.
`train_data_creator` only supports build 37.

## Acknowledgements
Standing on the shoulders of giants. This project could not have possible without the existence of many other tools and resources. Among them we would like to thank the people behind the following projects:
- [Ensembl Variant Effect Predictor (VEP)](https://grch38.ensembl.org/info/docs/tools/vep/index.html)
- [Variant Interpretation Pipeline (VIP)](https://github.com/molgenis/vip) 
- [phyloP](http://compgen.cshl.edu/phast) 
- [Illumina SpliceAI](https://github.com/Illumina/SpliceAI)
- [VKGL](https://vkgl.molgeniscloud.org/)
- [ClinVar](https://www.ncbi.nlm.nih.gov/clinvar)
- [gnomAD](https://gnomad.broadinstitute.org/)
