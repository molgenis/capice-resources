#!/bin/bash
#SBATCH --job-name=capice_poc
#SBATCH --time=23:59:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=16gb
#SBATCH --nodes=1
#SBATCH --export=NONE
#SBATCH --get-user-env=L60

set -e

errcho() { echo "$@"  1>&2; }

main() {
	digestCommandLine "$@"

	mkdir -p "${WORKDIR}/data/"
	CAPICE="${WORKDIR}/capice"

	install_capice_resources
	install_capice
	download
	run_vep
	conversion_tool
	process_vep
	create_poc_job
	train
	vcf_to_tsv
	copy_to_capice
	run_test
}

digestCommandLine() {
	readonly USAGE="
	Usage:
	create_poc.sh -a <arg> -n <arg> -b <arg> -w <arg> -r <arg> -p <arg>
		a) apptainer bind
		n) name of the capice branch
		b) path/to/bcftools_sif
		w) path/to/workdir
		r) path/to/capice_resources
		p) path/to/vip
	"

	while getopts a:n:b:j:w:r:p: flag
	do
		case "${flag}" in
			a) BIND=${OPTARG};;
			n) CAPICE_BRANCH=${OPTARG};;
			b) BCFTOOLS_SIF=${OPTARG};;
			w) WORKDIR=${OPTARG};;
			r) CAPICE_RESOURCES=${OPTARG};;
			p)
				VIP_DIR=${OPTARG};;
			\?)
				errcho "Error: invalid option"
				echo "${USAGE}"
				exit 1;;
		esac
	done
}

download(){
	echo "downloading"
	#FIXME: branchname in url
	curl -Ls -o "${WORKDIR}/data/train_input_raw.vcf.gz" "https://github.com/molgenis/capice/raw/feat/noGnomad/resources/train_input_raw.vcf.gz"
	curl -Ls -o "${WORKDIR}/data/predict_input_raw.vcf.gz" "https://github.com/molgenis/capice/raw/feat/noGnomad/resources/predict_input_raw.vcf.gz"
	curl -Ls -o "${WORKDIR}/data/breakends.vcf.gz" "https://github.com/molgenis/capice/raw/feat/noGnomad/tests/resources/breakends.vcf.gz"
	curl -Ls -o "${WORKDIR}/data/edge_cases.vcf.gz" "https://github.com/molgenis/capice/raw/feat/noGnomad/tests/resources/edge_cases.vcf.gz"
	curl -Ls -o "${WORKDIR}/data/symbolic_alleles.vcf.gz" "https://github.com/molgenis/capice/raw/feat/noGnomad/tests/resources/symbolic_alleles.vcf.gz"
	echo "finished downloading"
}

run_vep(){
	echo "running vep"
	for file in ${WORKDIR}/data/*.vcf.gz; do bash ${CAPICE_RESOURCES}/utility_scripts/slurm_run_vep.sh -p ${VIP_DIR} -i "${file}" -g -o "${file%.vcf.gz}_vep.vcf.gz"; done
	 mv "${WORKDIR}/data/train_input_raw_vep.vcf.gz" "${WORKDIR}/data/train_input_annotated.vcf.gz"
	 mv "${WORKDIR}/data/predict_input_raw_vep.vcf.gz" "${WORKDIR}/data/predict_input.vcf.gz"
	echo "finished running vep"
}

conversion_tool(){
	bash "${CAPICE}/scripts/convert_vep_vcf_to_tsv_capice.sh" -t -i "${WORKDIR}/data/train_input_annotated.vcf.gz" -o "${WORKDIR}/data/train_input_annotated.tsv.gz" -p "${BCFTOOLS_SIF}"
}

install_capice_resources(){
	echo "installing capice-resources"
	module load Python/3.10.4-GCCcore-11.3.0-bare
	python3 -m venv "${CAPICE_RESOURCES}/venv"
	source "${CAPICE_RESOURCES}/venv/bin/activate"
	pip --no-cache-dir install -e "${CAPICE_RESOURCES}[test]"
	deactivate
	module purge
	echo "finished installing capice-resources"
}

process_vep(){
	echo "running process_vep"
	wget -P "${WORKDIR}/data/" https://research.nhgri.nih.gov/CGD/download/txt/CGD.txt.gz
	module load Python/3.10.4-GCCcore-11.3.0-bare
	source "${CAPICE_RESOURCES}/venv/bin/activate"
	process-vep -g "${WORKDIR}/data/CGD.txt.gz" -f "${CAPICE}/resources/train_features.json" -t "${WORKDIR}/data/train_input_annotated.tsv.gz" -o "${WORKDIR}/data/processed/"
	deactivate
	module purge
	echo "finished process_vep"
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

create_poc_job() {
	echo "writing train script"
	echo "#!/bin/bash
#SBATCH --job-name=capice_train
#SBATCH --output=${WORKDIR}/capice_train.log
#SBATCH --error=${WORKDIR}/capice_train.err
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
-o ${WORKDIR}/xgb_booster_poc.ubj
" > "${WORKDIR}/train_poc.sh"
	echo "finished writing train script"
}

train(){
	echo "running capice training"
	bash "${WORKDIR}/train_poc.sh"
	echo "finished capice training"
}

vcf_to_tsv(){
	echo "running vcf_to_tsv"
	bash ${CAPICE}/scripts/convert_vep_vcf_to_tsv_capice.sh -p "${BCFTOOLS_SIF}" -t -i "${WORKDIR}/data/predict_input.vcf.gz" -o "${WORKDIR}/data/predict_input.tsv.gz"
	bash ${CAPICE}/scripts/convert_vep_vcf_to_tsv_capice.sh -p "${BCFTOOLS_SIF}" -t -i "${WORKDIR}/data/breakends_vep.vcf.gz" -o "${WORKDIR}/data/breakends_vep.tsv.gz"
	bash ${CAPICE}/scripts/convert_vep_vcf_to_tsv_capice.sh -p "${BCFTOOLS_SIF}" -t -i "${WORKDIR}/data/edge_cases_vep.vcf.gz" -o "${WORKDIR}/data/edge_cases_vep.tsv.gz"
	bash ${CAPICE}/scripts/convert_vep_vcf_to_tsv_capice.sh -p "${BCFTOOLS_SIF}" -t -i "${WORKDIR}/data/symbolic_alleles_vep.vcf.gz" -o "${WORKDIR}/data/symbolic_alleles_vep.tsv.gz"
	echo "finished vcf_to_tsv"
}

copy_to_capice(){
	echo "running copy_to_capice"
	cp "${WORKDIR}/data/processed/train_test.tsv.gz" "${CAPICE}/resources/"
	cp "${WORKDIR}/data/predict_input.tsv.gz" "${CAPICE}/resources/"
	cp "${WORKDIR}/xgb_booster_poc.ubj" "${CAPICE}/tests/resources/"
	cp "${WORKDIR}/data/breakends_vep.tsv.gz" "${CAPICE}/tests/resources/"
	cp "${WORKDIR}/data/edge_cases_vep.tsv.gz" "${CAPICE}/tests/resources/"
	cp "${WORKDIR}/data/symbolic_alleles_vep.tsv.gz" "${CAPICE}/tests/resources/"
	echo "finished copy_to_capice"
}

run_test(){
	echo "running test"
	module load Python/3.10.4-GCCcore-11.3.0-bare
	python3 -m venv "${CAPICE}/venv"
	source "${CAPICE}/venv/bin/activate"
	pip --no-cache-dir install -e "${CAPICE}[test]"
	cd "${CAPICE}"
	pytest
	deactivate
	module purge
	echo "finished test"
}

main "$@"
