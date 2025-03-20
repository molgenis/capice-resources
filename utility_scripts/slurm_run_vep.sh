#!/usr/bin/env bash

#SBATCH --job-name=run_vep
#SBATCH --time=23:59:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16gb
#SBATCH --nodes=1
#SBATCH --export=NONE
#SBATCH --get-user-env=L60

set -e

errcho() { echo "$@"  1>&2; }

# Usage.
readonly USAGE="Run VEP script
Usage:
run_vep.sh -p <arg> -i <arg> -o <arg> [-a] [-g] [-f]
-r    required: The path to the VIP resources directory
-p    required: The path to the vep plugins dir.
-e    required: The path to the vep sif file.
-p    required: The path to the installed VIP directory.
-i    required: The VEP output VCF.
-o    required: The directory and output filename.
-g    optional: enables the --per-gene flag for VEP.
-f    optional: Force flag. Overwrites existing output.

Please note that this script expects apptainer binds to be set correctly by the system administrator.
Additional apptainer binds can be set by setting the environment variable APPTAINER_BIND.
If using SLURM, please export this environment variable to the sbatch instance too.

Example:
run_vep.sh -p /path/to/vip -i some_file.vcf.gz -o some_file_vep.vcf.gz

Requirements:
- Apptainer (although Singularity should work too, please change the script and adjust apptainer to singularity)
- VIP installment (https://github.com/molgenis/vip)
"

FORCE=false
PG=false

main() {
  digestCommandLine "$@"
  runVep
}

digestCommandLine() {
  while getopts p:r:e:i:o:hafg flag
  do
    case "${flag}" in
      r) resources_directory=${OPTARG};;
      p) plugins_dir=${OPTARG};;
      e) vep_image=${OPTARG};;
      i) input=${OPTARG};;
      o) output=${OPTARG};;
      h)
        echo "${USAGE}"
        exit;;
      a)
        ASSEMBLY="GRCh38";;
      g)
        PG=true;;
      f)
        FORCE=true;;
      \?)
        errcho "Error: invalid option detected"
        echo "${USAGE}"
        exit 1;;
    esac
  done

  validateCommandLine
}

validateCommandLine() {
  local valid=true

  if [ -z "${vep_image}" ]
  then
    valid=false
    errcho "VEP image path not set/empty"
  else
    if [ ! -f "${vep_image}" ]
    then
      valid=false
      errcho "VEP image '${vep_image}' does not exist"
    fi
  fi

  if [ -z "${plugins_dir}" ]
  then
    valid=false
    errcho "VIP path not set/empty"
  fi

  if [ -z "${input}" ]
  then
    valid=false
    errcho "Input file not set/empty"
  else
    if [ ! -f "${input}" ]
    then
      valid=false
      errcho "Input file '${input}' does not exist"
    else
      if [[ "${input}" != *.vcf.gz ]]
      then
        valid=false
        errcho "Input file is not gzipped vcf"
      fi
    fi
  fi

  if [ -z "${output}" ]
  then
    valid=false
    errcho "Output file not set/empty"
  else
    # Validates proper output filename.
    if [[ "${output}" != *.vcf.gz ]]
    then
      valid=false
      errcho "output filename must end with '.vcf.gz'"
    else
      # Validates if output doesn't file already exist.
      if [ -f "${output}" ]
      then
        if [[ ${FORCE} == true ]]
        then
          echo "output file exists, enforcing output"
          rm "${output}"
        else
          errcho "output file exists and force flag is not called"
          valid=false
        fi
      fi
    fi
  fi

  # If a the command line arguments are invalid, exits with code 1.
  if [[ "${valid}" == false ]]; then errcho "Exiting."; exit 1; fi
}

runVep() {
    local args=()
    args+=("exec")
    args+=("${vep_image}")
    args+=("vep")
    args+=("--input_file" "${input}")
    args+=("--format" "vcf")
    args+=("--output_file" "${output}")
    args+=("--vcf")
    args+=("--compress_output" "gzip")
    args+=("--no_stats")
    args+=("--offline")
    args+=("--fasta" "${resources_directory}/GRCh38/GCA_000001405.15_GRCh38_no_alt_analysis_set.fna.gz")
    args+=("--cache")
    args+=("--buffer_size" "1000")
    args+=("--dir_cache" "${resources_directory}/vep/cache")
    args+=("--species" "homo_sapiens")
    args+=("--assembly" "GRCh38")
    args+=("--refseq")
    args+=("--exclude_predicted")
    args+=("--use_given_ref")
    args+=("--symbol")
    args+=("--flag_pick_allele")
    args+=("--sift" "s")
    args+=("--polyphen" "s")
    args+=("--total_length")
    args+=("--shift_3prime" "1")
    args+=("--allele_number")
    args+=("--numbers")
    args+=("--dont_skip")
    args+=("--allow_non_variant")
    args+=("--fork" "4")
    args+=("--dir_plugins" "${plugins_dir}")
    args+=("--plugin" "Grantham")
    args+=("--safe")
    args+=("--plugin" "SpliceAI,snv=${resources_directory}/GRCh38/spliceai_scores.masked.snv.hg38.vcf.gz,indel=${resources_directory}/GRCh38/spliceai_scores.masked.indel.hg38.vcf.gz")
    args+=("--plugin" "gnomAD,${resources_directory}/GRCh38/gnomad.total.v4.1.sites.stripped-v2.tsv.gz")
    args+=("--custom" "${resources_directory}/GRCh38/hg38.phyloP100way.bw,phyloP,bigwig,exact,0")
    if [[ "${PG}" == true ]]
    then
      args+=("--per_gene")
    fi

  apptainer "${args[@]}"
}

main "$@"
