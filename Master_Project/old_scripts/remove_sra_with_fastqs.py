#!/usr/bin/env python3
import argparse
import os
import sys
from typing import List, Tuple

ROOT = "/data/salomonis-archive/FASTQs/NCI-R01/POSEIDON"


def find_sample_dirs(root: str) -> List[str]:
    sample_dirs: List[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        if "sample_list.txt" in filenames:
            sample_dirs.append(dirpath)
    return sample_dirs


def paired_fastqs_exist(dir_path: str, srr: str) -> bool:
    r1 = os.path.join(dir_path, f"{srr}_1.fastq.gz")
    r2 = os.path.join(dir_path, f"{srr}_2.fastq.gz")
    return os.path.isfile(r1) and os.path.isfile(r2)


def list_sra_files(dir_path: str) -> List[str]:
    try:
        return [f for f in os.listdir(dir_path) if f.endswith('.sra') and os.path.isfile(os.path.join(dir_path, f))]
    except FileNotFoundError:
        return []


def remove_prefetch_dir_if_empty(dir_path: str, srr: str, dry_run: bool) -> Tuple[bool, str]:
    prefetch_dir = os.path.join(dir_path, srr)
    if not os.path.isdir(prefetch_dir):
        return False, ""
    try:
        entries = os.listdir(prefetch_dir)
    except OSError:
        return False, ""
    # If empty, remove
    if not entries:
        if dry_run:
            return True, f"DRY-RUN rm -r {prefetch_dir}"
        os.rmdir(prefetch_dir)
        return True, f"Removed empty {prefetch_dir}"
    # If only contains a same-named .sra (rare in this layout), consider remove after deleting .sra in parent
    if len(entries) == 1 and entries[0].endswith('.sra'):
        try:
            if dry_run:
                return True, f"DRY-RUN rm -r {prefetch_dir}"
            os.remove(os.path.join(prefetch_dir, entries[0]))
            os.rmdir(prefetch_dir)
            return True, f"Removed {prefetch_dir} with single SRA"
        except OSError:
            return False, ""
    return False, ""


def main() -> None:
    parser = argparse.ArgumentParser(description="Delete .sra files when corresponding paired FASTQs exist (space cleanup)")
    parser.add_argument("--root", default=ROOT, help="Project root to scan (default: repo root)")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without deleting files")
    parser.add_argument("--remove-prefetch-dirs", action="store_true", help="Also remove empty SRR/ prefetch directories if safe")
    args = parser.parse_args()

    sample_dirs = find_sample_dirs(args.root)
    total_deleted = 0
    total_dirs_removed = 0

    for d in sorted(sample_dirs):
        sras = list_sra_files(d)
        if not sras:
            continue
        for sra_name in sras:
            srr = sra_name[:-4]  # strip .sra
            if paired_fastqs_exist(d, srr):
                sra_path = os.path.join(d, sra_name)
                if args.dry_run:
                    print(f"DRY-RUN rm {sra_path}")
                else:
                    try:
                        os.remove(sra_path)
                        print(f"Removed {sra_path}")
                        total_deleted += 1
                    except OSError as e:
                        print(f"WARN: failed to remove {sra_path}: {e}", file=sys.stderr)
                if args.remove_prefetch_dirs:
                    removed, msg = remove_prefetch_dir_if_empty(d, srr, args.dry_run)
                    if msg:
                        print(msg)
                    if removed and not args.dry_run:
                        total_dirs_removed += 1

    print(f"Summary: deleted {total_deleted} .sra files; removed {total_dirs_removed} prefetch dirs")

if __name__ == "__main__":
    main()
