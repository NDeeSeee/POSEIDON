#!/bin/bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage: $0 [--directory DIR ...]

Download missing SRA files listed in sra_download_plan.tsv. If one or more
--directory options are supplied, only those directories are processed.
USAGE
}

BASE_DIR="/data/salomonis-archive/FASTQs/NCI-R01/POSEIDON"
PLAN_FILE="$BASE_DIR/sra_download_plan.tsv"
LOG_DIR="$BASE_DIR/logs"
LOG_FILE="$LOG_DIR/sra_download_$(date +%Y%m%d_%H%M%S).log"

mkdir -p "$LOG_DIR"

declare -a FILTER_DIRS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --directory)
      if [[ $# -lt 2 ]]; then
        echo "ERROR: --directory requires an argument" >&2
        exit 1
      fi
      FILTER_DIRS+=("$2")
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ ! -f "$PLAN_FILE" ]]; then
  echo "ERROR: Plan file not found: $PLAN_FILE" >&2
  exit 1
fi

module load sratoolkit/2.10.4
module load aspera/3.9.1

mapfile -t PLAN_LINES < <(tail -n +2 "$PLAN_FILE")

echo "=== SRA DOWNLOAD START $(date) ===" | tee -a "$LOG_FILE"

for line in "${PLAN_LINES[@]}"; do
  rel_dir=${line%%$'\t'*}
  srr_id=${line##*$'\t'}
  rel_dir=$(echo "$rel_dir" | tr -d '\r' | xargs)
  srr_id=$(echo "$srr_id" | tr -d '\r' | xargs)

  if [[ -n "${FILTER_DIRS[@]-}" ]]; then
    skip=true
    for dir in "${FILTER_DIRS[@]}"; do
      if [[ "$rel_dir" == "$dir" ]]; then
        skip=false
        break
      fi
    done
    $skip && continue
  fi

  if [[ -z "$rel_dir" || -z "$srr_id" ]]; then
    continue
  fi

  target_dir="$BASE_DIR/$rel_dir"
  if [[ ! -d "$target_dir" ]]; then
    echo "[WARN] Directory missing: $target_dir" | tee -a "$LOG_FILE"
    continue
  fi

  cd "$target_dir"

  if [[ -f "${srr_id}.sra" ]]; then
    echo "[SKIP] ${rel_dir} ${srr_id} (SRA already present)" | tee -a "$LOG_FILE"
    continue
  fi

  # clean up stray nested directory from previous attempt
  if [[ -d "$srr_id" ]]; then
    find "$srr_id" -type f -name '*.sra' -exec mv {} . \;
    rmdir "$srr_id" 2>/dev/null || true
    if [[ -f "${srr_id}.sra" ]]; then
      echo "[SKIP] ${rel_dir} ${srr_id} (SRA found after cleanup)" | tee -a "$LOG_FILE"
      continue
    fi
  fi

  echo "[INFO] Downloading ${rel_dir} ${srr_id}" | tee -a "$LOG_FILE"

  ngc_file=$(ls *.ngc 2>/dev/null | head -n 1 || true)
  PREFETCH_OPTS=(--output-directory "$target_dir" -f all -X 35000000 "$srr_id")
  if [[ -n "$ngc_file" ]]; then
    prefetch_cmd=(prefetch --ngc "$ngc_file" "${PREFETCH_OPTS[@]}")
  else
    prefetch_cmd=(prefetch "${PREFETCH_OPTS[@]}")
  fi

  set +e
  "${prefetch_cmd[@]}" >> "$LOG_FILE" 2>&1
  status=$?
  set -e

  if [[ $status -ne 0 ]]; then
    echo "[WARN] ${rel_dir} ${srr_id} (prefetch exit $status)" | tee -a "$LOG_FILE"
  fi

  if [[ -d "$srr_id" ]]; then
    find "$srr_id" -type f -name '*.sra' -exec mv {} . \;
    rmdir "$srr_id" 2>/dev/null || true
  fi

  if [[ -f "${srr_id}.sra" ]]; then
    echo "[OK] ${rel_dir} ${srr_id}" | tee -a "$LOG_FILE"
  else
    echo "[WARN] ${rel_dir} ${srr_id} (SRA missing after download attempt)" | tee -a "$LOG_FILE"
  fi

done

echo "=== SRA DOWNLOAD END $(date) ===" | tee -a "$LOG_FILE"
