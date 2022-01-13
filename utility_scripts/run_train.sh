#!/bin/bash
#SBATCH --job-name=Train_CAPICE_model
#SBATCH --time=2-00:59:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=10gb
#SBATCH --nodes=1

set -e

errcho() { echo "$@" 1>&2; }

readonly USAGE="Easy bash script to run the CAPICE train protocol on GCC cluster
Usage:
run_train.sh -i <arg> -o <arg>
-i  required: the training input TSV
-o  required: the output path and .pickle.dat filename

Example:
bash run_train.sh -i train_input.tsv.gz -o capice_versionX.pickle.dat

Requirements:
- Python 3.9
- (virtual) environment with CAPICE modules installed
- CAPICE repository clone / easybuild install
- EasyBuild
"

main() {
  digestCommandLine "$@"
  runVep
}

digestCommandLine() {
  while getopts i:o:a:h flag
  do
    case "${flag}" in
      i) input=${OPTARG};;
      o) output=${OPTARG};;
      h)
        echo "${USAGE}"
        exit;;
      /?)
        errcho "Error: invalid option"
        echo "${USAGE}"
        exit 1;;
    esac
  done

  validateCommandLine

  echo "CLA passed"
}

validateCommandLine() {
  local valid_command_line=true
  if [ -z "${input}" ]
  then
    valid_command_line=false
    errcho "Input file not set!"
  else
     if [ ! -f "${input}" ]
     then
       valid_command_line=false
       errcho "Input file does not exist!"
      else
        if [[ "${input}" != *.tsv.gz && "${input}" != *.tsv ]]
        then
          valid_command_line=false
          errcho "Input file must be a (gzipped) TSV!"
        fi
     fi
  fi

  if [ -z "${output}" ]
  then
    valid_command_line=false
    errcho "output not set"
  else
    if [ "${output}" != *.pickle.dat ]
    then
      valid_command_line=false
      errcho "Output must have the extension .pickle.dat !"
    fi
  fi

  if [ "${valid_command_line}" == false ];
  then
    errcho 'Exiting.'
    exit 1
  fi
}


runTrain() {
  local output="${output}"
  local input="${input}"
  local assembly="${assembly}"

  local args=()

  args+=("--input_file" "${input}")
  args+=("--format" "vcf")
  args+=("--output_file" "${output}")
  args+=("--vcf")
  args+=("--compress_output" "gzip")
  args+=("--regulatory")
  args+=("--sift" "s")
  args+=("--polyphen" "s")
  args+=("--domains")
  args+=("--numbers")
  args+=("--canonical")
  args+=("--symbol")
  args+=("--shift_3prime" "1")
  args+=("--allele_number")
  args+=("--no_stats")
  args+=("--offline")
  args+=("--cache")
  args+=("--dir_cache" "/apps/data/Ensembl/VEP/104")
  args+=("--species" "homo_sapiens")
  args+=("--assembly" "${assembly}")
  args+=("--refseq")
  args+=("--use_given_ref")
  args+=("--exclude_predicted")
  args+=("--flag_pick_allele")
  args+=("--force_overwrite")
  args+=("--fork" "4")
  args+=("--af_gnomad")
  args+=("--pubmed")
  args+=("--dont_skip")
  args+=("--allow_non_variant")
  args+=("--per_gene")

  echo "Loading VEP"

  module load VEP/104.2-foss-2018b-Perl-5.28.0

  echo "Running VEP"

  vep "${args[@]}"

  echo "Done"
}

main "$@"