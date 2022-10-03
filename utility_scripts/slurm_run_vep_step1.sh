#!/bin/bash
#
# Ensure first 3 lines below are adjusted accordingly!
#
#SBATCH --job-name=capice_vep_step1
#SBATCH --output=/path/to/output/dir/capice_vep_step1.log
#SBATCH --error=/path/to/output/dir/capice_vep_step1.err
#SBATCH --time=1:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=2gb
#SBATCH --nodes=1
#SBATCH --export=NONE
#SBATCH --get-user-env=L60

# Ensure these paths are set correctly!!!
vip_dir='/path/to/vip/'
input_dir='/path/to/directory/with/input/scripts/'
output_dir='/path/to/write/output/files/to/'
n_threads=4

# Defines all vip-specific paths. Check if VIP gets updated!
vep_image_path="${vip_dir}images/vep-107.0.sif"
vep_cache_dir="${vip_dir}resources/vep/cache/"
splice_ai_snv_path="${vip_dir}resources/GRCh37/spliceai_scores.masked.snv.hg19.vcf.gz"
splice_ai_indel_path="${vip_dir}resources/GRCh37/spliceai_scores.masked.indel.hg19.vcf.gz"
gnomad_sites_path="${vip_dir}resources/GRCh37/gnomad.total.r2.1.1.sites.stripped.vcf.gz"
phylop_path="${vip_dir}resources/GRCh37/hg19.100way.phyloP100way.bw"
vep_plugins_path="${vip_dir}resources/vep/plugins/"

# Ensure command below is up-to-date with https://github.com/molgenis/capice/#vep!!!
# While not present in regular VEP runs for CAPICE, `--per_gene` should be added to it!!!
# Ensure `--buffer_size 500` is added (or something similar) te reduce memory usage on a cluster.
run_vep() {
  singularity exec --bind /apps,/groups,/tmp "${vep_image_path}" \
  vep --input_file "$1" --format vcf --output_file "$2" \
  --vcf --compress_output gzip --sift s --polyphen s --numbers --symbol \
  --shift_3prime 1 --allele_number --refseq --total_length --no_stats --offline --cache \
  --dir_cache "${vep_cache_dir}" --species "homo_sapiens" --assembly GRCh37 --fork "${n_threads}" \
  --dont_skip --allow_non_variant --use_given_ref --exclude_predicted \
  --flag_pick_allele --plugin Grantham \
  --plugin SpliceAI,snv="${splice_ai_snv_path}",indel="${splice_ai_indel_path}" \
  --custom "${gnomad_sites_path},gnomAD,vcf,exact,0,AF,HN" \
  --custom "${phylop_path},phyloP,bigwig,exact,0" \
  --dir_plugins "${vep_plugins_path}" --per_gene --buffer_size 500
}

run_vep "${input_dir}train_input_raw.vcf.gz" "${output_dir}train_input_annotated.vcf.gz"
run_vep "${input_dir}predict_input_raw.vcf.gz" "${output_dir}predict_input.vcf.gz"
run_vep "${input_dir}breakends.vcf.gz" "${output_dir}breakends_vep.vcf.gz"
run_vep "${input_dir}edge_cases.vcf.gz" "${output_dir}edge_cases_vep.vcf.gz"
run_vep "${input_dir}symbolic_alleles.vcf.gz" "${output_dir}symbolic_alleles_vep.vcf.gz"