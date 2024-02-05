#!/bin/bash
#SBATCH --job-name=capice_validate
#SBATCH --time=5:59:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=8gb
#SBATCH --nodes=1
#SBATCH --export=NONE
#SBATCH --get-user-env=L60

digestCommandLine() {
	readonly USAGE="
	Usage:
	create_and_train.sh -c <arg> -r <arg> -p <arg> -m <arg> -n <arg> -v <arg> -w <arg>
	c) new capice checked out and installed
	r) capice resources checked out and installed
	p) capice prod version
	m) capice prod model version
	n) new model
	v) vep processed validation
	w) work_dir
	"

	while getopts c:r:p:m:n:v:w: flag
	do
		case "${flag}" in
			c) NEW_CAPICE=${OPTARG};;
			r) CAPICE_RESOURCES=${OPTARG};;
			p) PROD_CAPICE_VERSION=${OPTARG};;
			m) PROD_MODEL=${OPTARG};;
			n) NEW_MODEL=${OPTARG};;
			v) VALIDATION_TSV=${OPTARG};;
			w) WORKDIR=${OPTARG};;
			\?)
				errcho "Error: invalid option"
				echo "${USAGE}"
				exit 1;;
		esac
	done
	
	CAPICE="${WORKDIR}/capice"
}

main() {
	digestCommandLine "$@"
	install_capice "${PROD_CAPICE_VERSION}"
	download_model
	run_capice "${WORKDIR}/capice_${PROD_CAPICE_VERSION}" "${WORKDIR}/${PROD_MODEL}" "${WORKDIR}/prod_validation_predicted.tsv.gz"
	run_capice "${NEW_CAPICE}" "${NEW_MODEL}" "${WORKDIR}/new_validation_predicted.tsv.gz"
	compare_and_threshold
}

download_model() {
	echo "downlooading model"
	wget -P ${WORKDIR} "https://github.com/molgenis/capice/releases/download/${PROD_CAPICE_VERSION}/${PROD_MODEL}"
	echo "finished downlooading model"
}

install_capice(){
	echo "installing capice ${1}"
	git clone https://github.com/molgenis/capice.git "${WORKDIR}/capice_${1}"
	cd "${WORKDIR}/capice_${1}"
	git checkout "${1}"
	module load Python/3.10.4-GCCcore-11.3.0-bare
	python3 -m venv "${WORKDIR}/capice_${1}/venv"
	source "${WORKDIR}/capice_${1}/venv/bin/activate"
	pip --no-cache-dir install -e "${WORKDIR}/capice_${1}[test]"
	module purge
	echo "finished installing capice ${1}"
}

run_capice(){
    echo "running capice ${1}"
	module load Python/3.10.4-GCCcore-11.3.0-bare
	source $1/venv/bin/activate
	capice predict -i ${VALIDATION_TSV} -m $2 -o $3
	deactivate
    echo "finished running capice ${1}"
}

compare_and_threshold(){
    echo "running compare_and_threshold"
	source ${CAPICE_RESOURCES}/venv/bin/activate
	compare-model-performance -a ${WORKDIR}/new_validation_predicted.tsv.gz -l ${VALIDATION_TSV} -b ${WORKDIR}/prod_validation_predicted.tsv.gz -o ${WORKDIR}/compare
	threshold-calculator -v ${VALIDATION_TSV} -s ${WORKDIR}/new_validation_predicted.tsv.gz -o ${WORKDIR}/threshold/
	deactivate
    echo "finished compare_and_threshold"
}

main "$@"