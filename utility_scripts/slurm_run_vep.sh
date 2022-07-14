#!/bin/bash
#
# Ensure first 3 lines below are adjusted accordingly!
#
#SBATCH --job-name=<jobname>
#SBATCH --output=/path/to/<jobname>.log
#SBATCH --error=/path/to/<jobname>.err
#SBATCH --time=1:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=2gb
#SBATCH --nodes=1
#SBATCH --export=NONE
#SBATCH --get-user-env=L60

ml load vip

# Adjust paths to actual data!
input_path='/path/to/train_test.vcf.gz'
output_path='/path/to/train_test_annotated.vcf.gz'

# Ensure paths below are still up-to-date!
vep_image_path='/path/to/vep-105.0.sif'
vep_cache_dir='/apps/data/Ensembl/VEP/105'
splice_ai_snv_path='/apps/data/SpliceAI/GRCh37/spliceai_scores.raw.snv.vcf.gz'
splice_ai_indel_path='/apps/data/SpliceAI/GRCh37/spliceai_scores.raw.indel.vcf.gz'
gnomad_sites_path='/apps/data/gnomAD/v2.1.1/gnomad.total.r2.1.1.sites.stripped.vcf.gz'
vep_plugins_path="${EBROOTVIP}/plugins/vep/"

# Ensure command below is up-to-date with https://github.com/molgenis/capice/#vep!!!
# Ensure `--buffer_size 500` is added (or something similar) te reduce memory usage on a cluster.
# If used for the train-test dataset, be sure to add `--per_gene` to the command below!
run_vep() {
  singularity exec --bind /apps,/groups,/tmp "${vep_image_path}" \
  vep --input_file "$1" --format vcf --output_file "$2" --vcf --compress_output gzip --sift s \
   --polyphen s --numbers --symbol --shift_3prime 1 --allele_number --refseq --total_length \
   --no_stats --offline --dir_cache "${vep_cache_dir}" --species "homo_sapiens" --assembly GRCh37 \
   --fork 4 --dont_skip --allow_non_variant --use_given_ref --exclude_predicted --use_given_ref \
   --flag_pick_allele --buffer_size 500 \
   --plugin SpliceAI,snv="${splice_ai_snv_path}",indel="${splice_ai_indel_path}" \
   --dir_plugins "${vep_plugins_path}" --custom "${gnomad_sites_path},gnomAD,vcf,exact,0,AF,HN"
}

run_vep "${input_path}" "${output_path}"