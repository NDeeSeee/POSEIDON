#!/usr/bin/env python3
"""Reconcile sample_list.txt files with SRA reference lists.

For each directory containing a sample_list.txt, this script:

* Parses SRR/ERR/DRR identifiers from the sample list (column 2).
* Parses SRR/ERR/DRR identifiers from any "*-SRA*.txt" reference files in
  the same directory (treats multiple reference files separately and jointly).
* Writes a per-directory `discrepancies.csv` with membership flags showing
  which identifiers appear in the sample list and in each reference file.
* Computes the intersection between the sample list and the union of
  reference lists, and writes:
    - `intersection_srrs.txt` : identifiers we are confident about
    - `missing_sra_from_intersection.txt` : intersection identifiers that
       are not yet present as .sra files
    - `pending_fastq_from_intersection.txt` : intersection identifiers that
       do not yet have both _1/_2.fastq.gz files
* Creates/updates project-wide aggregates:
    - `discrepancies_master.csv` summarising membership per directory
    - `sra_download_plan.tsv` listing directory/SRR pairs that still need
       .sra downloads (intersection only)
    - `fastq_conversion_plan.tsv` listing directory/SRR pairs that still
       require FASTQ conversion (intersection only)

Running the script is idempotent – it overwrites the generated outputs
using the current on-disk state each time.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set, Tuple


ROOT = Path(__file__).resolve().parents[2]
SAMPLE_LIST_NAME = "sample_list.txt"
REFERENCE_GLOB = "*-SRA*.txt"

SRR_PATTERN = re.compile(r"^(?:[SED]RR)[0-9]+$", re.IGNORECASE)


@dataclass
class DirectoryReport:
    relative_path: str
    sample_ids: Set[str] = field(default_factory=set)
    reference_sets: Dict[str, Set[str]] = field(default_factory=dict)
    existing_sra_ids: Set[str] = field(default_factory=set)
    existing_fastq_pairs: Set[str] = field(default_factory=set)

    @property
    def reference_union(self) -> Set[str]:
        union: Set[str] = set()
        for values in self.reference_sets.values():
            union.update(values)
        return union

    @property
    def intersection_ids(self) -> Set[str]:
        if not self.reference_sets:
            return set()
        return self.sample_ids & self.reference_union

    @property
    def missing_sra_ids(self) -> Set[str]:
        return self.intersection_ids - self.existing_sra_ids

    @property
    def pending_fastq_ids(self) -> Set[str]:
        pending: Set[str] = set()
        for srr in self.intersection_ids:
            if srr not in self.existing_fastq_pairs:
                pending.add(srr)
        return pending


def parse_sample_list(path: Path) -> Set[str]:
    identifiers: Set[str] = set()
    with path.open() as fh:
        for line in fh:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = line.strip().split()
            if len(parts) < 2:
                continue
            field = parts[1]
            field = field.replace("_1.fastq.gz", "").replace("_2.fastq.gz", "")
            for token in field.split(','):
                token = token.strip()
                if SRR_PATTERN.match(token):
                    identifiers.add(token.upper())
    return identifiers


def parse_reference_file(path: Path) -> Set[str]:
    identifiers: Set[str] = set()
    with path.open() as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line:
                continue
            for token in re.split(r"[\s,]+", line):
                token = token.strip()
                if SRR_PATTERN.match(token):
                    identifiers.add(token.upper())
    return identifiers


def detect_existing_sra(dir_path: Path) -> Set[str]:
    ids = {p.stem.upper() for p in dir_path.glob('*.sra')}
    return ids


def detect_existing_fastq_pairs(dir_path: Path) -> Set[str]:
    ids: Set[str] = set()
    fastq_1 = {p.stem[:-3].upper() for p in dir_path.glob('*_1.fastq.gz')}
    fastq_2 = {p.stem[:-3].upper() for p in dir_path.glob('*_2.fastq.gz')}
    ids.update(fastq_1 & fastq_2)
    return ids


def sanitize_column_name(filename: str) -> str:
    base = Path(filename).stem  # remove extension
    base = base.replace('-', '_').replace(' ', '_')
    return f"in_{base}"


def write_directory_discrepancies(report: DirectoryReport, dir_path: Path) -> None:
    if not report.reference_sets and not report.sample_ids:
        return

    columns: List[str] = ["srr_id", "in_sample_list"]
    reference_columns: List[str] = []
    for ref_name in sorted(report.reference_sets):
        column = sanitize_column_name(ref_name)
        reference_columns.append(column)
        columns.append(column)
    columns.append("in_any_reference")

    union_ids = sorted(report.sample_ids | report.reference_union)
    output_path = dir_path / "discrepancies.csv"
    with output_path.open('w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writeheader()
        for srr in union_ids:
            row = {"srr_id": srr, "in_sample_list": int(srr in report.sample_ids)}
            in_any_ref = False
            for ref_name, column in zip(sorted(report.reference_sets), reference_columns):
                present = int(srr in report.reference_sets[ref_name])
                row[column] = present
                if present:
                    in_any_ref = True
            row["in_any_reference"] = int(in_any_ref)
            writer.writerow(row)


def write_simple_list(path: Path, identifiers: Iterable[str]) -> None:
    identifiers = list(sorted(set(identifiers)))
    if identifiers:
        with path.open('w') as fh:
            fh.write('\n'.join(identifiers) + '\n')
    elif path.exists():
        path.unlink()


def main() -> None:
    reports: List[DirectoryReport] = []

    for sample_file in sorted(ROOT.glob(f"**/{SAMPLE_LIST_NAME}")):
        dir_path = sample_file.parent
        relative_path = str(dir_path.relative_to(ROOT))

        sample_ids = parse_sample_list(sample_file)

        reference_sets: Dict[str, Set[str]] = {}
        for ref_file in sorted(dir_path.glob(REFERENCE_GLOB)):
            if ref_file.name == SAMPLE_LIST_NAME:
                continue
            reference_sets[ref_file.name] = parse_reference_file(ref_file)

        existing_sra_ids = detect_existing_sra(dir_path)
        existing_fastq_pairs = detect_existing_fastq_pairs(dir_path)

        report = DirectoryReport(
            relative_path=relative_path,
            sample_ids=sample_ids,
            reference_sets=reference_sets,
            existing_sra_ids=existing_sra_ids,
            existing_fastq_pairs=existing_fastq_pairs,
        )
        reports.append(report)

        # per-directory outputs
        write_directory_discrepancies(report, dir_path)
        write_simple_list(dir_path / "intersection_srrs.txt", report.intersection_ids)
        write_simple_list(dir_path / "missing_sra_from_intersection.txt", report.missing_sra_ids)
        write_simple_list(dir_path / "pending_fastq_from_intersection.txt", report.pending_fastq_ids)

    # project-wide aggregates
    master_columns = ["directory", "srr_id", "in_sample_list", "in_reference_union"]
    master_rows: List[Tuple[str, str, int, int]] = []

    download_plan_rows: List[Tuple[str, str]] = []
    fastq_plan_rows: List[Tuple[str, str]] = []

    for report in reports:
        union_ids = sorted(report.sample_ids | report.reference_union)
        for srr in union_ids:
            master_rows.append(
                (
                    report.relative_path,
                    srr,
                    int(srr in report.sample_ids),
                    int(srr in report.reference_union),
                )
            )

        for srr in sorted(report.missing_sra_ids):
            download_plan_rows.append((report.relative_path, srr))

        for srr in sorted(report.pending_fastq_ids):
            fastq_plan_rows.append((report.relative_path, srr))

    master_path = ROOT / "discrepancies_master.csv"
    with master_path.open('w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(master_columns)
        writer.writerows(master_rows)

    download_plan_path = ROOT / "sra_download_plan.tsv"
    with download_plan_path.open('w', newline='') as tsvfile:
        writer = csv.writer(tsvfile, delimiter='\t')
        writer.writerow(["directory", "srr_id"])
        writer.writerows(download_plan_rows)

    fastq_plan_path = ROOT / "fastq_conversion_plan.tsv"
    with fastq_plan_path.open('w', newline='') as tsvfile:
        writer = csv.writer(tsvfile, delimiter='\t')
        writer.writerow(["directory", "srr_id"])
        writer.writerows(fastq_plan_rows)

    print(f"Processed {len(reports)} directories containing sample lists.")
    print(f"Discrepancy summary written to {master_path.relative_to(ROOT)}")
    print(f"Directory download plan written to {download_plan_path.relative_to(ROOT)}"
          f" with {len(download_plan_rows)} entries")
    print(f"FASTQ conversion plan written to {fastq_plan_path.relative_to(ROOT)}"
          f" with {len(fastq_plan_rows)} entries")


if __name__ == "__main__":
    main()
