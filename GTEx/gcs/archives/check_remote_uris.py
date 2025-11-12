#!/usr/bin/env python3
import os
import sys
import glob
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple


def list_beds_txt(root: str) -> List[str]:
    return sorted(glob.glob(os.path.join(root, '*', '*.beds.txt')))


def count_missing(uris: List[str], max_workers: int = 32) -> Tuple[int, List[str]]:
    missing = []
    def check(uri: str) -> Tuple[str, bool]:
        if not uri:
            return uri, True
        r = subprocess.run(['gsutil', '-q', 'stat', uri], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return uri, (r.returncode != 0)

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(check, u): u for u in uris}
        for fut in as_completed(futs):
            uri, is_missing = fut.result()
            if is_missing:
                missing.append(uri)
    return len(missing), missing


def main() -> None:
    root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    files = list_beds_txt(root)
    if not files:
        print(f'No .beds.txt under {root}', file=sys.stderr)
        sys.exit(1)

    for fp in files:
        with open(fp) as fh:
            uris = [ln.strip() for ln in fh if ln.strip()]
        total = len(uris)
        miss_n, missing_list = count_missing(uris)
        print(f'{fp}: {total - miss_n}/{total} present, {miss_n} missing')
        if miss_n > 0:
            for u in missing_list[:10]:
                print(f'  MISSING: {u}')
            if miss_n > 10:
                print(f'  ... and {miss_n - 10} more missing')


if __name__ == '__main__':
    main()
