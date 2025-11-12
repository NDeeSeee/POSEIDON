#!/usr/bin/env python3
import os
from typing import Dict, List, Tuple

LOCAL_ROOT = "/data/salomonis-archive/FASTQs/NCI-R01/POSEIDON/GTEx/gcs/archives"
REMOTE_ROOT = "/users/pavb5f/gcs/fc-secure-1b3e77a1-94a0-4e56-9ffd-342eca7e1cbe/archives"


def list_tgz(root: str) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for tissue in sorted([d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))]):
        tdir = os.path.join(root, tissue)
        for name in os.listdir(tdir):
            if name.endswith('.beds.tgz') or name.endswith('.tgz'):
                result[name] = os.path.join(tdir, name)
    return result


def main() -> None:
    remote = list_tgz(REMOTE_ROOT)
    local = list_tgz(LOCAL_ROOT)

    missing_locally: List[Tuple[str, str]] = []
    for name, rpath in sorted(remote.items()):
        if name not in local:
            missing_locally.append((name, rpath))

    print(f"Remote archives: {len(remote)}")
    print(f"Local archives:  {len(local)}")
    print(f"Missing locally:  {len(missing_locally)}")
    for name, rpath in missing_locally:
        print(f"  {name} -> {rpath}")


if __name__ == "__main__":
    main()
