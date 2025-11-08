#!/bin/bash
# ================================================================
# Parallel SRA download submission script (LSF)
# Submits one job per SRR ID from an input list for parallel prefetch
# ================================================================

# Usage:
#   ./submit_sra_downloads.sh SRR_list.txt
# ================================================================

# Input SRR list
SRR_LIST=$1
if [ -z "$SRR_LIST" ]; then
    echo "Usage: $0 <SRR_list.txt>"
    exit 1
fi

# Directories
ROOT=$PWD
LOG_DIR=${ROOT}/logs
SRA_DIR=${ROOT}/sra

mkdir -p ${LOG_DIR} ${SRA_DIR}

# ----------------------------------------------------------------
# Recommended LSF settings:
#   -W 24:00          walltime (24 hours)
#   -n 1              one thread per prefetch job
#   -R "rusage[mem=16000]"  request 16 GB memory
#   -M 16000          memory limit
# ----------------------------------------------------------------

# Loop through SRR IDs and submit one job per SRR
while read SRR; do
    [ -z "$SRR" ] && continue
    bsub -W 24:00 -n 1 -M 16000 \
         -R "rusage[mem=16000] span[hosts=1]" \
         -J "prefetch_${SRR}" \
         -o ${LOG_DIR}/prefetch_${SRR}.out \
         -e ${LOG_DIR}/prefetch_${SRR}.err \
         "module load sratoolkit/2.10.4 && \
          echo '=== Downloading ${SRR} ===' && \
          prefetch ${SRR} --output-directory ${SRA_DIR} && \
          # Move the resulting .sra file to ROOT directory \
          if [ -f ${SRA_DIR}/${SRR}/${SRR}.sra ]; then \
              mv ${SRA_DIR}/${SRR}/${SRR}.sra ${ROOT}/; \
              rmdir ${SRA_DIR}/${SRR} 2>/dev/null || true; \
          fi && \
          echo '=== Completed ${SRR} === (moved to ${ROOT})'"
done < ${SRR_LIST}

echo "Submitted one LSF prefetch job per SRR ID from ${SRR_LIST}."
