#!/bin/bash
#SBATCH --job-name=liftover_variants
#SBATCH --time=05:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=20gb
#SBATCH --nodes=1

set -e

errcho() { echo "$@" 1>&2; }

readonly USAGE="Easy bash script to convert a GRCh37 VCF to GRCh38 VCF
Usage:
liftover_variants.sh -i <arg> -o <arg>
-i  required: the GRCh37 input VCF
-o  required: the GRCh38 output VCF path+filename (except extension!)

Example:
bash liftover_variants.sh -i /path/to/GRCh37.vcf -o /path/to/GRCh38

Requirements:
Picard
EasyBuild
"

main() {
  digestCommandLine "$@"
  runLiftover
}

digestCommandLine() {
  while getopts i:o:h flag
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
    errcho "input file not set"
  else
     if [ ! -f "${input}" ]
     then
       valid_command_line=false
       errcho "input file does not exist"
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


runLiftover() {
  local output="${output}.vcf"
  local rejected="${output}_rejected.vcf"
  local input="${input}"

  local args=()

  args+=("/apps/software/picard/2.20.5-Java-11-LTS/picard.jar" "LiftoverVcf")
  args+=("I=${input}")
  args+=("O=${output}")
  args+=("CHAIN=/apps/data/GRC/b37ToHg38.over.chain")
  args+=("REJECT=${rejected}")
  args+=("R=/apps/data/GRC/GCA_000001405.15/GCA_000001405.15_GRCh38_full_plus_hs38d1_analysis_set.fna.gz")

  echo "Loading Picard"

  module load picard

  echo "Running Picard"

  java -jar "${args[@]}"

  echo "Gzipping outputs"

  gzip "${output}"
  gzip "${rejected}"

  echo "Removing indexing file if made"
  if [ -f "${output}.vcf.idx" ]
  then
    rm "${output}.vcf.idx"
    echo "Indexing file removed"
  fi

  echo "Done"
}

main "$@"

