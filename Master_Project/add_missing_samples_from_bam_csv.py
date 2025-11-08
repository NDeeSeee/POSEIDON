#!/usr/bin/env python3
import os
import sys
import csv
from typing import List, Optional, Tuple, Set

# We only update sample_list.txt (3 columns). If absent, create it.


def read_bam_discrepancies(csv_path: str) -> List[str]:
    """Return sample_ids that are in_bam_dir==True and in_sample_list==False."""
    missing: List[str] = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            try:
                in_bam = row.get("in_bam_dir", "").strip().lower() in {"true", "1", "yes"}
                in_sample = row.get("in_sample_list", "").strip().lower() in {"true", "1", "yes"}
            except Exception:
                continue
            if in_bam and not in_sample:
                sid = (row.get("sample_id") or "").strip()
                if sid:
                    missing.append(sid)
    return missing


def read_existing_sample_ids(sample_list_path: str) -> Set[str]:
    ids: Set[str] = set()
    if not os.path.isfile(sample_list_path):
        return ids
    with open(sample_list_path, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()  # whitespace-separated
            if parts:
                ids.add(parts[0])
    return ids


def find_star_log_for_sample(directory: str, sample_id: str) -> Optional[str]:
    candidates = [
        os.path.join(directory, f"{sample_id}_Log.out"),
        os.path.join(directory, f"{sample_id}_Log.progress.out"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    return None


def parse_read_files_in_from_log(log_path: str) -> Tuple[List[str], List[str]]:
    """
    Parse STAR log for readFilesIn.
    Returns (r1_list, r2_list). If single-end, r2_list will be empty.
    """
    r1: List[str] = []
    r2: List[str] = []
    with open(log_path, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if "readFilesIn" in line:
                # Normalize whitespace
                parts = line.strip().split()
                try:
                    idx = parts.index("readFilesIn")
                except ValueError:
                    # Lines in some STAR logs are in table format; try another heuristic
                    if line.strip().startswith("readFilesIn"):
                        # e.g., "readFilesIn  file1 file2"
                        parts = line.strip().split()
                        idx = 0
                    else:
                        continue
                args = parts[idx + 1 :]
                # Remove trailing column descriptors like "~RE-DEFINED"
                if args and args[-1].startswith("~"):
                    # Trim until before first token starting with '~'
                    clean: List[str] = []
                    for tok in args:
                        if tok.startswith("~"):
                            break
                        clean.append(tok)
                    args = clean
                if not args:
                    continue
                # If exactly 2 args, they are paired lists which may be comma-separated lists
                if len(args) >= 2:
                    r1_arg = args[0]
                    r2_arg = args[1]
                    r1 = [x for x in r1_arg.split(",") if x]
                    r2 = [x for x in r2_arg.split(",") if x]
                    # If there are more tokens, sometimes STAR repeats in different sections; keep first found only
                    break
                else:
                    # Single-end or truncated; take the one token as R1
                    r1 = [args[0]]
                    r2 = []
                    break
    return r1, r2


def ensure_sample_list(path: str) -> None:
    if not os.path.isfile(path):
        # Create with no header (consistent with existing files)
        open(path, "a", encoding="utf-8").close()


def append_sample_row(sample_list_path: str, sample_id: str, r1_list: List[str], r2_list: List[str]) -> None:
    # Join lists into comma-separated values with no spaces
    r1_field = ",".join(r1_list) if r1_list else "NA"
    r2_field = ",".join(r2_list) if r2_list else "NA"
    with open(sample_list_path, "a", encoding="utf-8") as out:
        out.write(f"{sample_id}\t{r1_field}\t{r2_field}\n")


def process_directory(directory: str) -> Optional[int]:
    csv_path = os.path.join(directory, "bam_disrepancies.csv")
    if not os.path.isfile(csv_path):
        return None
    missing_samples = read_bam_discrepancies(csv_path)
    if not missing_samples:
        return 0

    sample_list_path = os.path.join(directory, "sample_list.txt")
    existing_ids = read_existing_sample_ids(sample_list_path)

    ensure_sample_list(sample_list_path)

    added = 0
    for sid in missing_samples:
        if sid in existing_ids:
            continue
        log_path = find_star_log_for_sample(directory, sid)
        if not log_path:
            print(f"WARNING: No STAR log found for {sid} in {directory}; skipping")
            continue
        r1_list, r2_list = parse_read_files_in_from_log(log_path)
        if not r1_list:
            print(f"WARNING: Could not parse reads for {sid} from {os.path.basename(log_path)}; skipping")
            continue
        append_sample_row(sample_list_path, sid, r1_list, r2_list)
        added += 1
    return added


def main(root: str) -> int:
    total_dirs = 0
    total_added = 0
    for cur_dir, subdirs, files in os.walk(root):
        # Speed: skip hidden dirs
        subdirs[:] = [d for d in subdirs if not d.startswith('.')]
        result = process_directory(cur_dir)
        if result is None:
            continue
        total_dirs += 1
        total_added += int(result)
        print(f"Updated {cur_dir}: added {int(result)} samples")
    print(f"Done. Directories updated: {total_dirs}; total samples added: {total_added}")
    return 0


if __name__ == "__main__":
    root_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    sys.exit(main(root_dir))
