#!/usr/bin/env python3
"""
POSEIDON FASTQ – Core Rewrite (minimal, maintainable)

Goal: drastically smaller, testable core that preserves essential behavior:
  • Parse sample_list.txt → sample_id → [SRR/ERR...]
  • Inventory filesystem → decide what to DO (plan) per SRR
  • Apply the plan: prefetch missing .sra, submit fastq‑dump jobs via LSF
  • Generate sample_list.with_status.txt snapshot (same 4‑column contract)
  • Safe cleanup of converted .sra once FASTQs exist (>0B)

Non‑goals for the core (moved out / optional extensions):
  – Deep gzip integrity scans / long timeouts
  – lsof/pgrep heuristics
  – STAR progress detection
  – Complex stuck‑job detection
  – Special bams1/legacy edge cases

Subcommands
  poseidon_core.py plan   <cancer_dir>         # print action plan
  poseidon_core.py apply  <cancer_dir>         # execute plan (download/submit)
  poseidon_core.py status <cancer_dir>         # write sample_list.with_status.txt
  poseidon_core.py clean  <cancer_dir>         # delete .sra with completed FASTQs

Dependencies expected in PATH on HPC: prefetch, fastq-dump (or fasterq-dump), bsub, bjobs

Design notes
  – Stateless “inventory()” + pure “plan_actions()” gives idempotent behavior and easy tests
  – Minimal validation: file existence/size + small FASTQ header sniff
  – Job submission uses a standard job name: fastq_<SRR>
  – You can swap the submit command with your bash wrapper if desired
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import shutil

# ----------------------------
# Types
# ----------------------------
@dataclass
class SRRInfo:
    srr: str
    sra: Optional[Path]
    r1: Optional[Path]
    r2: Optional[Path]
    r1_ok: bool
    r2_ok: bool
    sra_ok: bool

@dataclass
class Action:
    kind: str  # "download" | "convert"
    srr: str
    detail: str
    sra_path: Optional[Path] = None

# ----------------------------
# Parsing & inventory
# ----------------------------
# Accept SRR/ERR IDs even when followed by underscores or extensions
SRR_RE = re.compile(r"(SRR\d+|ERR\d+)")


def parse_sample_list(sample_list_path: Path) -> Dict[str, List[str]]:
    """Return mapping sample_id -> unique list of SRR/ERR IDs."""
    m: Dict[str, List[str]] = {}
    if not sample_list_path.exists():
        raise FileNotFoundError(f"Missing {sample_list_path}")
    with sample_list_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = [p for p in re.split(r"\t|\s+", line) if p]
            if len(parts) < 3:
                # keep permissive; skip if we cannot find IDs
                continue
            sample = parts[0]
            ids = set(SRR_RE.findall(",".join(parts[1:3])))
            if not ids:
                continue
            m[sample] = sorted(ids)
    if not m:
        raise ValueError("No valid samples with SRR/ERR IDs found.")
    return m


def _exists_nonempty(p: Optional[Path]) -> bool:
    if not p:
        return False
    try:
        return p.exists() and p.stat().st_size > 0
    except OSError:
        return False


def _fastq_header_ok(p: Path, n_lines: int = 8) -> bool:
    """Quick FASTQ sanity check – read a few lines and verify '@'/'+' pattern."""
    try:
        with gzip.open(p, "rt") as fh:
            lines = []
            for _ in range(n_lines):
                s = fh.readline()
                if not s:
                    break
                lines.append(s)
        if len(lines) < 4:
            return False
        # Check first record pattern
        return lines[0].startswith("@") and "+" in "".join(lines[:4])
    except Exception:
        return False


def _find_sra(cancer_dir: Path, srr: str) -> Optional[Path]:
    for ext in (".sra", ".sralite"):
        p = cancer_dir / f"{srr}{ext}"
        if p.exists():
            return p
    return None


def inventory(cancer_dir: Path, srrs: List[str]) -> Dict[str, SRRInfo]:
    """Scan filesystem for each SRR and return a compact status structure."""
    out: Dict[str, SRRInfo] = {}
    for srr in srrs:
        r1 = cancer_dir / f"{srr}_1.fastq.gz"
        r2 = cancer_dir / f"{srr}_2.fastq.gz"
        sra = _find_sra(cancer_dir, srr)

        r1_ok = _exists_nonempty(r1) and _fastq_header_ok(r1)
        r2_ok = _exists_nonempty(r2)
        if r2_ok:
            # light sniff for R2 if present
            r2_ok = _fastq_header_ok(r2)
        sra_ok = _exists_nonempty(sra)

        out[srr] = SRRInfo(srr=srr, sra=sra, r1=r1 if r1.exists() else None,
                           r2=r2 if r2.exists() else None, r1_ok=r1_ok, r2_ok=r2_ok, sra_ok=sra_ok)
    return out

# ----------------------------
# Planning
# ----------------------------

def plan_actions(inv: Dict[str, SRRInfo]) -> List[Action]:
    """Derive a minimal plan: download if no SRA; convert if SRA ok and FASTQ incomplete."""
    actions: List[Action] = []
    for srr, info in inv.items():
        fastq_done = info.r1_ok and (info.r2 is None or info.r2_ok)
        if fastq_done:
            continue
        if not info.sra_ok:
            actions.append(Action(kind="download", srr=srr, detail="prefetch"))
        else:
            actions.append(Action(kind="convert", srr=srr, detail="fastq-dump", sra_path=info.sra))
    return actions

# ----------------------------
# Executors
# ----------------------------

def run(cmd: List[str], cwd: Optional[Path] = None, capture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=False,
                          text=True, capture_output=capture)


def prefetch(cancer_dir: Path, srr: str) -> bool:
    # -X cap keeps downloads bounded similar to legacy script; adjust if needed
    cp = run(["prefetch", srr, "-X", "35000000"], cwd=cancer_dir, capture=True)
    if cp.returncode != 0:
        return False
    # move out of SRR/ subdir if created
    sub = cancer_dir / srr
    if sub.is_dir():
        for p in sub.glob("*.sra*"):
            target = cancer_dir / p.name
            if not target.exists():
                try:
                    p.rename(target)
                except Exception:
                    pass
        try:
            if not any(sub.iterdir()):
                sub.rmdir()
        except Exception:
            pass
    got = _find_sra(cancer_dir, srr)
    return bool(got and _exists_nonempty(got))


JOB_RE = re.compile(r"Job\s*<(?P<id>\d+)>", re.I)


def submit_fastq_dump(cancer_dir: Path, srr: str) -> Optional[str]:
    """Submit an LSF job that uses fasterq-dump + pigz for speed (by SRR ID).

    This version embeds absolute paths to the tools resolved at submit time so that
    jobs launched under LSF see the correct binaries even without re-activating conda.
    """
    job_name = f"fastq_{srr}"
    threads = int(os.environ.get("FQD_THREADS", "4"))

    # Resolve absolute binaries from the current environment (e.g., your conda env)
    fqd_bin = shutil.which("fasterq-dump") or "fasterq-dump"
    pigz_bin = shutil.which("pigz")  # may be None
    gzip_bin = shutil.which("gzip") or "gzip"

    # Warn if compression tools are unavailable
    if not pigz_bin and not shutil.which("gzip"):
        print(f"WARNING: Neither pigz nor gzip found in PATH. Compression may fail for {srr}")

    # Prepare safely-quoted binaries/args for bash body construction
    pigz_nonempty_arg = shlex.quote(pigz_bin or "")
    pigz_executable_arg = shlex.quote(pigz_bin or "/bin/false")
    cmp_if_pigz = shlex.quote(pigz_bin or gzip_bin)
    cmp_else_gzip = shlex.quote(gzip_bin)

    # Build a safe bash body; we pass SRR accession (not filename) to ensure proper output names
    # Use --temp to keep fasterq-dump scratch local to the chosen TMPD
    bash_body = " ".join([
        "set -euo pipefail;",
        f"cd {shlex.quote(str(cancer_dir))};",
        "mkdir -p logs || true;",
        f'TMPD="${{LS_TMPDIR:-${{TMPDIR:-/tmp}}}}/fqd_{srr}_$RANDOM";',
        'mkdir -p "$TMPD";',
        f"{shlex.quote(fqd_bin)} --split-files --threads {threads} --temp \"$TMPD\" -O \"$TMPD\" {shlex.quote(srr)};",
        # Choose compressor
        f'if [[ -n {pigz_nonempty_arg} ]] && [[ -x {pigz_executable_arg} ]]; then CMP={cmp_if_pigz}; else CMP={cmp_else_gzip}; fi;',
        f'[[ -f "$TMPD/{srr}_1.fastq" ]] && "$CMP" -p {threads} "$TMPD/{srr}_1.fastq" 2>/dev/null || "$CMP" "$TMPD/{srr}_1.fastq" || true;',
        f'[[ -f "$TMPD/{srr}_2.fastq" ]] && "$CMP" -p {threads} "$TMPD/{srr}_2.fastq" 2>/dev/null || "$CMP" "$TMPD/{srr}_2.fastq" || true;',
        'mv "$TMPD"/*.fastq.gz . || true;',
        'rm -rf "$TMPD";',
        # remove source SRA only if outputs look sane
        f'if [[ -s "{srr}_1.fastq.gz" && ( ! -e "{srr}_2.fastq.gz" || -s "{srr}_2.fastq.gz" ) ]]; then ',
        f'  [[ -f "{srr}.sra" ]] && rm -f "{srr}.sra";',
        f'  [[ -f "{srr}.sralite" ]] && rm -f "{srr}.sralite";',
        'fi;'
    ])

    cmd = [
        "bsub",
        "-J", job_name,
        "-oo", str((cancer_dir / "logs" / f"fastq_{srr}.out.txt")),
        "-eo", str((cancer_dir / "logs" / f"fastq_{srr}.err.txt")),
        "-cwd", str(cancer_dir),
        "-n", str(threads),
        # Uncomment/adjust if your site enforces memory requests
        # "-M", "64000", "-R", f"rusage[mem={64000}] span[hosts=1]",
        "bash", "-lc",
        bash_body
    ]
    cp = run(cmd, capture=True)
    if cp.returncode != 0:
        return None
    m = JOB_RE.search((cp.stdout or "") + (cp.stderr or ""))
    return m.group("id") if m else None


def bjobs_status(job_id: str) -> str:
    cp = run(["bjobs", "-noheader", "-o", "stat", job_id], capture=True)
    if cp.returncode != 0:
        return "UNKNOWN"
    return (cp.stdout or "").strip() or "UNKNOWN"

# ----------------------------
# Reporting & cleanup
# ----------------------------

def write_status_snapshot(cancer_dir: Path, samples: Dict[str, List[str]], inv: Dict[str, SRRInfo]) -> None:
    """Write sample_list.with_status.txt in the legacy 4‑column format."""
    out_lines: List[str] = []
    for sample, srrs in samples.items():
        r1_names: List[str] = []
        r2_names: List[str] = []
        sra_ready = 0
        fq_ready = 0
        total = len(srrs)
        for srr in srrs:
            info = inv[srr]
            if info.r1 and info.r1.exists():
                r1_names.append(info.r1.name)
            else:
                r1_names.append(f"{srr}_1.fastq.gz")
            # Only include R2 if it exists; leave empty for single‑end
            if info.r2 and info.r2.exists():
                r2_names.append(info.r2.name)
            # progress counts
            sra_ready += 1 if info.sra_ok else 0
            fq_ready += 1 if (info.r1_ok and (info.r2 is None or info.r2_ok)) else 0
        # derive status label
        if fq_ready == total:
            status = "FASTQ_DONE"
        elif sra_ready == total:
            status = f"FASTQ_IN_PROGRESS ({fq_ready}/{total} done)"
        elif sra_ready > 0:
            status = f"SRA_IN_PROGRESS ({sra_ready}/{total} done)"
        else:
            status = f"SRA_IN_PROGRESS (0/{total} done)"
        out_lines.append("\t".join([
            sample,
            ",".join(r1_names),
            ",".join(r2_names) if r2_names else "",
            status,
        ]))
    tmp = cancer_dir / "sample_list.with_status.txt.tmp"
    dst = cancer_dir / "sample_list.with_status.txt"
    tmp.write_text("\n".join(out_lines) + "\n")
    tmp.replace(dst)


def cleanup_sra_for_completed(cancer_dir: Path, inv: Dict[str, SRRInfo]) -> int:
    removed = 0
    for info in inv.values():
        if info.sra and info.sra.exists():
            fastq_done = info.r1_ok and (info.r2 is None or info.r2_ok)
            if fastq_done:
                try:
                    info.sra.unlink()
                    removed += 1
                except Exception:
                    pass
    return removed

# ----------------------------
# CLI operations
# ----------------------------

def do_plan(cancer_dir: Path, samples: Dict[str, List[str]]) -> List[Action]:
    all_srrs = [s for srrs in samples.values() for s in srrs]
    inv = inventory(cancer_dir, all_srrs)
    actions = plan_actions(inv)
    # pretty print
    for a in actions:
        if a.kind == "download":
            print(f"DOWNLOAD {a.srr}\t(prefetch)")
        else:
            print(f"CONVERT  {a.srr}\t(fastq-dump)")
    print(f"— total actions: {len(actions)}")
    return actions


def do_apply(cancer_dir: Path, samples: Dict[str, List[str]], no_wait: bool = True) -> None:
    all_srrs = [s for srrs in samples.values() for s in srrs]
    inv = inventory(cancer_dir, all_srrs)
    actions = plan_actions(inv)
    print(f"Planned actions: {len(actions)}")
    for act in actions:
        if act.kind == "download":
            ok = prefetch(cancer_dir, act.srr)
            print(("✓" if ok else "✗"), "prefetch", act.srr)
        else:
            # plan_actions only yields CONVERT when sra_ok=True; assert defensively
            if not inv[act.srr].sra_ok and not _find_sra(cancer_dir, act.srr):
                print("✗", "no SRA to convert for", act.srr)
                continue
            jid = submit_fastq_dump(cancer_dir, act.srr)
            print(("✓" if jid else "✗"), "bsub", act.srr, (jid or ""))
    # Always write a fresh status snapshot
    inv2 = inventory(cancer_dir, all_srrs)
    write_status_snapshot(cancer_dir, samples, inv2)
    if not no_wait:
        print("Note: waiting for jobs is not implemented in the minimal core. Run 'status' periodically.")


def do_status(cancer_dir: Path, samples: Dict[str, List[str]]) -> None:
    all_srrs = [s for srrs in samples.values() for s in srrs]
    inv = inventory(cancer_dir, all_srrs)
    write_status_snapshot(cancer_dir, samples, inv)
    print((cancer_dir / "sample_list.with_status.txt").as_posix())


def do_clean(cancer_dir: Path, samples: Dict[str, List[str]]) -> None:
    all_srrs = [s for srrs in samples.values() for s in srrs]
    inv = inventory(cancer_dir, all_srrs)
    n = cleanup_sra_for_completed(cancer_dir, inv)
    print(f"Removed {n} converted .sra files")


# ----------------------------
# Entry
# ----------------------------

def main():
    ap = argparse.ArgumentParser(description="POSEIDON FASTQ – minimal core")
    sub = ap.add_subparsers(dest="cmd", required=True)

    for name in ("plan", "apply", "status", "clean"):
        a = sub.add_parser(name)
        a.add_argument("cancer_dir", help="Directory containing sample_list.txt")
    sub.add_parser("version")

    args = ap.parse_args()
    if args.cmd == "version":
        print("poseidon-core 0.1")
        return

    cancer_dir = Path(args.cancer_dir).resolve()
    samples = parse_sample_list(cancer_dir / "sample_list.txt")

    if args.cmd == "plan":
        do_plan(cancer_dir, samples)
    elif args.cmd == "apply":
        do_apply(cancer_dir, samples, no_wait=True)
    elif args.cmd == "status":
        do_status(cancer_dir, samples)
    elif args.cmd == "clean":
        do_clean(cancer_dir, samples)


if __name__ == "__main__":
    main()
