#!/usr/bin/env python3
import os
import sys
import csv
import argparse
import hashlib
from datetime import datetime, timezone
from typing import Iterator, Optional, List

# Notes:
# - On Linux, os.stat().st_ctime is metadata change time, not true creation time.
#   We emit both mtime and ctime in ISO-8601 UTC for clarity.


def iso_utc(ts: float) -> str:
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return ""


def hash_file(path: str, algo: str = "sha256", chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.new(algo)
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""


def iter_paths(root: str, follow_symlinks: bool = False) -> Iterator[os.DirEntry]:
    stack: List[str] = [root]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as it:
                entries = list(it)
        except PermissionError:
            continue
        except FileNotFoundError:
            continue
        # Sort for stable output: directories first, then files by name
        entries.sort(key=lambda e: (not e.is_dir(follow_symlinks=follow_symlinks), e.name.lower()))
        for entry in entries:
            yield entry
            if entry.is_dir(follow_symlinks=follow_symlinks):
                stack.append(entry.path)


def snapshot(root: str, out_csv: Optional[str], pretty_txt: Optional[str], do_hash: bool, follow_symlinks: bool) -> int:
    root = os.path.abspath(root)
    rows = []
    # CSV header
    header = [
        "path_relative",
        "type",
        "size_bytes",
        "mtime_utc",
        "ctime_utc",
        "hash_sha256" if do_hash else None,
    ]
    header = [h for h in header if h is not None]

    # Optionally write a simple tree preview as we go
    tree_lines: List[str] = []
    prefix_root = os.path.basename(root)
    tree_lines.append(prefix_root)

    for entry in iter_paths(root, follow_symlinks=follow_symlinks):
        try:
            st = entry.stat(follow_symlinks=follow_symlinks)
        except Exception:
            # Unreadable; record minimal info
            st = None
        rel_path = os.path.relpath(entry.path, root)
        if rel_path == ".":
            rel_path = os.path.basename(root)
        kind = "dir" if (st and os.path.isdir(entry.path)) or entry.is_dir(follow_symlinks=follow_symlinks) else ("file" if (st and os.path.isfile(entry.path)) or entry.is_file(follow_symlinks=follow_symlinks) else "other")
        size = 0
        if kind == "file" and st is not None:
            size = int(getattr(st, "st_size", 0))
        mtime = iso_utc(getattr(st, "st_mtime", 0.0)) if st else ""
        ctime = iso_utc(getattr(st, "st_ctime", 0.0)) if st else ""
        digest = hash_file(entry.path) if (do_hash and kind == "file") else None

        row = [rel_path, kind, str(size), mtime, ctime]
        if do_hash:
            row.append(digest or "")
        rows.append(row)

        if pretty_txt is not None:
            # Compose indentation based on depth
            depth = rel_path.count(os.sep)
            indent = "  " * depth
            human = f"{indent}{entry.name}"
            if kind == "file":
                human += f"  ({size} B)"
            tree_lines.append(human)

    # Write CSV
    if out_csv:
        os.makedirs(os.path.dirname(os.path.abspath(out_csv)), exist_ok=True)
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)
    else:
        w = csv.writer(sys.stdout)
        w.writerow(header)
        w.writerows(rows)

    # Write pretty tree if requested
    if pretty_txt:
        os.makedirs(os.path.dirname(os.path.abspath(pretty_txt)), exist_ok=True)
        with open(pretty_txt, "w", encoding="utf-8") as f:
            f.write("\n".join(tree_lines) + "\n")

    return 0


def main():
    p = argparse.ArgumentParser(description="Snapshot a directory tree (path, type, size, times[, hash])")
    p.add_argument("root", nargs="?", default=os.getcwd(), help="Root directory to snapshot")
    p.add_argument("-o", "--out", dest="out_csv", default=None, help="Output CSV path (default: stdout)")
    p.add_argument("--pretty", dest="pretty_txt", default=None, help="Optional pretty tree output path (.txt)")
    p.add_argument("--hash", dest="do_hash", action="store_true", help="Compute SHA-256 for files (slower)")
    p.add_argument("--follow-symlinks", action="store_true", help="Follow symlinks during traversal")
    args = p.parse_args()

    return snapshot(args.root, args.out_csv, args.pretty_txt, args.do_hash, args.follow_symlinks)


if __name__ == "__main__":
    sys.exit(main())
