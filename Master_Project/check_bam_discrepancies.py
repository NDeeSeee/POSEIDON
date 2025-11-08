#!/usr/bin/env python3
import os
import sys
import csv
from typing import List, Set, Tuple, Optional

PREFERRED_SAMPLELIST_NAMES = [
    "sample_list.txt",
    "sample_list.with_status.txt",
]


def find_sample_list_file(directory: str) -> Optional[str]:
    """Return the most appropriate sample list file path in directory."""
    # Prefer exact names
    for name in PREFERRED_SAMPLELIST_NAMES:
        candidate = os.path.join(directory, name)
        if os.path.isfile(candidate):
            return candidate
    # Fallback: any file starting with sample_list and ending with .txt
    try:
        candidates = [f for f in os.listdir(directory) if f.startswith("sample_list") and f.endswith(".txt")]
    except FileNotFoundError:
        return None
    if not candidates:
        return None
    # If there is a with_status present, prefer it
    with_status = [f for f in candidates if f == "sample_list.with_status.txt"]
    if with_status:
        return os.path.join(directory, with_status[0])
    # Otherwise, if only one, use it; else pick lexicographically smallest to be deterministic
    candidates.sort()
    return os.path.join(directory, candidates[0])


def parse_sample_list_ids(path: str) -> Set[str]:
    """Read first column (whitespace-separated) as sample IDs; ignore empty/comment lines."""
    ids: Set[str] = set()
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Split on any whitespace or tab
            parts = line.split()
            if not parts:
                continue
            ids.add(parts[0])
    return ids


def list_bam_files(bam_dir: str) -> List[str]:
    try:
        entries = os.listdir(bam_dir)
    except FileNotFoundError:
        return []
    # Only true BAM files; exclude indices and hidden files
    return [f for f in entries if f.endswith(".bam") and not f.endswith(".bam.bai") and not f.startswith(".")]


def normalize_bam_basename(filename: str) -> str:
    """Return a cleaned sample-like name from a BAM filename (strip extensions and common STAR suffixes)."""
    base = filename
    if base.endswith(".bam"):
        base = base[:-4]
    # Strip common STAR alignment suffixes if present
    star_suffixes = [
        "_Aligned.sortedByCoord.out",
        ".Aligned.sortedByCoord.out",
        "-Aligned.sortedByCoord.out",
    ]
    for suff in star_suffixes:
        if base.endswith(suff):
            base = base[: -len(suff)]
            break
    return base


def map_bam_ids_to_sample_list(bam_ids: Set[str], sample_ids: Set[str]) -> Tuple[Set[str], Set[str]]:
    """
    Attempt to map bam-derived names to sample IDs using exact or prefix matches.
    Returns (mapped_ids_in_sample_list, unmapped_bam_ids_as_is)
    """
    mapped: Set[str] = set()
    unmapped: Set[str] = set()
    if not sample_ids:
        # Nothing to map to
        return set(), set(bam_ids)

    # Pre-compute for speed
    sample_ids_sorted = sorted(sample_ids, key=len, reverse=True)

    for bid in bam_ids:
        if bid in sample_ids:
            mapped.add(bid)
            continue
        # Prefer the longest sample id that is a prefix of the bam id
        best: Optional[str] = None
        for sid in sample_ids_sorted:
            if bid.startswith(sid) or sid.startswith(bid):
                best = sid
                break
        if best is not None:
            mapped.add(best)
        else:
            unmapped.add(bid)
    return mapped, unmapped


def write_discrepancies_csv(target_dir: str, all_ids: List[str], in_bam: Set[str], in_sample: Set[str], out_name: str = "bam_disrepancies.csv") -> None:
    out_path = os.path.join(target_dir, out_name)
    with open(out_path, "w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(["sample_id", "in_bam_dir", "in_sample_list", "mismatch"])
        for sid in all_ids:
            a = sid in in_bam
            b = sid in in_sample
            writer.writerow([sid, str(a), str(b), str(a != b)])


def process_directory(parent_dir: str) -> Optional[str]:
    """If directory contains bams/bams1, compare against sample list and write CSV. Returns path of CSV if written."""
    bam_dirs = []
    for sub in ("bams", "bams1"):
        path = os.path.join(parent_dir, sub)
        if os.path.isdir(path):
            bam_dirs.append(path)
    if not bam_dirs:
        return None

    bam_files: List[str] = []
    for bdir in bam_dirs:
        bam_files.extend(list_bam_files(bdir))

    bam_ids_raw = {normalize_bam_basename(f) for f in bam_files}

    sl_file = find_sample_list_file(parent_dir)
    sample_ids: Set[str] = set()
    if sl_file:
        sample_ids = parse_sample_list_ids(sl_file)

    mapped_ids, unmapped_bam_ids = map_bam_ids_to_sample_list(bam_ids_raw, sample_ids)

    in_bam_ids: Set[str] = set(mapped_ids)
    in_bam_ids.update(unmapped_bam_ids)

    all_ids = sorted(in_bam_ids.union(sample_ids))

    write_discrepancies_csv(parent_dir, all_ids, in_bam_ids, sample_ids)

    return os.path.join(parent_dir, "bam_disrepancies.csv")


def main(root: str) -> int:
    processed = 0
    for cur_dir, subdirs, files in os.walk(root):
        # Skip hidden directories quickly
        subdirs[:] = [d for d in subdirs if not d.startswith('.')]
        result = process_directory(cur_dir)
        if result:
            processed += 1
            # Optional: print progress
            print(f"Wrote: {result}")
    print(f"Completed. Directories processed: {processed}")
    return 0


if __name__ == "__main__":
    root_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    sys.exit(main(root_dir))
