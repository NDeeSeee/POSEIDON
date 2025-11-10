#!/usr/bin/env python3
import os
import re
import sys
import csv
import argparse
import subprocess
from typing import Dict, List, Optional, Set, Tuple

RUN_ID_RE = re.compile(r"\b(SRR\d{6,}|ERR\d{6,}|DRR\d{6,})\b")
SAMPLE_FROM_LOG_RE = re.compile(r"(.+)_Log\.out$")


def parse_star_logs_for_mapping(cohort_dir: str) -> Dict[str, str]:
    """Return mapping run_id -> sample_id by scanning *_Log.out files and readFilesIn lines."""
    mapping: Dict[str, str] = {}
    candidates: List[str] = []
    # top-level STAR logs
    try:
        for fn in os.listdir(cohort_dir):
            if fn.endswith("_Log.out"):
                candidates.append(os.path.join(cohort_dir, fn))
    except FileNotFoundError:
        pass
    # logs/ directory STAR logs
    logs_dir = os.path.join(cohort_dir, "logs")
    if os.path.isdir(logs_dir):
        for root, subdirs, files in os.walk(logs_dir):
            subdirs[:] = [d for d in subdirs if not d.startswith('.')]
            for fn in files:
                if fn.endswith("_Log.out"):
                    candidates.append(os.path.join(root, fn))
    for path in candidates:
        m = SAMPLE_FROM_LOG_RE.search(path)
        if not m:
            continue
        sample_id = os.path.basename(path).replace("_Log.out", "")
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    # Skip comment lines to avoid matching example IDs in documentation
                    if line.lstrip().startswith('#'):
                        continue
                    if "readFilesIn" in line:
                        for run in RUN_ID_RE.findall(line):
                            mapping.setdefault(run, sample_id)
        except Exception:
            continue
    return mapping


def ena_biosample_for_run(run_id: str, timeout_s: int = 6) -> Optional[str]:
    try:
        import urllib.request as urlreq
        import urllib.error as urlerr
        url = (
            "https://www.ebi.ac.uk/ena/portal/api/filereport?"
            f"accession={run_id}&result=read_run&fields=run_accession,biosample_accession&format=tsv"
        )
        with urlreq.urlopen(url, timeout=timeout_s) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
        lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
        if len(lines) >= 2:
            header = lines[0].split("\t")
            row = lines[1].split("\t")
            if "biosample_accession" in header:
                idx = header.index("biosample_accession")
                bs = row[idx].strip()
                if bs:
                    return bs
    except Exception:
        return None
    return None


def edirect_biosample_for_run(run_id: str, timeout_s: int = 10) -> Optional[str]:
    try:
        cmd = f'esearch -db sra -query "{run_id}" | efetch -format runinfo'
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout_s)
        if proc.returncode != 0 or not proc.stdout:
            return None
        reader = csv.DictReader(proc.stdout.splitlines())
        for row in reader:
            if (row.get("Run") or "").strip() == run_id:
                bs = (row.get("BioSample") or "").strip()
                if bs:
                    return bs
        # fallback first row
        rows = list(csv.DictReader(proc.stdout.splitlines()))
        if rows:
            bs = (rows[0].get("BioSample") or "").strip()
            if bs:
                return bs
    except Exception:
        return None
    return None


def load_disrepancy_rows(path: str) -> List[str]:
    runs: List[str] = []
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if (row.get("mismatch") or "").strip().lower() != "true":
                continue
            idv = (row.get("id") or "").strip()
            id_type = (row.get("id_type") or "").strip().upper()
            if not idv:
                continue
            if id_type in {"SRR", "ERR", "DRR"}:
                runs.append(idv)
    return runs


def enrich_cohort(cohort_dir: str) -> Optional[str]:
    # Determine input discrepancy file
    in_path = None
    spec_path = os.path.join(cohort_dir, "logs", "discrepancy_2.csv")
    if os.path.isfile(spec_path):
        # If already spec format with sample_id, skip
        with open(spec_path, "r", encoding="utf-8", errors="ignore") as fh:
            header = fh.readline().lower()
            if "sample_id" in header:
                return None
        in_path = spec_path
    else:
        alt = os.path.join(cohort_dir, "disrepancy_2.csv")
        if os.path.isfile(alt):
            in_path = alt
        else:
            return None

    runs = load_disrepancy_rows(in_path)
    if not runs:
        return None

    # Build run->sample mapping from logs
    r2s_map = parse_star_logs_for_mapping(cohort_dir)

    # Resolve missing via ENA/Entrez
    for run in list(runs):
        if run in r2s_map:
            continue
        bs = ena_biosample_for_run(run)
        if not bs:
            bs = edirect_biosample_for_run(run)
        if bs:
            r2s_map[run] = bs

    if not r2s_map:
        return None

    # Aggregate per sample
    sample_to_runs: Dict[str, Set[str]] = {}
    for run in runs:
        sid = r2s_map.get(run)
        if not sid:
            continue
        sample_to_runs.setdefault(sid, set()).add(run)

    if not sample_to_runs:
        return None

    # Prepare output rows
    out_rows: List[Tuple[str, str, str, str]] = []
    for sid in sorted(sample_to_runs.keys()):
        run_ids = sorted(sample_to_runs[sid])
        r1_list = [f"{r}_1.fastq.gz" for r in run_ids]
        r2_list = []
        for r in run_ids:
            r2_candidate = f"{r}_2.fastq.gz"
            if os.path.isfile(os.path.join(cohort_dir, r2_candidate)):
                r2_list.append(r2_candidate)
        out_rows.append((sid, ",".join(run_ids), ",".join(r1_list), ",".join(r2_list) if r2_list else "NA"))

    # Write to disrepancy_2_mapped.csv in same directory as input
    in_dir = os.path.dirname(in_path) if os.path.dirname(in_path) else cohort_dir
    out_path = os.path.join(in_dir, "disrepancy_2_mapped.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sample_id", "srr_ids", "r1_list", "r2_list"])
        w.writerows(out_rows)
    return out_path


def discover_cohorts(root: str) -> List[str]:
    cohorts: List[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        if os.path.isfile(os.path.join(dirpath, "disrepancy_2.csv")) or os.path.isfile(
            os.path.join(dirpath, "logs", "discrepancy_2.csv")
        ):
            cohorts.append(dirpath)
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
    return cohorts


def main():
    ap = argparse.ArgumentParser(description="Enrich discrepancy_2 files with sample_id and SRR mapping (logs + ENA/Entrez)")
    ap.add_argument("root", nargs="?", default=os.getcwd(), help="Root directory or cohort directory")
    args = ap.parse_args()
    root = os.path.abspath(args.root)

    if os.path.isfile(os.path.join(root, "disrepancy_2.csv")) or os.path.isfile(os.path.join(root, "logs", "discrepancy_2.csv")):
        cohorts = [root]
    else:
        cohorts = discover_cohorts(root)

    written = 0
    for c in sorted(set(cohorts)):
        out = enrich_cohort(c)
        if out:
            written += 1
            print(f"Wrote: {out}")
    print(f"Completed. Cohorts enriched: {written}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
