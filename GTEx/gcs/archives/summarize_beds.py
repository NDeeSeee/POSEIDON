#!/usr/bin/env python3
import os
import sys
import glob
from typing import Dict, List, Tuple


def extract_sample_name(bed_path: str) -> str:
    # Get last path component and trim at first occurrence of '.Aligned'
    basename = bed_path.rsplit('/', 1)[-1]
    if '.Aligned' in basename:
        return basename.split('.Aligned', 1)[0]
    # Fallback: drop extension
    return basename.rsplit('.', 1)[0]


def summarize_beds_file(file_path: str) -> Tuple[int, int, List[str], Dict[str, int]]:
    sample_to_count: Dict[str, int] = {}
    with open(file_path, 'r') as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            sample = extract_sample_name(line)
            sample_to_count[sample] = sample_to_count.get(sample, 0) + 1

    num_with_two = sum(1 for c in sample_to_count.values() if c == 2)
    num_with_one = sum(1 for c in sample_to_count.values() if c == 1)
    only_once = sorted([s for s, c in sample_to_count.items() if c == 1])
    return num_with_two, num_with_one, only_once, sample_to_count


def find_beds_txt_files(root: str) -> List[str]:
    pattern = os.path.join(root, '**', '*.beds.txt')
    return sorted(glob.glob(pattern, recursive=True))


def main() -> None:
    root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    files = find_beds_txt_files(root)
    if not files:
        print(f'No .beds.txt files found under {root}')
        sys.exit(1)

    for fp in files:
        num_two, num_one, only_once, counts = summarize_beds_file(fp)
        print(f'File: {fp}')
        print(f'  samples_with_2_lines: {num_two}')
        print(f'  samples_with_1_line:  {num_one}')
        if only_once:
            print('  only_once_samples:')
            for s in only_once:
                print(f'    {s}')
        else:
            print('  only_once_samples: (none)')
        # If any anomalies exist (counts not 1 or 2), report briefly
        anomalies = sorted([s for s, c in counts.items() if c not in (1, 2)])
        if anomalies:
            print('  anomalies_counts_not_1_or_2:')
            for s in anomalies:
                print(f'    {s}: {counts[s]}')
        print()


if __name__ == '__main__':
    main()
