#!/usr/bin/env python3

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

try:
    from openpyxl import Workbook
except ModuleNotFoundError as exc:
    sys.stderr.write(
        "Error: openpyxl is required to write .xlsx files.\n"
        "Install it with: pip install openpyxl\n"
    )
    raise


SHEET_ORDER = [
    "Tumors",
    "Premalignant",
    "Controls",
    "Bulk_CellTypes",
    "Unknown",
]


def normalize_label(raw_label: str) -> str:
    if raw_label is None:
        return ""
    simplified = " ".join(raw_label.strip().lower().replace("_", " ").replace("-", " ").split())
    return simplified


def map_top_label_to_sheet(raw_label: str) -> Tuple[str, bool]:
    """
    Map a top_label value to a target sheet name.

    Returns (sheet_name, is_recognized)
    """
    label = normalize_label(raw_label)

    if label == "tumor" or label == "tumour":
        return "Tumors", True
    if label in {"pre malignant", "premalignant"}:
        return "Premalignant", True
    if label == "normal":
        return "Controls", True
    if label in {"cell line", "cellline", "cell line sample"}:
        return "Bulk_CellTypes", True
    if label == "unknown":
        return "Unknown", True

    # Unrecognized labels go to Unknown
    return "Unknown", False


def read_tsv_as_rows(tsv_path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    with tsv_path.open("r", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("Input TSV appears to have no header row.")
        fieldnames = list(reader.fieldnames)
        rows: List[Dict[str, str]] = [row for row in reader]
    return fieldnames, rows


def write_workbook(
    fieldnames: List[str],
    sheet_to_rows: Dict[str, List[Dict[str, str]]],
    output_path: Path,
    include_empty_sheets: bool,
) -> None:
    wb = Workbook()
    # Remove the default sheet to fully control sheet creation
    default_title = wb.active.title
    wb.remove(wb[default_title])

    for sheet_name in SHEET_ORDER:
        rows = sheet_to_rows.get(sheet_name, [])
        if not rows and not include_empty_sheets:
            continue
        ws = wb.create_sheet(title=sheet_name)
        ws.append(fieldnames)
        for row in rows:
            ws.append([row.get(col, "") for col in fieldnames])

    wb.save(str(output_path))


def convert_tsv_to_xlsx(
    input_path: Path,
    output_path: Path,
    include_empty_sheets: bool = False,
) -> int:
    fieldnames, rows = read_tsv_as_rows(input_path)

    # Rename 'run_accession' column to 'Run' in headers and rows
    if "run_accession" in fieldnames:
        idx = fieldnames.index("run_accession")
        fieldnames[idx] = "Run"
        for row in rows:
            # Preserve an existing 'Run' if present; otherwise migrate value
            if "Run" not in row:
                row["Run"] = row.get("run_accession", "")
            # Remove the old key to avoid duplicate columns downstream
            if "run_accession" in row:
                row.pop("run_accession", None)

    # Rename 'BioSample' to 'BioSample_Sparse' (retain original values under the new name)
    if "BioSample" in fieldnames:
        idx = fieldnames.index("BioSample")
        fieldnames[idx] = "BioSample_Sparse"
        for row in rows:
            # Preserve an existing 'BioSample_Sparse' if present; otherwise migrate value
            if "BioSample_Sparse" not in row:
                row["BioSample_Sparse"] = row.get("BioSample", "")
            # Remove the old key to avoid duplicate columns downstream
            if "BioSample" in row:
                row.pop("BioSample", None)

    # Rename 'sample_accession' to 'BioSample' (this becomes the canonical BioSample column)
    if "sample_accession" in fieldnames:
        idx = fieldnames.index("sample_accession")
        fieldnames[idx] = "BioSample"
        for row in rows:
            # Do not overwrite an existing 'BioSample' value if somehow present
            if "BioSample" not in row or not row.get("BioSample"):
                row["BioSample"] = row.get("sample_accession", "")
            # Remove the old key to avoid duplicate columns downstream
            if "sample_accession" in row:
                row.pop("sample_accession", None)

    if "top_label" not in fieldnames:
        sys.stderr.write(
            "Error: The input file is missing the required 'top_label' column.\n"
        )
        return 1

    sheet_to_rows: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    unrecognized_labels: Dict[str, int] = defaultdict(int)

    for row in rows:
        top_label = row.get("top_label", "")
        sheet_name, recognized = map_top_label_to_sheet(top_label)
        sheet_to_rows[sheet_name].append(row)
        if not recognized:
            norm = normalize_label(top_label)
            unrecognized_labels[norm] += 1

    # Ensure deterministic iteration order for writing
    for sheet_name in SHEET_ORDER:
        sheet_to_rows.setdefault(sheet_name, [])

    write_workbook(fieldnames, sheet_to_rows, output_path, include_empty_sheets)

    total_rows = sum(len(v) for v in sheet_to_rows.values())
    sys.stdout.write(
        f"Wrote {total_rows} rows across sheets to {output_path.name}.\n"
    )
    for sheet_name in SHEET_ORDER:
        count = len(sheet_to_rows[sheet_name])
        if count or include_empty_sheets:
            sys.stdout.write(f"  - {sheet_name}: {count}\n")

    if unrecognized_labels:
        sys.stderr.write("Warning: Unrecognized top_label values routed to 'Unknown':\n")
        for label, count in sorted(unrecognized_labels.items(), key=lambda x: (-x[1], x[0])):
            sys.stderr.write(f"  - '{label}': {count}\n")

    return 0


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Convert a TSV metadata file into an XLSX workbook with sheets by top_label."
        )
    )
    parser.add_argument(
        "input",
        type=str,
        help="Path to input .tsv file (must include 'top_label' column)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional output .xlsx path (default: same basename as input)",
    )
    parser.add_argument(
        "--include-empty-sheets",
        action="store_true",
        help="Create empty sheets for all categories even if no rows",
    )
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)

    input_path = Path(args.input)
    if not input_path.exists():
        sys.stderr.write(f"Error: Input file not found: {input_path}\n")
        return 1

    if args.output is None:
        output_path = input_path.with_suffix(".xlsx")
    else:
        output_path = Path(args.output)
        if output_path.suffix.lower() != ".xlsx":
            output_path = output_path.with_suffix(".xlsx")

    return convert_tsv_to_xlsx(
        input_path=input_path,
        output_path=output_path,
        include_empty_sheets=args.include_empty_sheets,
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
