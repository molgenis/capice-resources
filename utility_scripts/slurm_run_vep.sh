#!/usr/bin/env bash

#SBATCH --job-name=run_vep
#SBATCH --time=10:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=3gb
#SBATCH --nodes=1
#SBATCH --export=NONE
#SBATCH --get-user-env=L60

set -e

errcho() { echo "$@"  1>&2; }

# Usage.
readonly USAGE="Run VEP script
Usage:
run_vep.sh -i <arg> -o <arg> [-a] [-g] [-f]
-i    required: The VEP output VCF.
-o    required: The directory and output filename for the CAPICE .tsv.gz.
-a    optional: change the assembly from GRCh37 to GRCh38
-g    optional: enables the --per-gene flag for VEP
-f    optional: Force flag. Overwrites existing output.

Example:
run_vep.sh -i some_file.vcf.gz -o some_file_vep.tsv.gz

Requirements:
VIP installment
"

FORCE=false
ASSEMBLY="GRCh37"
PG=false
DIRECTORY=<"/path/to/vip/directory">
RESOURCES_DIRECTORY="${DIRECTORY}resources/"
VEP_IMAGE="${DIRECTORY}images/vep-107.0.sif"

main() {
  digestCommandLine "$@"
  runVep
}

digestCommandLine() {
  while getopts i:o:hafg flag
  do
    case "${flag}" in
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

  if [ -z "${input}" ]
  then
    valid=false
    errcho "Input file not set/empty"
  else
    if [ ! -f "${input}" ]
    then
      valid=false
      errcho "Input file does not exist"
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

  if [ ! -f "${VEP_IMAGE}" ]
  then
    errcho "VEP singularity image not found"
    valid=false
  fi

  # If a the command line arguments are invalid, exits with code 1.
  if [[ "${valid}" == false ]]; then errcho "Exiting."; exit 1; fi
}

runVep() {
  local args=()
  args+=("exec")
  args+=("--bind" "/apps,/groups")
  args+=("${VEP_IMAGE}")
  args+=("vep")
  args+=("--input_file" "${input}")
  args+=("--format" "vcf")
  args+=("--output_file" "${output}")
  args+=("--vcf")
  args+=("--compress_output" "gzip")
  args+=("--sift" "s")
  args+=("--polyphen" "s")
  args+=("--numbers")
  args+=("--symbol")
  args+=("--shift_3prime" "1")
  args+=("--allele_number")
  args+=("--refseq")
  args+=("--total_length")
  args+=("--no_stats")
  args+=("--offline")
  args+=("--cache")
  args+=("--dir_cache" "${RESOURCES_DIRECTORY}/vep/cache")
  args+=("--species" "homo_sapiens")
  args+=("--assembly" "${ASSEMBLY}")
  args+=("--fork" "4")
  args+=("--dont_skip")
  args+=("--allow_non_variant")
  args+=("--use_given_ref")
  args+=("--exclude_predicted")
  args+=("--flag_pick_allele")
  args+=("--plugin" "Grantham")
  if [[ "${PG}" == true ]]
  then
    args+=("--per_gene")
  fi
  args+=("--dir_plugins" "${RESOURCES_DIRECTORY}/vep/plugins")

  if [[ "${ASSEMBLY}" == "GRCh37" ]]
  then
    args+=("--plugin" "SpliceAI,snv=${RESOURCES_DIRECTORY}GRCh37/spliceai_scores.masked.snv.hg19.vcf.gz,indel=${RESOURCES_DIRECTORY}GRCh37/spliceai_scores.masked.indel.hg19.vcf.gz")
    args+=("--custom" "${RESOURCES_DIRECTORY}GRCh37/gnomad.total.r2.1.1.sites.stripped.vcf.gz,gnomAD,vcf,exact,0,AF,HN")
    args+=("--custom" "${RESOURCES_DIRECTORY}GRCh37/hg19.100way.phyloP100way.bw,phyloP,bigwig,exact,0")
  else
    args+=("--plugin" "SpliceAI,snv=${RESOURCES_DIRECTORY}GRCh38/spliceai_scores.masked.snv.hg38.vcf.gz,indel=${RESOURCES_DIRECTORY}GRCh38/spliceai_scores.masked.indel.hg38.vcf.gz")
    args+=("--custom" "${RESOURCES_DIRECTORY}GRCh38/gnomad.genomes.v3.1.2.sites.stripped.vcf.gz,gnomAD,vcf,exact,0,AF,HN")
    args+=("--custom" "${RESOURCES_DIRECTORY}GRCh38/hg38.phyloP100way.bw,phyloP,bigwig,exact,0")
  fi
  singularity "${args[@]}"
}

main "$@"
