#!/usr/bin/env bash

#SBATCH --job-name=run_vep
#SBATCH --time=5:59:00
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
run_vep.sh -p <arg> -i <arg> -o <arg> [-a] [-g] [-f]
-p    required: The path to the installed VIP directory.
-i    required: The VEP output VCF.
-o    required: The directory and output filename.
-a    optional: change the assembly from GRCh37 to GRCh38.
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
ASSEMBLY="GRCh37"
PG=false

main() {
  digestCommandLine "$@"
  runVep
}

digestCommandLine() {
  while getopts p:i:o:hafg flag
  do
    case "${flag}" in
      p)
        vip_path=${OPTARG}
        resources_directory="${vip_path%/}/resources/" # %/ to ensure that paths are set correct
        vep_image="${vip_path%/}/images/vep-107.0.sif"
        ;;
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

  if [ -z "${vip_path}" ]
  then
    valid=false
    errcho "VIP path not set/empty"
  else
    if [ ! -f "${vep_image}" ]
    then
      valid=false
      errcho "VEP 107.0 image does not exist"
    fi
  fi

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
  args+=("--dir_cache" "${resources_directory}/vep/cache")
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
  args+=("--dir_plugins" "${resources_directory}/vep/plugins")

  if [[ "${ASSEMBLY}" == "GRCh37" ]]
  then
    args+=("--plugin" "SpliceAI,snv=${resources_directory}GRCh37/spliceai_scores.masked.snv.hg19.vcf.gz,indel=${resources_directory}GRCh37/spliceai_scores.masked.indel.hg19.vcf.gz")
    args+=("--custom" "${resources_directory}GRCh37/gnomad.total.r2.1.1.sites.stripped.patch1.vcf.gz,gnomAD,vcf,exact,0,AF,HN")
    args+=("--custom" "${resources_directory}GRCh37/hg19.100way.phyloP100way.bw,phyloP,bigwig,exact,0")
  else
    args+=("--plugin" "SpliceAI,snv=${resources_directory}GRCh38/spliceai_scores.masked.snv.hg38.vcf.gz,indel=${resources_directory}GRCh38/spliceai_scores.masked.indel.hg38.vcf.gz")
    args+=("--custom" "${resources_directory}GRCh38/gnomad.genomes.v3.1.2.sites.stripped.vcf.gz,gnomAD,vcf,exact,0,AF,HN")
    args+=("--custom" "${resources_directory}GRCh38/hg38.phyloP100way.bw,phyloP,bigwig,exact,0")
  fi
  apptainer "${args[@]}"
}

main "$@"
