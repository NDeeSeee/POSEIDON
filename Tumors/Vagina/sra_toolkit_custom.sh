#!/bin/bash
# ==========================================================
# LSF submission script to download SRA files and convert
# them to paired-end FASTQs using fastq-dump (gzip-compressed)
# ==========================================================

INPUTFILE=$1
SAMPLE=$(basename $INPUTFILE .sra)
DIR=$(pwd)

cat <<EOF
#BSUB -L /bin/bash
#BSUB -W 40:00
#BSUB -n 2
#BSUB -R "span[ptile=4]"
#BSUB -M 32000
#BSUB -e $DIR/logs/%J_sra.err.txt
#BSUB -o $DIR/logs/%J_sra.out.txt
#BSUB -J sra_download_${SAMPLE}

cd $DIR
mkdir -p logs sra fastq

# Load required modules
module load sratoolkit/2.10.4
module load aspera/3.9.1
module load python3/3.8.6

echo "=== Starting SRA download for ${INPUTFILE} ==="

# Prefetch missing SRA accessions
prefetch --option-file ${INPUTFILE} --output-directory sra

# Move all downloaded .sra files to ./sra
find sra -type f -name '*.sra' -exec mv {} sra/ \;

# Remove empty SRR directories (ignore rmdir warnings)
find sra -type d -name 'SRR*' -exec rmdir {} \; 2>/dev/null || true

# Convert .sra files to compressed FASTQs
for f in sra/*.sra; do
    base=\$(basename \$f .sra)
    echo "Converting \$base.sra to FASTQs..."
    fastq-dump --split-files --gzip --outdir fastq \$f
done

echo "=== All FASTQs generated successfully for ${INPUTFILE} ==="
EOF

# To submit:
# ./sratoolkit_fastq.sh <SRR_list.txt> | bsub
