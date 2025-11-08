#!/usr/bin/env python3
import os
import sys
import csv
import subprocess
from typing import Dict, List, Optional, Tuple, Set

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
SRAMETA_DIR = os.path.join(REPO_ROOT, "SRAMetadataFiles")

# Accept common header aliases
SAMPLE_ID_HEADERS = {
    "biosample",
    "sample_accession",
    "samplename",
    "sample",
}
RUN_HEADERS = {"run", "run_accession"}
LAYOUT_HEADERS = {"librarylayout", "library_layout"}


def detect_delimiter(header_line: str) -> str:
    if "\t" in header_line:
        return "\t"
    return ","


def normalize_header(name: str) -> str:
    return name.strip().lower()


def load_local_metadata_mappings() -> Dict[str, List[Tuple[str, str]]]:
    """Return mapping: sample_id (SAMN/SAMEA) -> list of (run, layout)."""
    mapping: Dict[str, List[Tuple[str, str]]] = {}
    if not os.path.isdir(SRAMETA_DIR):
        return mapping

    # Collect .tsv and .csv files only
    for fn in os.listdir(SRAMETA_DIR):
        if not (fn.endswith(".tsv") or fn.endswith(".csv")):
            continue
        path = os.path.join(SRAMETA_DIR, fn)
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                first = fh.readline()
                if not first:
                    continue
                delim = detect_delimiter(first)
                fh.seek(0)
                reader = csv.DictReader(fh, delimiter=delim)
                # Map headers to lowercase
                field_map = {normalize_header(h): h for h in reader.fieldnames or []}
                # Find required columns
                sample_col = next((field_map[h] for h in SAMPLE_ID_HEADERS if h in field_map), None)
                run_col = next((field_map[h] for h in RUN_HEADERS if h in field_map), None)
                layout_col = next((field_map[h] for h in LAYOUT_HEADERS if h in field_map), None)
                if not sample_col or not run_col:
                    continue
                for row in reader:
                    sid = (row.get(sample_col) or "").strip()
                    run = (row.get(run_col) or "").strip()
                    layout = (row.get(layout_col) or "").strip().upper() if layout_col else ""
                    if not sid or not run:
                        continue
                    if layout not in {"PAIRED", "SINGLE"}:
                        # Best guess default; most datasets are paired
                        layout = layout or "PAIRED"
                    mapping.setdefault(sid, []).append((run, layout))
        except Exception:
            continue
    return mapping


def edirect_available() -> bool:
    return (shutil.which("esearch") is not None) and (shutil.which("efetch") is not None)


def query_runs_via_edirect(sample_id: str) -> List[Tuple[str, str]]:
    """Query NCBI SRA for a sample's runs using Entrez Direct. Returns list of (run, layout)."""
    cmd = f'esearch -db sra -query "{sample_id}" | efetch -format runinfo'
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if proc.returncode != 0 or not proc.stdout:
        return []
    runs: List[Tuple[str, str]] = []
    reader = csv.DictReader(proc.stdout.splitlines())
    for row in reader:
        run = (row.get("Run") or "").strip()
        layout = (row.get("LibraryLayout") or "").strip().upper()
        if not run:
            continue
        if layout not in {"PAIRED", "SINGLE"}:
            layout = "PAIRED"
        runs.append((run, layout))
    return runs


def build_r1_r2(runs_with_layouts: List[Tuple[str, str]]) -> Tuple[List[str], List[str]]:
    r1: List[str] = []
    r2: List[str] = []
    for run, layout in runs_with_layouts:
        if layout == "PAIRED":
            r1.append(f"{run}_1.fastq.gz")
            r2.append(f"{run}_2.fastq.gz")
        else:  # SINGLE
            r1.append(f"{run}_1.fastq.gz")
            # Do not add to r2; will be NA if stays empty
    return r1, r2


def read_discrepancies(csv_path: str) -> List[str]:
    missing: List[str] = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            in_bam = (row.get("in_bam_dir", "").strip().lower() in {"true", "1", "yes"})
            in_list = (row.get("in_sample_list", "").strip().lower() in {"true", "1", "yes"})
            sid = (row.get("sample_id") or "").strip()
            if in_bam and not in_list and sid:
                missing.append(sid)
    return missing


def read_existing_ids(sample_list_path: str) -> Set[str]:
    existing: Set[str] = set()
    if not os.path.isfile(sample_list_path):
        return existing
    with open(sample_list_path, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()  # whitespace
            if parts:
                existing.add(parts[0])
    return existing


def rename_incomplete(sample_list_path: str) -> Optional[str]:
    if not os.path.isfile(sample_list_path):
        return None
    incomplete_path = os.path.join(os.path.dirname(sample_list_path), "incomplete_sample_list.txt")
    # If a previous incomplete exists, overwrite it to reflect current state
    try:
        os.replace(sample_list_path, incomplete_path)
    except Exception:
        return None
    return incomplete_path


def process_directory(directory: str, local_map: Dict[str, List[Tuple[str, str]]]) -> Tuple[int, int]:
    csv_path = os.path.join(directory, "bam_disrepancies.csv")
    if not os.path.isfile(csv_path):
        return (0, 0)

    missing_ids = read_discrepancies(csv_path)
    if not missing_ids:
        return (0, 0)

    sample_list_path = os.path.join(directory, "sample_list.txt")
    existing_ids = read_existing_ids(sample_list_path)

    # Determine which truly missing samples we will add
    to_add = [sid for sid in missing_ids if sid not in existing_ids]
    if not to_add:
        return (0, 0)

    # Resolve runs for each sid
    resolved: Dict[str, Tuple[List[str], List[str]]] = {}

    # Try from local metadata first
    for sid in to_add:
        runs = local_map.get(sid, [])
        if runs:
            r1, r2 = build_r1_r2(runs)
            resolved[sid] = (r1, r2)

    # For any not resolved, query Entrez Direct
    for sid in to_add:
        if sid in resolved:
            continue
        runs = query_runs_via_edirect(sid)
        if not runs:
            continue
        r1, r2 = build_r1_r2(runs)
        resolved[sid] = (r1, r2)

    if not resolved:
        return (0, 0)

    # Rename original sample_list.txt to incomplete_sample_list.txt (if exists)
    renamed = rename_incomplete(sample_list_path)

    # Read original content (from incomplete if renamed; else empty)
    original_lines: List[str] = []
    base_path = os.path.join(directory, "incomplete_sample_list.txt") if renamed else sample_list_path
    if os.path.isfile(base_path):
        with open(base_path, "r", encoding="utf-8", errors="ignore") as fh:
            original_lines = fh.read().splitlines()

    # Write new complete sample_list.txt
    added_count = 0
    with open(sample_list_path, "w", encoding="utf-8") as out:
        for line in original_lines:
            out.write(line.rstrip("\n") + "\n")
        for sid in to_add:
            if sid not in resolved:
                continue
            r1_list, r2_list = resolved[sid]
            r1_field = ",".join(r1_list) if r1_list else "NA"
            r2_field = ",".join(r2_list) if r2_list else "NA"
            out.write(f"{sid}\t{r1_field}\t{r2_field}\n")
            added_count += 1

    return (len(to_add), added_count)


def main(root: str) -> int:
    local_map = load_local_metadata_mappings()
    dirs_processed = 0
    rows_added_total = 0
    for cur_dir, subdirs, files in os.walk(root):
        subdirs[:] = [d for d in subdirs if not d.startswith('.')]
        to_add_count, added_count = process_directory(cur_dir, local_map)
        if to_add_count or added_count:
            dirs_processed += 1
            print(f"{cur_dir}: to_add={to_add_count}, added={added_count}")
        rows_added_total += added_count
    print(f"Done. Directories updated: {dirs_processed}, rows added: {rows_added_total}")
    return 0


if __name__ == "__main__":
    import shutil
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else os.getcwd()))
