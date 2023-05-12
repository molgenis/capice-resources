#!/bin/bash
#SBATCH --job-name=liftover_variants
#SBATCH --time=05:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=20gb
#SBATCH --nodes=1
#SBATCH --export=NONE
#SBATCH --get-user-env=L60

set -e

errcho() { echo "$@" 1>&2; }

readonly USAGE="Easy bash script to convert a GRCh37 VCF to GRCh38 VCF
Usage:
liftover_variants.sh -p <arg> -i <arg> -o <arg> -c <arg> -r <arg>
-p  required: The path to the Picard singularity image
-i  required: the GRCh37 input VCF
-o  required: the GRCh38 output VCF path+filename (except extension!)
-c  required: the chain file
-r  required: the reference sequence fasta for the TARGET build

Please note that this script expects apptainer binds to be set correctly by the system administrator.
Additional apptainer binds can be set by setting the environment variable APPTAINER_BIND.
If using SLURM, please export this environment variable to the sbatch instance too.

Example:
bash liftover_variants.sh -p /path/to/picard_singularity_image.sif -i /path/to/GRCh37.vcf -o /path/to/GRCh38 -c /path/to/chain_file.chain -r /path/to/reference.fna.gz

Requirements:
- Apptainer (although Singularity should work too, please change the script and adjust apptainer to singularity)
- Picard singularity image, available here: https://download.molgeniscloud.org/downloads/vip/images/utils
"

main() {
  digestCommandLine "$@"
  runLiftover
}

digestCommandLine() {
  while getopts p:i:o:c:r:h flag
  do
    case "${flag}" in
      p) picard_path=${OPTARG};;
      i) input=${OPTARG};;
      o) output=${OPTARG};;
      c) chain_file=${OPTARG};;
      r) reference=${OPTARG};;
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
  if [ -z "${picard_path}" ]
  then
    valid_command_line=false
    errcho "picard singularity image not set"
  else
     if [ ! -f "${picard_path}" ]
     then
       valid_command_line=false
       errcho "picard singularity image does not exist"
     fi
  fi

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

  if [ -z "${chain_file}" ]
  then
    valid_command_line=false
    errcho "chain file not set"
  else
     if [ ! -f "${chain_file}" ]
     then
       valid_command_line=false
       errcho "chain_file file does not exist"
     fi
  fi

  if [ -z "${reference}" ]
  then
    valid_command_line=false
    errcho "reference file not set"
  else
     if [ ! -f "${reference}" ]
     then
       valid_command_line=false
       errcho "reference file does not exist"
     fi
  fi

  if [ "${valid_command_line}" == false ];
  then
    errcho 'exiting.'
    exit 1
  fi
}


runLiftover() {
  local rejected="${output}_rejected.vcf"
  local output="${output}.vcf"
  local input="${input}"

  local args=()

  args+=("exec")
  args+=("${picard_path}")
  args+=("java" "-jar")
  args+=("/opt/picard/lib/picard.jar" "LiftoverVcf")
  args+=("-I" "${input}")
  args+=("-O" "${output}")
  args+=("-C" "${chain_file}")
  args+=("--REJECT" "${rejected}")
  args+=("-R" "${reference}")
  args+=("-WMC" "true")

  apptainer "${args[@]}"

  gzip "${output}"
  gzip "${rejected}"

}

main "$@"
