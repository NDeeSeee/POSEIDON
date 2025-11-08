#!/bin/bash
# ================================================================
# STAR 2-pass alignment LSF submission script
# Submits one job per sample from a sample list file
# Each job runs run_star-new.sh with appropriate FASTQ files.
# ================================================================

# Create output directories
mkdir -p bams logs

# Paths
ROOT=$PWD
SAMPLE_LIST=${ROOT}/sample_list_se.txt
LOG_FILE=${ROOT}/logs/job_submission_log.txt

# Initialize or timestamp the log file
echo "=== Job Submission Log ($(date)) ===" >> ${LOG_FILE}
echo "SAMPLE	FASTQ_FILE	LSF_JOBID	TIMESTAMP" >> ${LOG_FILE}

# ----------------------------------------------------------------
# Recommended LSF settings:
#   -W 12:00              walltime (12 hours)
#   -n 8                  use 8 threads per STAR run
#   -R "rusage[mem=16000]" request 16 GB per core (128 GB total)
#   -M 128000             total memory limit (matches 128 GB)
#   span[hosts=1]         keep all threads on one host
# ----------------------------------------------------------------
# Adjust -W or memory values if your cluster has tighter limits.
# ----------------------------------------------------------------

while read SAMPLE FASTQ1; do
    # Submit job and capture job ID
    JOBID=$(bsub -W 12:00 -n 2 -M 128000 \
        -R "rusage[mem=16000] span[hosts=1]" \
        -J "align_${SAMPLE}" \
        -o logs/STAR2pass_${SAMPLE}.out \
        -e logs/STAR2pass_${SAMPLE}.err \
        "$ROOT/run_star-new-se.sh $SAMPLE $FASTQ1" | awk '{print $2}' | tr -d '<>')

    # Log submission info
    echo -e "${SAMPLE}\t${FASTQ1}\t${JOBID}\t$(date)" >> ${LOG_FILE}
done < ${SAMPLE_LIST}

echo "All jobs submitted. Log written to ${LOG_FILE}"
# End of script
