#!/bin/bash
#SBATCH --job-name=run_vep
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=8gb
#SBATCH --nodes=1

set -e

errcho() { echo "$@" 1>&2; }

readonly USAGE="Easy bash script to run VEP on the GCC cluster
Usage:
run_vep.sh -i <arg> -o <arg>
-i  required: the VEP input VCF
-a  required: the GRCh assembly
-o  required: the VEP output VCF filename and path

Example:
bash run_vep.sh -i vep_input.vcf -o vep_output.vcf.gz

Requirements:
VEP
EasyBuild
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
      a) assembly=${OPTARG};;
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
    errcho "input file not set"
  else
     if [ ! -f "${input}" ]
     then
       valid_command_line=false
       errcho "input file does not exist"
     fi
  fi

  if [ -z "${assembly}" ]
  then
    valid_command_line=false
    errcho "assembly not set"
  else
    if [ "${assembly}" != "GRCh37" ]
    then
      if [ "${assembly}" != "GRCh38" ]
      then
        valid_command_line=false
        errcho "assembly is not set to GRCh37 or GRCh38"
      fi
    fi
  fi

  if [ -z "${output}" ]
  then
    valid_command_line=false
    errcho "output not set"
  fi

  if [ "${valid_command_line}" == false ];
  then
    errcho 'exiting.'
    exit 1
  fi
}


runVep() {
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
