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
	install_capice "${CAPICE_BRANCH}"
	install_capice "${PROD_CAPICE_VERSION}"
	create_train_data
	vep
	postprocess
	create_model_job
	train
	download_model
	run_capice "${WORKDIR}/capice/${PROD_CAPICE_VERSION}/" "${WORKDIR}/validation/${PROD_MODEL}" "${WORKDIR}/validation/prod_validation_predicted.tsv.gz"
	run_capice "${WORKDIR}/capice/${CAPICE_BRANCH}/" "${WORKDIR}/model/capice_model.ubj" "${WORKDIR}/validation/new_validation_predicted.tsv.gz"
	compare_and_threshold
  explain
  merge_rank
}

merge_rank(){
}

digestCommandLine() {
	readonly USAGE="
	Usage:
	create_and_train.sh -v <arg> -c <arg> -b <arg> -w <arg> -r <arg> -n <arg> -p <arg> -t <arg> -m <arg> 
    v) path/to/vkgl_file
		c) path/to/clinvar_file
		b) path/to/bcftools_sif
		w) path/to/workdir
		r) path/to/capice_resources
		n) capice branch name
		p) path/to/vip
		t) capice production tag
		m) capice production model file name
	"

	while getopts v:b:c:w:r:n:p:t:m: flag
	do
		case "${flag}" in
			v) VKGL_FILE=${OPTARG};;
			b) BCFTOOLS_SIF=${OPTARG};;
			c) CLINVAR_FILE=${OPTARG};;
			w) WORKDIR=${OPTARG};;
			r) CAPICE_RESOURCES=${OPTARG};;
			n) CAPICE_BRANCH=${OPTARG};;
			p) VIP_DIR=${OPTARG};;
			t) PROD_CAPICE_VERSION=${OPTARG};;
			m) PROD_MODEL=${OPTARG};;
			\?)
				errcho "Error: invalid option"
				echo "${USAGE}"
				exit 1;;
		esac
	done
	
	CAPICE="${WORKDIR}/capice/${CAPICE_BRANCH}"
}

install_capice(){
	echo "installing capice ${1}"
	git clone https://github.com/molgenis/capice.git "${WORKDIR}/capice/${1}"
	cd "${WORKDIR}/capice/${1}"
	git checkout "${1}"
	module load Python/3.10.4-GCCcore-11.3.0-bare
	python3 -m venv "${WORKDIR}/capice/${1}/venv"
	source "${WORKDIR}/capice/${1}/venv/bin/activate"
	pip --no-cache-dir install -e "${WORKDIR}/capice/${1}[test]"
	module purge
	echo "finished installing capice ${1}"
}

create_train_data() {
	echo "running train-data-creator"
	module load Python/3.10.4-GCCcore-11.3.0-bare
	python3 -m venv "${CAPICE_RESOURCES}/venv"
	source ${CAPICE_RESOURCES}/venv/bin/activate
	train-data-creator -v ${VKGL_FILE} -c ${CLINVAR_FILE} -o ${WORKDIR}/data/
	deactivate
	module purge
	echo "finished running train-data-creator"
}

vep() {
	echo "running vep on train test"
	bash ${CAPICE_RESOURCES}/utility_scripts/slurm_run_vep.sh -p ${VIP_DIR} -g -i ${WORKDIR}/data/train_test.vcf.gz -o ${WORKDIR}/data/train_test_vep.vcf.gz
	bash ${CAPICE}/scripts/convert_vep_vcf_to_tsv_capice.sh -p ${BCFTOOLS_SIF} -t -i ${WORKDIR}/data/train_test_vep.vcf.gz -o ${WORKDIR}/data/train_test_vep.tsv.gz
	echo "finished running vep on train test"
	echo "running vep on validation"
	bash ${CAPICE_RESOURCES}/utility_scripts/slurm_run_vep.sh -p ${VIP_DIR} -g -i ${WORKDIR}/data/validation.vcf.gz -o ${WORKDIR}/data/validation_vep.vcf.gz
	bash ${CAPICE}/scripts/convert_vep_vcf_to_tsv_capice.sh -p ${BCFTOOLS_SIF} -t -i ${WORKDIR}/data/validation_vep.vcf.gz -o ${WORKDIR}/data/validation_vep.tsv.gz
	echo "finished running vep on validation"
}

postprocess(){
  	echo "running process_vep"
  	wget -P ${WORKDIR}/data/ https://research.nhgri.nih.gov/CGD/download/txt/CGD.txt.gz
  	module load Python/3.10.4-GCCcore-11.3.0-bare
  	source ${CAPICE_RESOURCES}/venv/bin/activate
  	process-vep -a -g ${WORKDIR}/data/CGD.txt.gz -f ${CAPICE}/resources/train_features.json -t ${WORKDIR}/data/train_test_vep.tsv.gz -v ${WORKDIR}/data/validation_vep.tsv.gz -o ${WORKDIR}/data/processed/
  	deactivate
  	module purge
  	echo "finished process_vep"
}

create_model_job() {
	echo "writing train script"
	mkdir -p "${WORKDIR}/model/"
	mkdir -p "${WORKDIR}/scripts/"
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
" > ${WORKDIR}/scripts/train.sh
	echo "finished writing train script"
}

train(){
	echo "running capice training"
	bash ${WORKDIR}/scripts/train.sh
	echo "finished capice training"
}

download_model() {
	echo "downlooading model"
	wget -P ${WORKDIR}/validation/ "https://github.com/molgenis/capice/releases/download/${PROD_CAPICE_VERSION}/${PROD_MODEL}"
	echo "finished downloading model"
}

run_capice(){
    echo "running capice ${1}"
	module load Python/3.10.4-GCCcore-11.3.0-bare
	source $1/venv/bin/activate
	capice predict -i ${WORKDIR}/data/processed/validation.tsv.gz -m $2 -o $3
	deactivate
    echo "finished running capice ${1}"
}

compare_and_threshold(){
    echo "running compare_and_threshold"
	source ${CAPICE_RESOURCES}/venv/bin/activate
	compare-model-performance -a ${WORKDIR}/validation/new_validation_predicted.tsv.gz -l ${WORKDIR}/data/processed/validation.tsv.gz -b ${WORKDIR}/validation/prod_validation_predicted.tsv.gz -o ${WORKDIR}/validation/performance
	threshold-calculator -v ${WORKDIR}/data/processed/validation.tsv.gz -s ${WORKDIR}/validation/new_validation_predicted.tsv.gz -o ${WORKDIR}/validation/threshold/
	deactivate
    echo "finished compare_and_threshold"
}

explain(){
  source ${CAPICE}/venv/bin/activate
  mkdir -p ${WORKDIR}/explain/
  capice explain -i ${WORKDIR}/model/capice_model.ubj -o ${WORKDIR}/explain/new_explain.tsv.gz
  capice explain -i ${WORKDIR}/validation/${PROD_MODEL} -o ${WORKDIR}/explain/${PROD_CAPICE_VERSION}_explain.tsv.gz
  deactivate
}

merge_rank(){
  source ${CAPICE_RESOURCES}/venv/bin/activate
  compare-model-features -a ${WORKDIR}/explain/new_explain.tsv.gz -b ${WORKDIR}/explain/${PROD_CAPICE_VERSION}_explain.tsv.gz -o ${WORKDIR}/explain/merged_grch38.tsv.gz
  deactivate
}

main "$@"
