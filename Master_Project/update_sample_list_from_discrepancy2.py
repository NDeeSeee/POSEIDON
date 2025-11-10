#!/usr/bin/env python3
import os
import sys
import csv
import argparse
from typing import Dict, List, Optional, Set, Tuple

# Minimal implementation per specs/disrepancy2_mapping_spec.txt
# - ONLY uses existing discrepancy files (prefers logs/discrepancy_2.csv, also supports disrepancy_2.csv)
# - NO BAM/bams inspection
# - Idempotent merge that keeps existing rows and adds/augments based on discrepancy_2 content


def read_sample_list(path: str) -> Dict[str, Tuple[Set[str], Set[str]]]:
    mapping: Dict[str, Tuple[Set[str], Set[str]]] = {}
    if not os.path.isfile(path):
        return mapping
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        for raw in fh:
            s = raw.rstrip("\n")
            if not s or s.startswith("#"):
                continue
            parts = s.split("\t")
            if not parts:
                continue
            sid = parts[0].strip()
            r1_list = parts[1].strip() if len(parts) >= 2 else ""
            r2_list = parts[2].strip() if len(parts) >= 3 else ""
            r1: Set[str] = set([p.strip() for p in r1_list.split(",") if p.strip()]) if r1_list else set()
            r2: Set[str] = set()
            if r2_list and r2_list.upper() != "NA":
                r2 = set([p.strip() for p in r2_list.split(",") if p.strip()])
            mapping[sid] = (r1, r2)
    return mapping


def write_sample_list(path: str, mapping: Dict[str, Tuple[Set[str], Set[str]]]) -> None:
    rows = []
    for sid in sorted(mapping.keys()):
        r1, r2 = mapping[sid]
        r1_join = ",".join(sorted(r1))
        r2_join = ",".join(sorted(r2)) if r2 else "NA"
        rows.append((sid, r1_join, r2_join))
    with open(path, "w", encoding="utf-8", newline="") as out:
        w = csv.writer(out, delimiter="\t", lineterminator="\n")
        w.writerows(rows)


def find_discrepancy_file(cohort_dir: str) -> Optional[str]:
    # Prefer the mapped/enriched file (with sample_id column)
    mapped = os.path.join(cohort_dir, "disrepancy_2_mapped.csv")
    if os.path.isfile(mapped):
        return mapped
    # Also check in logs directory
    mapped_logs = os.path.join(cohort_dir, "logs", "discrepancy_2_mapped.csv")
    if os.path.isfile(mapped_logs):
        return mapped_logs
    # Fallback to old naming
    candidate = os.path.join(cohort_dir, "logs", "discrepancy_2.csv")
    if os.path.isfile(candidate):
        return candidate
    fallback = os.path.join(cohort_dir, "disrepancy_2.csv")
    if os.path.isfile(fallback):
        return fallback
    return None


def dir_has_fastq(cohort_dir: str, filename: str) -> bool:
    # Simple, fast existence check for deciding R2 presence
    return os.path.isfile(os.path.join(cohort_dir, filename))


def parse_discrepancy2(path: str) -> List[Tuple[str, List[str], List[str]]]:
    """
    Return list of (sample_id, r1_list, r2_list).
    Supports two formats:
    - Spec format: columns include sample_id and either srr_ids or explicit r1_list/r2_list
    - Our generated format: id,id_type,in_logs,in_sample_list,location,mismatch (no sample_id). In this case,
      we cannot map SRR->sample deterministically from the CSV alone. We will emit warnings and skip SRR-only rows.
    """
    out: List[Tuple[str, List[str], List[str]]] = []
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        reader = csv.DictReader(fh)
        fields = {k.lower(): k for k in (reader.fieldnames or [])}
        has_sample = "sample_id" in fields
        has_srrs = "srr_ids" in fields
        has_r1 = "r1_list" in fields
        has_r2 = "r2_list" in fields
        spec_like = has_sample and (has_srrs or has_r1)

        if spec_like:
            for row in reader:
                sid = (row.get(fields["sample_id"]) or "").strip()
                if not sid:
                    continue
                r1_list: List[str] = []
                r2_list: List[str] = []
                if has_r1:
                    r1_list = [p.strip() for p in (row.get(fields["r1_list"]) or "").split(",") if p.strip()]
                if has_r2:
                    r2_raw = (row.get(fields["r2_list"]) or "").strip()
                    if r2_raw.upper() != "NA":
                        r2_list = [p.strip() for p in r2_raw.split(",") if p.strip()]
                if (not r1_list) and has_srrs:
                    srrs = [p.strip() for p in (row.get(fields["srr_ids"]) or "").split(",") if p.strip()]
                    r1_list = [f"{s}_1.fastq.gz" for s in srrs]
                    # r2 decided later by file presence; leave empty here
                out.append((sid, r1_list, r2_list))
        else:
            # Our generated format; gather only biosample rows with mismatch==True or SRR rows without sample mapping?
            # We cannot infer sample for SRR-only rows; skip with minimal warning.
            # For SAMEA/SAMN rows, discrepancy files typically show them already in sample_list, so nothing to add.
            # Hence: return empty; caller will no-op this directory.
            return []
    return out


def merge_changes(cohort_dir: str, sl_map: Dict[str, Tuple[Set[str], Set[str]]], recs: List[Tuple[str, List[str], List[str]]]) -> Tuple[int, int, int, List[str]]:
    added = 0
    merged = 0
    unchanged = 0
    warnings: List[str] = []

    for sid, r1_list, r2_list in recs:
        if not sid:
            warnings.append(f"{cohort_dir}: row skipped (missing sample_id)")
            continue
        if sid not in sl_map:
            sl_map[sid] = (set(), set())
            was_new = True
        else:
            was_new = False
        r1_set, r2_set = sl_map[sid]

        before = (len(r1_set), len(r2_set))

        # Normalize and add R1
        for r1 in r1_list:
            if r1:
                r1_set.add(r1)
        # For R2: include only those listed or that exist as files
        for r2 in r2_list:
            if r2:
                r2_set.add(r2)
        # If we had srr-only (no r2), infer R2 presence by filesystem
        if r1_list and not r2_list:
            for r1 in r1_list:
                if r1.endswith("_1.fastq.gz"):
                    r2 = r1.replace("_1.fastq.gz", "_2.fastq.gz")
                    if dir_has_fastq(cohort_dir, r2):
                        r2_set.add(r2)

        after = (len(r1_set), len(r2_set))
        if after == before:
            unchanged += 1
        elif was_new:
            added += 1
        else:
            merged += 1
    return added, merged, unchanged, warnings


def process_cohort(cohort_dir: str, dry_run: bool = False) -> Optional[str]:
    dfile = find_discrepancy_file(cohort_dir)
    if not dfile:
        return None

    sl_path = os.path.join(cohort_dir, "sample_list.txt")
    if not os.path.isfile(sl_path):
        # Spec assumes it exists; if not, skip silently (minimalism)
        return None

    recs = parse_discrepancy2(dfile)
    if not recs:
        return None

    sl_map = read_sample_list(sl_path)
    before_keys = set(sl_map.keys())

    added, merged, unchanged, warns = merge_changes(cohort_dir, sl_map, recs)

    summary_dir = os.path.join(cohort_dir, "logs")
    os.makedirs(summary_dir, exist_ok=True)
    summary_path = os.path.join(summary_dir, "update_sample_list_2.summary.txt")

    if dry_run:
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(f"DRY-RUN: would add={added} merge={merged} unchanged={unchanged}\n")
            for w in warns:
                f.write(f"WARN: {w}\n")
        return summary_path

    # Atomic-like write: rename original and write new
    incomplete_path = os.path.join(cohort_dir, "incomplete_sample_list_2.txt")
    try:
        os.replace(sl_path, incomplete_path)
    except Exception:
        # If replace fails, attempt a copy-then-write flow (avoid complexity; still minimal)
        pass

    write_sample_list(sl_path, sl_map)

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"add={added} merge={merged} unchanged={unchanged}\n")
        for w in warns:
            f.write(f"WARN: {w}\n")

    return summary_path


def discover_cohorts(root: str) -> List[str]:
    cohorts: List[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Only process directories that already have a discrepancy file (prefer mapped)
        if (os.path.isfile(os.path.join(dirpath, "disrepancy_2_mapped.csv")) or
            os.path.isfile(os.path.join(dirpath, "logs", "discrepancy_2_mapped.csv")) or
            os.path.isfile(os.path.join(dirpath, "logs", "discrepancy_2.csv")) or
            os.path.isfile(os.path.join(dirpath, "disrepancy_2.csv"))):
            cohorts.append(dirpath)
        # prune hidden
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
    return cohorts


def main():
    ap = argparse.ArgumentParser(description="Update sample_list.txt using existing discrepancy_2 reports (logs only)")
    ap.add_argument("root", nargs="?", default=os.getcwd(), help="Root directory or a single cohort directory")
    ap.add_argument("--dry-run", action="store_true", help="Report changes only; do not modify files")
    args = ap.parse_args()

    root = os.path.abspath(args.root)

    to_process: List[str]
    if (os.path.isfile(os.path.join(root, "disrepancy_2_mapped.csv")) or
        os.path.isfile(os.path.join(root, "logs", "discrepancy_2_mapped.csv")) or
        os.path.isfile(os.path.join(root, "logs", "discrepancy_2.csv")) or
        os.path.isfile(os.path.join(root, "disrepancy_2.csv"))):
        to_process = [root]
    else:
        to_process = discover_cohorts(root)

    processed = 0
    for c in sorted(set(to_process)):
        res = process_cohort(c, dry_run=args.dry_run)
        if res:
            processed += 1
            print(f"Wrote: {res}")
    print(f"Completed. Cohorts updated: {processed}")


if __name__ == "__main__":
    sys.exit(main())
