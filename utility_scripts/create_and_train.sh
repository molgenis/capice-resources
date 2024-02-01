#!/bin/bash
#SBATCH --job-name=capice_create_and_train
#SBATCH --time=23:59:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=16gb
#SBATCH --nodes=1
#SBATCH --export=NONE
#SBATCH --get-user-env=L60

set -e

errcho() { echo "$@"  1>&2; }

TRAIN=false

main() {
	digestCommandLine "$@"
	create_train_data
	vep
	create_model_job
	if [[ ${TRAIN} == true ]]
	then
		train
	fi
}

digestCommandLine() {
	readonly USAGE="Run VEP script
	Usage:
	run_vep.sh -v <arg> -c <arg> -b <arg> -w <arg> -r <arg> -c <arg> -v <arg> -t
		v) path/to/vkgl_file
		c) path/to/clinvar_file
		c) path/to/bcftools_sif
		w) path/to/workdir
		r) path/to/capice_resources
		g) path/to/capice git repo
		p) path/to/vip
		t) train capice model
	"

	while getopts v:b:c:w:r:g:p:t flag
	do
		case "${flag}" in
			v) VKGL_FILE=${OPTARG};;
			b) BCFTOOLS_SIF=${OPTARG};;
      c) CLINVAR_FILE=${OPTARG};;
			w) WORKDIR=${OPTARG};;
			r) CAPICE_RESOUCES=${OPTARG};;
			g) CAPICE=${OPTARG};;
			p)
				VIP_DIR=${OPTARG};;
			t)
				TRAIN=true;;
			\?)
				errcho "Error: invalid option"
				echo "${USAGE}"
				exit 1;;
		esac
	done
}

create_train_data() {
	echo "running train-data-creator"
	module load Python/3.10.4-GCCcore-11.3.0-bare
	source ${CAPICE_RESOUCES}/venv/bin/activate
	train-data-creator -v ${VKGL_FILE} -c ${CLINVAR_FILE} -o ${WORKDIR}/data/
	deactivate
	module purge
	echo "finished running train-data-creator"
}

vep() {
	echo "running vep on train test"
	bash ${CAPICE_RESOUCES}/utility_scripts/slurm_run_vep.sh -p ${VIP_DIR} -g -i ${WORKDIR}/data/train_test.vcf.gz -o ${WORKDIR}/data/train_test_vep.vcf.gz
	bash ${CAPICE}/scripts/convert_vep_vcf_to_tsv_capice.sh -p ${BCFTOOLS_SIF} -t -i ${WORKDIR}/data/train_test_vep.vcf.gz -o ${WORKDIR}/data/train_test_vep.tsv.gz
	echo "finished running vep on train test"
	echo "running vep on validation"
	bash ${CAPICE_RESOUCES}/utility_scripts/slurm_run_vep.sh -p ${VIP_DIR} -g -i ${WORKDIR}/data/validation.vcf.gz -o ${WORKDIR}/data/validation_vep.vcf.gz
	bash ${CAPICE}/scripts/convert_vep_vcf_to_tsv_capice.sh -p ${BCFTOOLS_SIF} -t -i ${WORKDIR}/data/validation_vep.vcf.gz -o ${WORKDIR}/data/validation_vep.tsv.gz
	echo "finished running vep on validation"
}

create_model_job() {
	echo "writing train script"
echo "
    #!/bin/bash
    #SBATCH --job-name=capice_train
    #SBATCH --output=${WORKDIR}/model/capice_train_grch38.log
    #SBATCH --error=${WORKDIR}/model/capice_train_grch38.err
    #SBATCH --time=23:59:00
    #SBATCH --cpus-per-task=8
    #SBATCH --mem=25gb
    #SBATCH --nodes=1
    #SBATCH --export=NONE
    #SBATCH --get-user-env=L60
    module load Python/3.10.4-GCCcore-11.3.0-bare
    source ${CAPICE}/venv/bin/activate
    capice -v train -t 8 -i ${WORKDIR}/data/train_test_vep.tsv.gz \
    -e ${CAPICE}/resources/train_features.json \
    -o ${WORKDIR}/model/capice_model.ubj
	" > ${WORKDIR}/train.sh
	echo "finished writing train script"
}

train(){
	echo "running capice training"
	bash ${WORKDIR}/train.sh
	echo "finished capice training"
}

main "$@"