[![Build Status](https://app.travis-ci.com/molgenis/capice-resources.svg?branch=main)](https://app.travis-ci.com/molgenis/capice-resources)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=molgenis_capice-resources&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=molgenis_capice-resources)

# capice-resources

Repository for resource files for CAPICE and updating CAPICE model. It contains several modules listed below. 

## Requirements
- CAPICE (personal git branch for development)
- [VIP](https://github.com/molgenis/vip) v4.12.2 (include both GRCh37 & GRCh38 during installation)
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

### TLDR

**IMPORTANT:** Unless mentioned otherwise, filenames refer to the same file. So if an output filename
is described in 1 step and a step later mentions the same filename, they both refer to the same file.

**IMPORTANT 2:** Bash scripts have been adjusted to function with "apptainer". If using singularity: change "apptainer" synthax within scripts to "singularity". Also make sure to set the `--bind` correctly.

1. Update the CAPICE tool: 
   1. Make new branch for [CAPICE](https://github.com/molgenis/capice) and checkout this branch locally.
   2. Determine feature to add and check whether a VEP processor should be written for it (VEP processors usually don't
      have to be written for int/float values).
   3. Add feature to `capice/resources/train_features.json`.
   4. Update VEP command in the `capice/README.md` (Requirements & Usage -> VEP).
   5. Download the following files to a single directory on the system/cluster where VIP is installed: 
      * [train_input_raw.vcf.gz](https://github.com/molgenis/capice/blob/master/resources/train_input_raw.vcf.gz)
      * [predict_input_raw.vcf.gz](https://github.com/molgenis/capice/blob/master/resources/predict_input_raw.vcf.gz)
      * [breakends.vcf.gz](https://github.com/molgenis/capice/blob/master/tests/resources/breakends.vcf.gz)
      * [edge_cases.vcf.gz](https://github.com/molgenis/capice/blob/master/tests/resources/edge_cases.vcf.gz)
      * [symbolic_alleles.vcf.gz](https://github.com/molgenis/capice/blob/master/tests/resources/symbolic_alleles.vcf.gz)
   6. Annotate all downloaded files with VEP using the supplied [slurm_run_vep.sh](utility_scripts/slurm_run_vep.sh):
       * Supply a smaller `--time` argument to slurm (processing the files should take a maximum of 20 minutes each)
       * Ensure `-g` is supplied.
       * To reduce potential error, a for loop should be used to mark each file (this is assuming you have changed directory into the single directory):
         * ```bash
           for file in *.vcf.gz; do sbatch --time=00:20:00 slurm_run_vep.sh -p </path/to/vip_install_directory> -i "${file}" -g -o "${file%.vcf.gz}_vep.vcf.gz"; done
           ```
       * Once all files have been processed, rename the following files:
       * ```bash
         mv ./train_input_raw_vep.vcf.gz ./train_input_annotated.vcf.gz
         mv ./predict_input_raw_vep.vcf.gz ./predict_input.vcf.gz
         ```
       You should now have the following files:
      - train_input_annotated.vcf.gz
      - predict_input.vcf.gz
      - breakends_vep.vcf.gz
      - edge_cases_vep.vcf.gz
      - symbolic_alleles_vep.vcf.gz
   7. Run the [CAPICE conversion tool](https://github.com/molgenis/capice/blob/master/scripts/convert_vep_vcf_to_tsv_capice.sh)
      on the train input. (note: use `-t` when using the conversion tool)
      ```shell
      bash capice/scripts/convert_vep_vcf_to_tsv_capice.sh -t -i <train_input_annotated.vcf.gz> -o <train_input_annotated.tsv.gz>
      ```
   8. Load Python and install [capice-resources](https://github.com/molgenis/capice-resources) in virtual environment. Run following commands in capice-resources folder:
      ```shell
      module load Python/3.10.4-GCCcore-11.3.0-bare
      python3 -m venv venv
      source venv/bin/activate
      pip --no-cache-dir install -e '.[test]'
      module purge
      ```
   9. Download/prepare CGD data if not yet locally available:
      ```shell
      wget https://research.nhgri.nih.gov/CGD/download/txt/CGD.txt.gz
      # update_date can be found at the bottom of https://research.nhgri.nih.gov/CGD/download/
      mv CGD.txt.gz CGD_<update_date>.txt.gz
      ```
   10. Run capice-resources `process-vep` module: 
       ```shell
       module load Python/3.10.4-GCCcore-11.3.0-bare
       source ./venv/bin/activate
       process-vep -g <path/to/CGD.txt.gz> -j </path/to/capice/resources/up_to_date_train_features.json> -t </path/to/train_input_annotated.tsv.gz> -o </path/to/output>
       deactivate
       module purge
       ```
   11. Load & install capice:
       ```shell
       git clone https://github.com/molgenis/capice.git
       cd capice
       git checkout <branch_name>
       module load Python/3.10.4-GCCcore-11.3.0-bare
       python3 -m venv venv
       source venv/bin/activate
       pip --no-cache-dir install -e '.[test]'
       module purge
       ```
   12. Create a script to run capice to generate a new model, like the following:
       ```shell
       #!/bin/bash
       #SBATCH --job-name=CAPICE_POC_train
       #SBATCH --output=/path/to/output/dir/capice_poc_train.log
       #SBATCH --error=/path/to/output/dir/capice_poc_train.err
       #SBATCH --time=23:59:00
       #SBATCH --cpus-per-task=8
       #SBATCH --mem=16gb
       #SBATCH --nodes=1
       #SBATCH --export=NONE
       #SBATCH --get-user-env=L60
       module load Python/3.10.4-GCCcore-11.3.0-bare
       source </path/to/your/capice/venv/bin/activate>
       capice -v train -t 8 -i </path/to/train_input.tsv.gz> -m </path/to/capice/resources/train_features.json> -o </path/to/store/output/xgb_booster_poc.ubj>
       module purge
       ```
       And run it (`sbatch <scriptname>`).
   13. Run BCF tools for the other files:
       ```shell
       bash capice/scripts/convert_vep_vcf_to_tsv_capice.sh -p </path/to/bcftools.sif> -t -i predict_input.vcf.gz -o predict_input.tsv.gz
       bash capice/scripts/convert_vep_vcf_to_tsv_capice.sh -p </path/to/bcftools.sif> -t -i breakends_vep.vcf.gz -o breakends_vep.tsv.gz
       bash capice/scripts/convert_vep_vcf_to_tsv_capice.sh -p </path/to/bcftools.sif> -t -i edge_cases_vep.vcf.gz -o edge_cases_vep.tsv.gz
       bash capice/scripts/convert_vep_vcf_to_tsv_capice.sh -p </path/to/bcftools.sif> -t -i symbolic_alleles_vep.vcf.gz -o symbolic_alleles_vep.tsv.gz
       ```
   14. Move the files to capice
       ```shell
       cp train_input.tsv.gz </path/to/capice/resources/>
       cp predict_input.tsv.gz </path/to/capice/resources/>
       cp xgb_booster_poc.ubj </path/to/capice/tests/resources/>
       cp breakends_vep.tsv.gz </path/to/capice/tests/resources/>
       cp edge_cases_vep.tsv.gz </path/to/capice/tests/resources/>
       cp symbolic_alleles_vep.tsv.gz </path/to/capice/tests/resources/>
       ```
   15. Install your current branch of capice in a virtual environment and run the tests.
       ```shell
       module load Python/3.10.4-GCCcore-11.3.0-bare
       python3 -m venv venv
       source venv/bin/activate
       pip --no-cache-dir install -e '.[test]'
       pytest
       deactivate
       module purge
       ```
   16. Update the README regarding [VEP plugins](https://github.com/molgenis/capice#requirements) and
   the [VEP command](https://github.com/molgenis/capice#vep) if needed.
   17. Create pull-request for review.
   18. Once the pull-request is reviewed/merged by someone else, create a new release(-candidate):
       1. Tag master with `v<major>.<minor>.<patch>-rc<cadidate_version>`.
       2. Generate a pre-release draft on GitHub.
   19. Create new Singularity image of the pre-release (note: singularity images do function with apptainer):
       1. Copy [this def file](https://github.com/molgenis/vip/blob/main/utils/singularity/def/capice-4.0.0.def)
       2. Update the defined capice version & filename.
       3. Run `sudo apptainer build sif/capice-<version>.sif def/capice-<version>.def` (where `sif/capice-4.0.0.sif` is the output path.)
2. Install new capice version on cluster & ensure capice-resources on the cluster is up-to-date (`git pull origin main`).
3. Download latest public GRCh37 [VKGL](https://vkgl.molgeniscloud.org/menu/main/background) and [Clinvar](https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh37/) datasets. 
   ```shell
   wget https://downloads.molgeniscloud.org/downloads/VKGL/VKGL_public_consensus_<date>.tsv
   wget https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh37/clinvar.vcf.gz
   ```
4. Use `train-data-creator` to create a train-test and validation VCFs:  
   ```shell
   module load Python/3.10.4-GCCcore-11.3.0-bare
   source ./venv/bin/activate
   train-data-creator -v </path/to/vkgl_public_consensus_<date>.tsv> -c </path/to/clinvar.vcf.gz> -o </path/to/output_train_data>
   deactivate
   module purge
   ```
5. Make [capice-resources](https://github.com/molgenis/capice-resources) GitHub release draft and add
   the `train_test.vcf.gz` and `validation.vcf.gz` files created in the previous step.
6. Update `./utility_scripts/slurm_run_vep.sh` with the new VEP command.
7. Run the VEP singularity image on both the train-test & validation VCF files (separately!):
   ```shell
   sbatch --output=</path/to/train_test_vep.log> --error=</path/to/train_test_vep.err> ./utility_scripts/slurm_run_vep.sh -p </path/to/vip/directory> -g -i </path/to/train_test.vcf.gz> -o </path/to/train_test_vep.vcf.gz>
   sbatch --output=</path/to/validation_vep.log> --error=</path/to/validation_vep.err> ./utility_scripts/slurm_run_vep.sh -p </path/to/vip/directory> -g -i </path/to/validation.vcf.gz> -o </path/to/validation_vep.vcf.gz>
   ```
   __IMPORTANT:__ If memory causes issues, `--buffer_size 500` (or something similar) can be used 
   to reduce memory usage (at the cost of speed).
8. Lift over not-annotated VCFs (output from `train-data-creator`) to GRCh38 using `liftover_variants.sh` (and the latest Picard image, available [here](https://download.molgeniscloud.org/downloads/vip/images/)):
   ```shell
   sbatch --output=</path/to/train_test_liftover_grch38.log> --error=</path/to/train_test_liftover_grch38.err> ./utility_scripts/liftover_variants.sh -p </path/to/picard_image.sif> -b </additional,/apptainer,/binds> -i </path/to/train_test.vcf.gz> -o </path/to/train_test_grch38>
   sbatch --output=</path/to/train_test_liftover_grch38.log> --error=</path/to/train_test_liftover_grch38.err> ./utility_scripts/liftover_variants.sh -p </path/to/picard_image.sif> -b </additional,/apptainer,/binds> -i </path/to/validation.vcf.gz> -o </path/to/validation_grch38>
   ```
   __IMPORTANT:__ Do not supply an extension as it doesn't produce a single file!
9. Use the VEP singularity image to annotate the GRCh38 VCF files:
   ```shell
   sbatch --output=</path/to/train_test_grch38_vep.log> --error=</path/to/train_test_grch38_vep.err> ./utility_scripts/slurm_run_vep.sh -p </path/to/vip/directory> -g -a -i </path/to/train_test_grch38.vcf.gz> -o </path/to/train_test_grch38_vep.vcf.gz>
   sbatch --output=</path/to/validation_grch38_vep.log> --error=</path/to/validation_grch38_vep.err> ./utility_scripts/slurm_run_vep.sh -p </path/to/vip/directory> -g -a -i </path/to/validation_grch38.vcf.gz> -o </path/to/validation_grch38_vep.vcf.gz>
   ```
10. Convert VEP annotated train-test & validation VCFs (separately!) back to TSV using 
    [CAPICE conversion tool](https://github.com/molgenis/capice/blob/master/scripts/convert_vep_vcf_to_tsv_capice.sh) (using `-t`):
    ```shell
    bash capice/scripts/convert_vep_vcf_to_tsv_capice.sh -p </path/to/bcftools.sif> -t -i </path/to/train_test_vep.vcf.gz> -o </path/to/train_test_vep.tsv.gz>
    bash capice/scripts/convert_vep_vcf_to_tsv_capice.sh -p </path/to/bcftools.sif> -t -i </path/to/validation_vep.vcf.gz> -o </path/to/validation_vep.tsv.gz>
    bash capice/scripts/convert_vep_vcf_to_tsv_capice.sh -p </path/to/bcftools.sif> -t -i </path/to/train_test_grch38_vep.vcf.gz> -o </path/to/train_test_grch38_vep.tsv.gz>
    bash capice/scripts/convert_vep_vcf_to_tsv_capice.sh -p </path/to/bcftools.sif> -t -i </path/to/validation_grch38_vep.vcf.gz> -o </path/to/validation_grch38_vep.tsv.gz>
    ```
11. Process train-test & validation TSVs (ensure `-a` is added for GRCh38):
    ```shell
    module load Python/3.10.4-GCCcore-11.3.0-bare
    source ./venv/bin/activate
    process-vep -j </path/to/train_features.json> -g <path/to/CGD.txt.gz> -t </path/to/train_test_vep.tsv.gz> -v </path/to/validation.tsv.gz> -o </path/to/build37> 1> </path/to/build37.log>
    process-vep -j </path/to/train_features.json> -g <path/to/CGD.txt.gz> -a -t </path/to/train_test_grch38_vep.tsv.gz> -v </path/to/validation_grch38_vep.tsv.gz> -o </path/to/grch38> 1> </path/to/grch38.log>
    deactivate
    module purge
    ```
12. Train the new model using the train-test TSV and impute json (for both GRCh37 & GRCh38):
    ```shell
    #!/bin/bash
    #SBATCH --job-name=capice_train_grch37
    #SBATCH --output=/path/to/output/dir/capice_train_grch37.log
    #SBATCH --error=/path/to/output/dir/capice_train_grch37.err
    #SBATCH --time=23:59:00
    #SBATCH --cpus-per-task=8
    #SBATCH --mem=25gb
    #SBATCH --nodes=1
    #SBATCH --export=NONE
    #SBATCH --get-user-env=L60
    module load Python/3.10.4-GCCcore-11.3.0-bare
    source </path/to/your/capice/venv/bin/activate>
    capice -v train -t 8 -i </path/to/train_test_vep_processed.tsv.gz> \
    -e </path/to/capice/resources/train_features.json> \
    -o </path/to/store/output/capice_model_grch37.ubj>
    ```
    
    ```shell
    #!/bin/bash
    #SBATCH --job-name=capice_train_grch38
    #SBATCH --output=/path/to/output/dir/capice_train_grch38.log
    #SBATCH --error=/path/to/output/dir/capice_train_grch38.err
    #SBATCH --time=23:59:00
    #SBATCH --cpus-per-task=8
    #SBATCH --mem=25gb
    #SBATCH --nodes=1
    #SBATCH --export=NONE
    #SBATCH --get-user-env=L60
    module load Python/3.10.4-GCCcore-11.3.0-bare
    source </path/to/your/capice/venv/bin/activate>
    capice -v train -t 8 -i </path/to/train_test_grch38_vep_processed.tsv.gz> \
    -e </path/to/capice/resources/train_impute_values.json> \
    -o </path/to/store/output/capice_model_grch38.ubj>
    ```
13. Attach the new models to the draft release created in [capice-resources](https://github.com/molgenis/capice-resources) releases.
14. Run CAPICE on the newly created models:
    ```shell
    module load Python/3.10.4-GCCcore-11.3.0-bare
    source capice/venv/bin/activate
    capice predict -i </path/to/validation_vep_processed.tsv.gz> -m </path/to/capice_model_grch37.ubj> -o </path/to/validation_pedicted.tsv.gz>
    capice predict -i </path/to/validation_grch38_vep_processed.tsv.gz> -m </path/to/capice_model_grch38.ubj> -o </path/to/validation_grch38_pedicted.tsv.gz>
    deactivate
    ```
    (Note: `module purge` is not required as `Python/3.10.4-GCCcore-11.3.0-bare` is required for the next steps too)
15. Use latest non `Release Candidate` model to generate CAPICE results file of the same validation TSV:
    ```shell
    python3 -m venv capice-v<version>/venv
    source capice-v<version>/venv/bin/activate
    pip --no-cache-dir install capice==<version>
    wget https://github.com/molgenis/capice/releases/download/v<version>/v<version>-v<model_version>_grch37.ubj
    wget https://github.com/molgenis/capice/releases/download/v<version>/v<version>-v<model_version>_grch38.ubj
    capice predict -i </path/to/validation_vep_processed.tsv.gz> -m </path/to/v<version>>-v<model_version>_grch37.ubj> -o </path/to/validation_pedicted_old_model.tsv.gz>
    capice predict -i </path/to/validation_grch38_vep_processed.tsv.gz> -m </path/to/v<version>>-v<model_version>_grch38.ubj> -o </path/to/validation_grch38_pedicted_old_model.tsv.gz>
    deactivate
    ```
16. Use module `compare-model-performance` to compare performance of two models: (`capice_predict_input.tsv` is the validation TSV used in the 2 steps above):  
    ```shell
    source capice-resources/venv/bin/activate
    compare-model-performance -a </path/to/validation_pedicted.tsv.gz> -l </path/to/validation_vep_processed.tsv.gz> -b </path/to/validation_pedicted_old_model.tsv.gz> -o </output/dir/path/grch37/>
    compare-model-performance -a </path/to/validation_grch38_pedicted.tsv.gz> -l </path/to/validation_grch38_vep_processed.tsv.gz> -b </path/to/validation_grch38_pedicted_old_model.tsv.gz> -o </output/dir/path/grch38/>
    deactivate
    ```
17. Run CAPICE explain tool on generated models:
    ```shell
    source capice/venv/bin/activate
    capice explain -i </path/to/capice_model_grch37.ubj> -o </path/to/capice_model_grch37_explain.tsv.gz>
    capice explain -i </path/to/capice_model_grch38.ubj> -o </path/to/capice_model_grch38_explain.tsv.gz>
    capice explain -i </path/to/v<version>-v<model_version>_grch37.ubj> -o </path/to/v<version>-v<model_version>_grch37_explain.tsv.gz>
    capice explain -i </path/to/v<version>-v<model_version>_grch38.ubj> -o </path/to/v<version>-v<model_version>_grch38_explain.tsv.gz>
    deactivate
    ```
18. Merge/rank explain tool output:
    ```shell
    source capice-resources/venv/bin/activate
    compare-model-features -a </path/to/capice_model_grch37_explain.tsv.gz> -b </path/to/v<version>-v<model_version>_grch37_explain.tsv.gz> -o </path/to/merged_grch37.tsv.gz>
    compare-model-features -a </path/to/capice_model_grch38_explain.tsv.gz> -b </path/to/v<version>-v<model_version>_grch38_explain.tsv.gz> -o </path/to/merged_grch38.tsv.gz>
    deactivate
    module purge
    ```

## Making train-test and validation VCF files

Download the latest public GRCh37 [VKGL](https://vkgl.molgeniscloud.org/menu/main/background) and [Clinvar](https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh37/) datasets and simply supply them to `train-data-creator`. 
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
