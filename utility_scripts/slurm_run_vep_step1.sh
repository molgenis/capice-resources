#!/bin/bash
#
# Ensure first 3 lines below are adjusted accordingly!
#
#SBATCH --job-name=vep_train_test
#SBATCH --output=/path/to/output/dir/vep_train_test.log
#SBATCH --error=/path/to/output/dir/vep_train_test.err
#SBATCH --time=1:00:00
#SBATCH  --cpus-per-task=4
#SBATCH --mem=2gb
#SBATCH --nodes=1

ml load vip

# Adjust paths to actual data!
home="/path/to/groups/account/"
# Assuming capice lives in your home
capice_resources_dir="${home}capice/resources/"
capice_test_resources_dir="${home}capice/tests/resources/"
output_dir="${home}train_gnomad_hn/"
train_input_path="${capice_resources_dir}train_input_raw.vcf.gz"
train_output_path="${output_dir}train_input_annotated.vcf.gz"
predict_input_path="${capice_resources_dir}predict_input_raw.vcf.gz"
predict_output_path="${output_dir}predict_input.vcf.gz"
breakend_input_path="${capice_test_resources_dir}breakends.vcf.gz"
breakend_output_path="${output_dir}breakends_vep.vcf.gz"
edge_input_path="${capice_test_resources_dir}edge_cases.vcf.gz"
edge_output_path="${output_dir}edge_cases_vep.vcf.gz"
symbolic_input_path="${capice_test_resources_dir}symbolic_alleles.vcf.gz"
symbolic_output_path="${output_dir}symbolic_alleles_vep.vcf.gz"



# Ensure paths below are still up-to-date!
vep_image_path='/path/to/sif/vep-105.0.sif'
vep_cache_dir='/apps/data/Ensembl/VEP/105'
splice_ai_snv_path='/apps/data/SpliceAI/GRCh37/spliceai_scores.raw.snv.vcf.gz'
splice_ai_indel_path='/apps/data/SpliceAI/GRCh37/spliceai_scores.raw.indel.vcf.gz'
gnomad_sites_path='/apps/data/gnomAD/v2.1.1/gnomad.total.r2.1.1.sites.stripped.vcf.gz'
vep_plugins_path="${EBROOTVIP}/plugins/vep/"


# Ensure command below is up-to-date with https://github.com/molgenis/capice/#vep!!!
# Ensure `--buffer_size 500` is added (or something similar) te reduce memory usage on a cluster.
run_vep() {
  singularity exec --bind /apps,/groups,/tmp "${vep_image_path}" \
  vep --input_file "$1" --format vcf --output_file "$2" --vcf --compress_output gzip --sift s \
   --polyphen s --numbers --symbol --shift_3prime 1 --allele_number --refseq --total_length \
   --no_stats --offline --dir_cache "${vep_cache_dir}" --species "homo_sapiens" --assembly GRCh37 \
   --fork 4 --dont_skip --allow_non_variant --use_given_ref --exclude_predicted --use_given_ref \
   --flag_pick_allele --per_gene --buffer_size 500 \
   --plugin SpliceAI,snv="${splice_ai_snv_path}",indel="${splice_ai_indel_path}" \
   --dir_plugins "${vep_plugins_path}" --custom "${gnomad_sites_path},gnomAD,vcf,exact,0,AF,HN"
}

run_vep "${train_input_path}" "${train_output_path}"
run_vep "${predict_input_path}" "${predict_output_path}"
run_vep "${breakend_input_path}" "${breakend_output_path}"
run_vep "${edge_input_path}" "${edge_output_path}"
run_vep "${symbolic_input_path}" "${symbolic_output_path}"