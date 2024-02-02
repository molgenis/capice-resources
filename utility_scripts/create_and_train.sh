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
	install_capice
	create_train_data
	vep
	postprocess
	create_model_job
	if [[ ${TRAIN} == true ]]
	then
		train
	fi
}

digestCommandLine() {
	readonly USAGE="
	Usage:
	create_and_train.sh -v <arg> -c <arg> -b <arg> -w <arg> -r <arg> -n <arg> -p <arg> -t
    v) path/to/vkgl_file
		c) path/to/clinvar_file
		b) path/to/bcftools_sif
		w) path/to/workdir
		r) path/to/capice_resources
		n) capice branch name
		p) path/to/vip
		t) train capice model
	"

	while getopts v:b:c:w:r:n:p:t flag
	do
		case "${flag}" in
			v) VKGL_FILE=${OPTARG};;
			b) BCFTOOLS_SIF=${OPTARG};;
      c) CLINVAR_FILE=${OPTARG};;
			w) WORKDIR=${OPTARG};;
			r) CAPICE_RESOUCES=${OPTARG};;
			n) CAPICE_BRANCH=${OPTARG};;
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

install_capice(){
	echo "installing capice"
	git clone https://github.com/molgenis/capice.git "${WORKDIR}/capice"
	cd "${WORKDIR}/capice"
	git checkout "${CAPICE_BRANCH}"
	module load Python/3.10.4-GCCcore-11.3.0-bare
	python3 -m venv "${CAPICE}/venv"
	source "${CAPICE}/venv/bin/activate"
	pip --no-cache-dir install -e "${CAPICE}[test]"
	module purge
	echo "finished installing capice"
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

postprocess(){
  	echo "running process_vep"
  	wget -P ${WORKDIR}/data/ https://research.nhgri.nih.gov/CGD/download/txt/CGD.txt.gz
  	module load Python/3.10.4-GCCcore-11.3.0-bare
  	source ${CAPICE_RESOUCES}/venv/bin/activate
  	process-vep -a -g ${WORKDIR}/data/CGD.txt.gz -f ${CAPICE}/resources/train_features.json -t ${WORKDIR}/data/train_test_vep.tsv.gz -v ${WORKDIR}/data/validation_vep.tsv.gz -o ${WORKDIR}/data/processed/
  	deactivate
  	module purge
  	echo "finished process_vep"
}

create_model_job() {
	echo "writing train script"
	mkdir "${WORKDIR}/model/"
  echo "#!/bin/bash
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
capice -v train -t 8 -i ${WORKDIR}/data/processed/train_test.tsv.gz \
-e ${CAPICE}/resources/train_features.json \
-o ${WORKDIR}/model/capice_model.ubj
" > ${WORKDIR}/train.sh
	echo "finished writing train script"
}

train(){
	echo "running capice training"
	mkdir ${WORKDIR}/model
	bash ${WORKDIR}/train.sh
	echo "finished capice training"
}

main "$@"