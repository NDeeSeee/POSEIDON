#!/bin/bash
set -euo pipefail

BASE_DIR="/data/salomonis-archive/FASTQs/NCI-R01/POSEIDON"
PLAN_FILE="$BASE_DIR/fastq_conversion_plan.tsv"
LOG_DIR="$BASE_DIR/logs"
LOG_FILE="$LOG_DIR/fastq_conversion_$(date +%Y%m%d_%H%M%S).log"

mkdir -p "$LOG_DIR"

if [[ ! -f "$PLAN_FILE" ]]; then
  echo "ERROR: Plan file not found: $PLAN_FILE" >&2
  exit 1
fi

mapfile -t PLAN_LINES < <(tail -n +2 "$PLAN_FILE")

if [[ ${#PLAN_LINES[@]} -eq 0 ]]; then
  echo "=== FASTQ CONVERSION START $(date) ===" | tee -a "$LOG_FILE"
  echo "[INFO] No pending conversions listed in $PLAN_FILE" | tee -a "$LOG_FILE"
  echo "=== FASTQ CONVERSION END $(date) ===" | tee -a "$LOG_FILE"
  exit 0
fi

echo "=== FASTQ CONVERSION START $(date) ===" | tee -a "$LOG_FILE"

for line in "${PLAN_LINES[@]}"; do
  rel_dir=${line%%$'\t'*}
  srr_id=${line##*$'\t'}
  rel_dir=$(echo "$rel_dir" | tr -d '\r' | xargs)
  srr_id=$(echo "$srr_id" | tr -d '\r' | xargs)

  if [[ -z "$rel_dir" || -z "$srr_id" ]]; then
    continue
  fi

  target_dir="$BASE_DIR/$rel_dir"
  if [[ ! -d "$target_dir" ]]; then
    echo "[WARN] Directory missing: $target_dir" | tee -a "$LOG_FILE"
    continue
  fi

  if [[ ! -f "$target_dir/sample_list.txt" ]]; then
    echo "[WARN] sample_list.txt missing in $target_dir" | tee -a "$LOG_FILE"
  fi

  if [[ -f "$target_dir/${srr_id}_1.fastq.gz" && -f "$target_dir/${srr_id}_2.fastq.gz" ]]; then
    echo "[SKIP] $rel_dir $srr_id (FASTQ already present)" | tee -a "$LOG_FILE"
    continue
  fi

  if [[ ! -f "$target_dir/${srr_id}.sra" ]]; then
    echo "[WARN] $rel_dir $srr_id missing .sra file" | tee -a "$LOG_FILE"
    continue
  fi

  echo "[INFO] Submitting conversion for $rel_dir $srr_id" | tee -a "$LOG_FILE"

  if (
    cd "$target_dir" &&
    bash "$BASE_DIR/ValeriiGitRepo/scripts/manual_pipeline/fdump.sh" "${srr_id}.sra"
  ) >> "$LOG_FILE" 2>&1; then
    echo "[OK] Submission requested for $rel_dir $srr_id" | tee -a "$LOG_FILE"
  else
    echo "[FAIL] Job submission failed for $rel_dir $srr_id" | tee -a "$LOG_FILE"
  fi
done

echo "=== FASTQ CONVERSION END $(date) ===" | tee -a "$LOG_FILE"
