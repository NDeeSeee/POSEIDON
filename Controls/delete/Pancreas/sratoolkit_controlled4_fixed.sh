#!/bin/bash
INPUTFILE=$1
DIR=$(pwd)

cat <<EOFBSUB
#BSUB -L /bin/bash
#BSUB -W 150:00
#BSUB -n 4
#BSUB -R "span[ptile=4]"
#BSUB -M 10000
#BSUB -e $DIR/logs/%J_sra.err.txt
#BSUB -o $DIR/logs/%J_sra.out.txt
#BSUB -J sra_download

cd $DIR

mkdir -p logs

module load sratoolkit/3.1.1
module load aspera/3.9.1 

#Bioproject PRJNA1093555. Controlled Pancreatic Samples
#Downloading samples from input file

EOFBSUB

# Read each line from the input file and create prefetch commands
while IFS= read -r line; do
    if [[ ! -z "$line" && ! "$line" =~ ^# ]]; then
        echo "prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 $line"
    fi
done < "$INPUTFILE"

cat <<EOFBSUB

EOFBSUB

# Submit the job
