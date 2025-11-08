#!/usr/bin/env bash
set -euo pipefail

# Small script to:
# 1) Submit LSF jobs to extract altanalyze_output.tar.gz in each tissue subdirectory
#    and prune contents to only ExpressionInput
# 2) Produce a TSV summary from metadata.txt with columns:
#    tissue_name, acronym, num_samples, status (downloaded_and_unpacked|missing_yet)

BASE_DIR="$(cd "${BASH_SOURCE[0]%/*}" && pwd)"
cd "$BASE_DIR"

# --- Configuration ---
# 32 GB memory, 2 cores, 4 minutes
BSUB_CORES=2
BSUB_MEM_MB=32000
BSUB_WALL="0:04"

# Output paths for per-job logs
LOG_DIR="$BASE_DIR/.lsf_logs"
mkdir -p "$LOG_DIR"

# Submit one job per subdirectory containing altanalyze_output.tar.gz
submit_jobs() {
  shopt -s nullglob
  for tissue_dir in "$BASE_DIR"/*/ ; do
    [ -d "$tissue_dir" ] || continue
    tissue_name=$(basename "$tissue_dir")
    tarball="$tissue_dir/altanalyze_output.tar.gz"
    # Only submit if the tarball exists and ExpressionInput is not already present
    if [[ -f "$tarball" ]]; then
      if [[ -d "$tissue_dir/altanalyze_output/ExpressionInput" ]]; then
        echo "[SKIP] $tissue_name: already unpacked (ExpressionInput exists)" >&2
        continue
      fi
      job_name="unpack_${tissue_name}"
      out_log="$LOG_DIR/${job_name}.out"
      err_log="$LOG_DIR/${job_name}.err"
      echo "[SUBMIT] $tissue_name: extracting altanalyze_output.tar.gz" >&2
      bsub \
        -J "$job_name" \
        -n "$BSUB_CORES" \
        -R "span[hosts=1] rusage[mem=${BSUB_MEM_MB}]" \
        -W "$BSUB_WALL" \
        -oo "$out_log" -eo "$err_log" \
        bash -lc "set -euo pipefail; cd \"$tissue_dir\" && tar -xvzf \"$tarball\" && cd altanalyze_output && find . -mindepth 1 -maxdepth 1 -not -name 'ExpressionInput' -exec rm -rf {} +"
    else
      echo "[INFO] $tissue_name: no altanalyze_output.tar.gz present" >&2
    fi
  done
}

normalize_key() {
  # Lowercase; spaces and hyphens to underscores; collapse multiple underscores
  awk '{print tolower($0)}' | sed -E 's/[ -]+/_/g; s/_+/_/g'
}

build_dir_map() {
  # Build mapping of normalized_dir_name -> absolute_dir_path into global associative array DIR_MAP
  declare -gA DIR_MAP=()
  shopt -s nullglob
  for d in "$BASE_DIR"/*/; do
    [[ -d "$d" ]] || continue
    dn=$(basename "$d")
    norm=$(printf "%s" "$dn" | normalize_key)
    DIR_MAP["$norm"]="${d%/}"
  done
}

# Produce TSV summary using metadata.txt
# Columns: tissue_name<TAB>acronym<TAB>num_samples<TAB>status[\tsubmission_id\tworkflow_id (if present later)]
# status values: downloaded_and_unpacked | missing_yet
summarize_metadata() {
  local meta_file="$BASE_DIR/metadata.txt"
  local out_tsv="$BASE_DIR/metadata_summary.tsv"
  if [[ ! -f "$meta_file" ]]; then
    echo "metadata.txt not found at $meta_file" >&2
    return 1
  fi

  build_dir_map

  declare -A ACR
  # Editable acronym mappings (fallback applied if missing)
  ACR[breast]=BRCA
  ACR[lung]=LUNG
  ACR[muscle]=MUSC
  ACR[nerve]=NERV
  ACR[pituitary]=PIT
  ACR[prostate]=PRAD
  ACR[testis]=TGCT
  ACR[thyroid]=THCA
  ACR[fallopian_tube]=FALLO

  # Directory overrides (normalized metadata tissue -> normalized folder key)
  declare -A TISSUE_ALIAS
  TISSUE_ALIAS[fallopian_tube]=fallopian
  TISSUE_ALIAS[cervix_uteri]=cervix_utery

  # Header
  printf "tissue_name\tacronym\tnum_samples\tstatus\n" > "$out_tsv"

  # Parse lines like: "  568 breast"
  while IFS= read -r line; do
    # Match lines beginning with number then tissue token
    if [[ "$line" =~ ^[[:space:]]*([0-9]+)[[:space:]]+([a-z_]+)[[:space:]]*$ ]]; then
      count="${BASH_REMATCH[1]}"
      tissue_key="${BASH_REMATCH[2]}"  # lower-case with underscores per metadata

      # Compute display tissue name: Title_Case with underscores (to match existing directories/TSV style)
      tissue_display=$(sed 's/_/ /g' <<<"$tissue_key" | awk '{for (i=1;i<=NF;i++){ $i=toupper(substr($i,1,1)) substr($i,2)}; print}' | sed 's/ /_/g')

      # Determine normalized directory key to check
      norm_tissue="$tissue_key"
      if [[ -n "${TISSUE_ALIAS[$tissue_key]:-}" ]]; then
        norm_tissue="${TISSUE_ALIAS[$tissue_key]}"
      fi

      # Acronym mapping with fallback to uppercased first 4 letters of tissue_key
      acronym="${ACR[$tissue_key]:-}"
      if [[ -z "$acronym" ]]; then
        acronym=$(tr '[:lower:]' '[:upper:]' <<<"${tissue_key}" | cut -c1-4)
      fi

      status="missing_yet"
      dir_path="${DIR_MAP[$(printf "%s" "$norm_tissue" | normalize_key)]-}"
      if [[ -n "$dir_path" && -d "$dir_path/altanalyze_output/ExpressionInput" ]]; then
        status="downloaded_and_unpacked"
      fi

      printf "%s\t%s\t%s\t%s\n" "$tissue_display" "$acronym" "$count" "$status" >> "$out_tsv"
    fi
  done < "$meta_file"

  echo "Wrote summary: $out_tsv" >&2
}

# Refresh only the status column in an existing metadata_summary.tsv based on real directories
refresh_statuses_in_tsv() {
  local tsv="$BASE_DIR/metadata_summary.tsv"
  [[ -f "$tsv" ]] || { echo "No metadata_summary.tsv to refresh" >&2; return 0; }

  build_dir_map
  # Same aliases as above
  declare -A TISSUE_ALIAS
  TISSUE_ALIAS[fallopian_tube]=fallopian
  TISSUE_ALIAS[cervix_uteri]=cervix_utery

  local tmp="$tsv.tmp"
  awk -F"\t" -v BASE_DIR="$BASE_DIR" -v OFS="\t" '
    function normalize_key(s,  t){
      gsub(/[ -]+/, "_", s);
      gsub(/_+/, "_", s);
      return tolower(s);
    }
  ' < /dev/null >/dev/null 2>&1

  # Use awk to rewrite status using a shell-evaluated test for directory existence
  {
    IFS=$'\n'
    read -r header || true
    printf "%s\n" "$header"
    while IFS=$'\n' read -r line; do
      [[ -z "$line" ]] && { printf "\n"; continue; }
      tissue_name=$(cut -f1 <<<"$line")
      # Normalize tissue name from TSV
      norm=$(printf "%s" "$tissue_name" | sed 's/ /_/g' | awk '{print tolower($0)}')
      case "$norm" in
        cervix_uteri) norm=cervix_utery;;
        fallopian_tube) norm=fallopian;;
      esac
      dir_path="${DIR_MAP[$norm]-}"
      new_status="missing_yet"
      if [[ -n "$dir_path" && -d "$dir_path/altanalyze_output/ExpressionInput" ]]; then
        new_status="downloaded_and_unpacked"
      fi
      # Rebuild the line with updated 4th column while preserving other columns
      cols=()
      IFS=$'\t' read -r -a cols <<<"$line"
      cols[3]="$new_status"
      printf "%s" "${cols[0]}"
      for ((i=1;i<${#cols[@]};i++)); do
        printf "\t%s" "${cols[i]}"
      done
      printf "\n"
    done
  } < "$tsv" > "$tmp"
  mv -f "$tmp" "$tsv"
  echo "Refreshed statuses in $tsv" >&2
}

# Default behavior: submit any needed jobs, then refresh statuses if summary exists,
# otherwise create a fresh summary from metadata.txt
submit_jobs
if [[ -f "$BASE_DIR/metadata_summary.tsv" ]]; then
  refresh_statuses_in_tsv
else
  summarize_metadata
fi

echo "Done. LSF jobs submitted (if any). Summary TSV generated." >&2
