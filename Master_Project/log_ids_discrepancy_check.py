#!/usr/bin/env python3
import os
import re
import sys
import csv
from typing import Dict, Iterable, List, Optional, Set, Tuple

ID_PATTERN = re.compile(r"\b(SRR\d{6,}|ERR\d{6,}|DRR\d{6,}|SAMN\d{6,}|SAMEA\d{6,}|SAMD\d{6,}|GSM\d{6,})\b")
FASTQ_ID_PATTERN = re.compile(r"\b(SRR\d{6,}|ERR\d{6,}|DRR\d{6,})")

LOG_FILE_SUFFIXES = (".log", ".out", ".err", ".txt")
STAR_LOG_GLOBS = ("_Log.out", "_Log.progress.out")


def find_candidate_log_files(directory: str) -> List[str]:
    candidates: List[str] = []
    # logs/ subdir
    logs_dir = os.path.join(directory, "logs")
    if os.path.isdir(logs_dir):
        for root, subdirs, files in os.walk(logs_dir):
            # avoid hidden subdirs
            subdirs[:] = [d for d in subdirs if not d.startswith('.')]
            for fn in files:
                if fn.startswith('.'):
                    continue
                if fn.lower().endswith(LOG_FILE_SUFFIXES):
                    candidates.append(os.path.join(root, fn))
    # top-level STAR logs
    try:
        for fn in os.listdir(directory):
            for suf in STAR_LOG_GLOBS:
                if fn.endswith(suf):
                    candidates.append(os.path.join(directory, fn))
                    break
    except FileNotFoundError:
        pass
    return candidates


def extract_ids_from_files(files: Iterable[str]) -> Set[str]:
    found: Set[str] = set()
    for path in files:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    # Skip comment lines to avoid matching example IDs in documentation
                    if line.lstrip().startswith('#'):
                        continue
                    for m in ID_PATTERN.findall(line):
                        found.add(m)
        except Exception:
            continue
    return found


def parse_sample_list(sample_list_path: str) -> Tuple[Set[str], Set[str]]:
    biosample_ids: Set[str] = set()
    run_ids: Set[str] = set()
    try:
        with open(sample_list_path, "r", encoding="utf-8", errors="ignore") as fh:
            for raw in fh:
                s = raw.strip()
                if not s or s.startswith('#'):
                    continue
                parts = s.split("\t")
                if len(parts) < 1:
                    continue
                biosample = parts[0].strip()
                if biosample:
                    biosample_ids.add(biosample)
                # R1 and R2 columns
                if len(parts) >= 2:
                    for token in (parts[1] or '').split(','):
                        base = os.path.basename(token.strip())
                        m = FASTQ_ID_PATTERN.search(base)
                        if m:
                            run_ids.add(m.group(1))
                if len(parts) >= 3:
                    for token in (parts[2] or '').split(','):
                        base = os.path.basename(token.strip())
                        m = FASTQ_ID_PATTERN.search(base)
                        if m:
                            run_ids.add(m.group(1))
    except FileNotFoundError:
        pass
    return biosample_ids, run_ids


def compare_ids(directory: str) -> Optional[str]:
    sample_list_path = os.path.join(directory, "sample_list.txt")
    log_files = find_candidate_log_files(directory)
    if not log_files:
        return None

    log_ids = extract_ids_from_files(log_files)
    if not log_ids:
        return None

    biosample_ids, run_ids = parse_sample_list(sample_list_path)

    # Determine presence
    rows: List[List[str]] = []
    missing_count = 0
    for idv in sorted(log_ids):
        id_type = (
            "SRR" if idv.startswith("SRR") else
            "ERR" if idv.startswith("ERR") else
            "DRR" if idv.startswith("DRR") else
            "SAMN" if idv.startswith("SAMN") else
            "SAMEA" if idv.startswith("SAMEA") else
            "SAMD" if idv.startswith("SAMD") else
            "GSM" if idv.startswith("GSM") else
            "OTHER"
        )
        in_sample = False
        location = "none"
        if id_type in {"SAMN", "SAMEA", "SAMD"}:
            in_sample = idv in biosample_ids
            location = "first_column" if in_sample else "none"
        elif id_type in {"SRR", "ERR", "DRR"}:
            in_sample = idv in run_ids
            location = "R1_or_R2" if in_sample else "none"
        else:
            in_sample = False
            location = "n/a"
        mismatch = not in_sample
        if mismatch:
            missing_count += 1
        rows.append([idv, id_type, "True", str(in_sample), location, str(mismatch)])

    if missing_count == 0:
        return None

    out_path = os.path.join(directory, "disrepancy_2.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "id_type", "in_logs", "in_sample_list", "location", "mismatch"])
        w.writerows(rows)
    return out_path


def main(root: str) -> int:
    wrote = 0
    for dirpath, dirnames, filenames in os.walk(root):
        # prune heavy dirs minimally
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        result = compare_ids(dirpath)
        if result:
            wrote += 1
            print(f"Wrote: {result}")
    print(f"Completed. Directories with discrepancies: {wrote}")
    return 0


if __name__ == "__main__":
    root_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    sys.exit(main(root_dir))
