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
	create
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
	run_vep.sh -a <arg> -b <arg> -w <arg> -r <arg> -c <arg> -v <arg> -t
		a) path/to/vkgl_file
		b) path/to/clinvar_file
		w) path/to/workdir
		r) path/to/capice_resources
		c) path/to/capice
		v) path/to/vip
		t) train capice model
	"

	while getopts a:b:w:r:c:v:t flag
	do
		case "${flag}" in
			a) VKGL_FILE=${OPTARG};;
			b) CLINVAR_FILE=${OPTARG};;
			w) WORKDIR=${OPTARG};;
			r) CAPICE_RESOUCES=${OPTARG};;
			c) CAPICE=${OPTARG};;
			v) 
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

create() {
	echo "running train-data-creator"
	module load Python/3.10.4-GCCcore-11.3.0-bare
	source ${CAPICE_RESOUCES}/venv/bin/activate
	train-data-creator -v ${VKGL_FILE} -c ${CLINVAR_FILE} -o ${WORKDIR}/train/
	deactivate
	module purge
	echo "finished running train-data-creator"
}

vep() {
	echo "running vep on train test"
	bash ${CAPICE_RESOUCES}/utility_scripts/slurm_run_vep.sh -p ${VIP_DIR} -g -i ${WORKDIR}/train/train_test.vcf.gz -o ${WORKDIR}/train/train_test_vep.vcf.gz
	bash ${CAPICE}/scripts/convert_vep_vcf_to_tsv_capice.sh -p ${BCFTOOLS_SIF} -t -i ${WORKDIR}/train/train_test_grch38_vep.vcf.gz -o ${WORKDIR}/train/train_test_grch38_vep.tsv.gz
	echo "finished running vep on train test"
	echo "running vep on validation"
	bash ${CAPICE_RESOUCES}/utility_scripts/slurm_run_vep.sh -p ${VIP_DIR} -g -i ${WORKDIR}/train/validation.vcf.gz -o ${WORKDIR}/train/validation_vep.vcf.gz
	bash ${CAPICE}/scripts/convert_vep_vcf_to_tsv_capice.sh -p ${BCFTOOLS_SIF} -t -i ${WORKDIR}/train/validation_grch38_vep.vcf.gz -o ${WORKDIR}/train/validation_grch38_vep.tsv.gz
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
    capice -v train -t 8 -i ${WORKDIR}/train/train_test_grch38_vep.tsv.gz \
    -e ${CAPICE}/resources/train_features.json \
    -o ${WORKDIR}/model/capice_model.ubj
	" > ${WORKDIR}/train/train.sh
	echo "finished writing train script"
}

train(){
	echo "running capice training"
	bash ${WORKDIR}/train/train.sh
	echo "finished capice training"
}

main "$@"