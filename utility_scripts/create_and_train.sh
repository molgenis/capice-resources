#!/bin/bash
#SBATCH --time=23:59:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=32gb
#SBATCH --nodes=1
#SBATCH --export=NONE
#SBATCH --get-user-env=L60

set -e

errcho() { echo "$@"  1>&2; }

TRAIN=false

main() {
	digestCommandLine "$@"
	install_capice_resources "${CAPICE_RESOURCES}"
	install_capice "${CAPICE_BRANCH}"
	install_capice "${PROD_CAPICE_VERSION}"
	create_train_data
	download_prod_train_test
	filter_validation
	vep
	postprocess
	create_model_job
	train
	download_model
	run_capice "${WORKDIR}/venvs/capice${PROD_CAPICE_VERSION}" "${WORKDIR}/capice/${PROD_CAPICE_VERSION}/" "${WORKDIR}/validation/${PROD_MODEL}" "${WORKDIR}/validation/prod_validation_predicted.tsv.gz"
	run_capice "${WORKDIR}/venvs/capice${CAPICE_BRANCH}" "${WORKDIR}/capice/${CAPICE_BRANCH}/" "${WORKDIR}/model/capice_model.ubj" "${WORKDIR}/validation/new_validation_predicted.tsv.gz"
	compare_and_threshold
  	explain
  	merge_rank
}

digestCommandLine() {
	readonly USAGE="
	Usage:
	create_and_train.sh -v <arg> -c <arg> -b <arg> -w <arg> -r <arg> -n <arg> -p <arg> -t <arg> -m <arg> -d <arg>
    v) path/to/vkgl_file
		c) path/to/clinvar_file
		b) path/to/bcftools_sif
		w) path/to/workdir
		r) path/to/capice_resources
		n) capice branch name
		p) path/to/vip
		t) capice production tag
		m) capice production model file name
		d) capice traintest data file name
	"

	while getopts v:b:c:w:r:n:p:t:m:d: flag
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
			d) PROD_TRAIN_FILE=${OPTARG};;
			\?)
				errcho "Error: invalid option"
				echo "${USAGE}"
				exit 1;;
		esac
	done

	CAPICE="${WORKDIR}/capice/${CAPICE_BRANCH}"
}

install_capice_resources(){
	echo "installing capice resources"
	mkdir "${WORKDIR}/venvs/"
	module load Python/3.10.4-GCCcore-11.3.0-bare
	python3 -m venv "${WORKDIR}/venvs/capice-resources"
	source "${WORKDIR}/venvs/capice-resources/bin/activate"
	pip --no-cache-dir install "${CAPICE_RESOURCES}"
	module purge
	echo "finished installing capice resources"
}

install_capice(){
	echo "installing capice ${1}"
	git clone https://github.com/molgenis/capice.git "${WORKDIR}/capice/${1}"
	cd "${WORKDIR}/capice/${1}"
	git checkout "${1}"
	module load Python/3.10.4-GCCcore-11.3.0-bare
	python3 -m venv "${WORKDIR}/venvs/capice${1}"
	source "${WORKDIR}/venvs/capice${1}/bin/activate"
	pip --no-cache-dir install "${WORKDIR}/capice/${1}"
	module purge
	echo "finished installing capice ${1}"
}

create_train_data() {
	echo "running train-data-creator"
	module load Python/3.10.4-GCCcore-11.3.0-bare
	source ${WORKDIR}/venvs/capice-resources/bin/activate
	train-data-creator -v ${VKGL_FILE} -c ${CLINVAR_FILE} -o ${WORKDIR}/data/
	deactivate
	module purge
	echo "finished running train-data-creator"
}


download_prod_train_test() {
	mkdir -p ${WORKDIR}/validation/prod/
	echo "downloading production train_test"
	wget -P ${WORKDIR}/validation/prod/ "https://github.com/molgenis/capice/releases/download/${PROD_CAPICE_VERSION}/${PROD_TRAIN_FILE}"
	echo "finished downloading production train_test"
}

filter_validation() {
	ml HTSlib
	gunzip -c ${WORKDIR}/validation/prod/${PROD_TRAIN_FILE} > ${WORKDIR}/validation/prod/previous_train.vcf
	gunzip ${WORKDIR}/data/validation.vcf.gz
	awk 'FNR==NR { a[$1_$2_$4_$5]; next } /^#/ || !($1_$2_$4_$5 in a)' ${WORKDIR}/validation/prod/previous_train.vcf ${WORKDIR}/data/validation.vcf | bgzip > ${WORKDIR}/data/filtered_validation.vcf.gz
	rm ${WORKDIR}/data/validation.vcf
	rm ${WORKDIR}/validation/prod/previous_train.vcf
}

vep() {
	echo "running vep on train test"
	bash ${CAPICE_RESOURCES}/utility_scripts/slurm_run_vep.sh -p ${VIP_DIR} -g -i ${WORKDIR}/data/train_test.vcf.gz -o ${WORKDIR}/data/train_test_vep.vcf.gz
	bash ${CAPICE}/scripts/convert_vep_vcf_to_tsv_capice.sh -p ${BCFTOOLS_SIF} -t -i ${WORKDIR}/data/train_test_vep.vcf.gz -o ${WORKDIR}/data/train_test_vep.tsv.gz
	echo "finished running vep on train test"
	echo "running vep on validation"
	bash ${CAPICE_RESOURCES}/utility_scripts/slurm_run_vep.sh -p ${VIP_DIR} -g -i ${WORKDIR}/data/filtered_validation.vcf.gz -o ${WORKDIR}/data/validation_vep.vcf.gz
	bash ${CAPICE}/scripts/convert_vep_vcf_to_tsv_capice.sh -p ${BCFTOOLS_SIF} -t -i ${WORKDIR}/data/validation_vep.vcf.gz -o ${WORKDIR}/data/validation_vep.tsv.gz
	echo "finished running vep on validation"
}

postprocess(){
  	echo "running process_vep"
  	wget -P ${WORKDIR}/data/ https://research.nhgri.nih.gov/CGD/download/txt/CGD.txt.gz
  	module load Python/3.10.4-GCCcore-11.3.0-bare
  	source ${WORKDIR}/venvs/capice-resources/bin/activate
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
source ${WORKDIR}/venvs/capice${CAPICE_BRANCH}/bin/activate
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
	echo "downloading model"
	wget -P ${WORKDIR}/validation/ "https://github.com/molgenis/capice/releases/download/${PROD_CAPICE_VERSION}/${PROD_MODEL}"
	echo "finished downloading model"
}

run_capice(){
  echo "running capice ${2}"
	module load Python/3.10.4-GCCcore-11.3.0-bare
	source $1/bin/activate
	capice predict -i ${WORKDIR}/data/processed/validation.tsv.gz -m $3 -o $4
	deactivate
  echo "finished running capice ${2}"
}

compare_and_threshold(){
    echo "running compare_and_threshold"
  module load Python/3.10.4-GCCcore-11.3.0-bare
	source ${WORKDIR}/venvs/capice-resources/bin/activate
	compare-model-performance -a ${WORKDIR}/validation/new_validation_predicted.tsv.gz -l ${WORKDIR}/data/processed/validation.tsv.gz -b ${WORKDIR}/validation/prod_validation_predicted.tsv.gz -o ${WORKDIR}/validation/performance
	threshold-calculator -v ${WORKDIR}/data/processed/validation.tsv.gz -s ${WORKDIR}/validation/new_validation_predicted.tsv.gz -o ${WORKDIR}/validation/threshold/
	deactivate
    echo "finished compare_and_threshold"
}

explain(){
  module load Python/3.10.4-GCCcore-11.3.0-bare
  source ${WORKDIR}/venvs/capice${CAPICE_BRANCH}/bin/activate
  mkdir -p ${WORKDIR}/explain/
  capice explain -i ${WORKDIR}/model/capice_model.ubj -o ${WORKDIR}/explain/new_explain.tsv.gz
  capice explain -i ${WORKDIR}/validation/${PROD_MODEL} -o ${WORKDIR}/explain/${PROD_CAPICE_VERSION}_explain.tsv.gz
  deactivate
}

merge_rank(){
  module load Python/3.10.4-GCCcore-11.3.0-bare
  source ${WORKDIR}/venvs/capice-resources/bin/activate
  compare-model-features -a ${WORKDIR}/explain/new_explain.tsv.gz -b ${WORKDIR}/explain/${PROD_CAPICE_VERSION}_explain.tsv.gz -o ${WORKDIR}/explain/merged_grch38.tsv.gz
  deactivate
}

main "$@"