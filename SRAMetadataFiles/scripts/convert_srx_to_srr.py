#!/usr/bin/env python3
"""
Convert SRX experiment IDs to SRR run IDs in metadata files.
"""

import csv
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional
import argparse


def get_srr_from_srx(srx_id: str) -> str:
    """
    Query NCBI E-utilities to get SRR ID from SRX ID.
    """
    try:
        # Step 1: Search for the SRX ID to get the UID
        search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=sra&term={srx_id}&retmode=json"

        with urllib.request.urlopen(search_url) as response:
            import json
            data = json.load(response)

        uid_list = data.get('esearchresult', {}).get('idlist', [])
        if not uid_list:
            print(f"  Warning: No UID found for {srx_id}")
            return ''

        uid = uid_list[0]

        # Step 2: Fetch the run info using efetch
        fetch_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=sra&id={uid}&retmode=xml"

        with urllib.request.urlopen(fetch_url) as response:
            xml_data = response.read()

        # Parse XML to extract SRR ID
        root = ET.fromstring(xml_data)

        # Look for RUN accession
        for run in root.findall('.//RUN'):
            srr_id = run.get('accession', '')
            if srr_id.startswith('SRR'):
                return srr_id

        # Alternative: look in IDENTIFIERS
        for id_elem in root.findall('.//IDENTIFIERS/PRIMARY_ID'):
            if id_elem.text and id_elem.text.startswith('SRR'):
                return id_elem.text

        print(f"  Warning: No SRR found for {srx_id}")
        return ''

    except Exception as e:
        print(f"  Error fetching {srx_id}: {e}")
        return ''


def convert_file(input_path: Path, output_path: Path, run_column: str = 'Run', exp_column: str = 'SRA_Experiment'):
    """
    Read TSV, convert SRX to SRR, write updated TSV.
    """
    print(f"Reading {input_path}...")

    with open(input_path, 'r', newline='') as f:
        reader = csv.DictReader(f, delimiter='\t')
        fieldnames = list(reader.fieldnames)
        rows = list(reader)

    print(f"Found {len(rows)} rows")

    # Build SRX to SRR mapping
    srx_to_srr = {}
    unique_srx = set(row.get(exp_column, '') for row in rows if row.get(exp_column, ''))

    print(f"Converting {len(unique_srx)} unique SRX IDs to SRR IDs...")

    for i, srx_id in enumerate(sorted(unique_srx), 1):
        if not srx_id or not srx_id.startswith('SRX'):
            continue

        print(f"  [{i}/{len(unique_srx)}] {srx_id}...", end='', flush=True)

        srr_id = get_srr_from_srx(srx_id)

        if srr_id:
            srx_to_srr[srx_id] = srr_id
            print(f" -> {srr_id}")
        else:
            print(f" FAILED")

        # Rate limiting - be nice to NCBI (they limit to ~3 per second)
        time.sleep(1.0)  # 1 request per second to avoid 429 errors

    # Update rows with SRR IDs
    updated = 0
    for row in rows:
        srx_id = row.get(exp_column, '')
        if srx_id in srx_to_srr:
            row[run_column] = srx_to_srr[srx_id]
            updated += 1

    print(f"\nUpdated {updated} rows with SRR IDs")

    # Write updated file
    print(f"Writing to {output_path}...")
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)

    print(f"Success! Wrote {len(rows)} rows to {output_path}")


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert SRX experiment IDs to SRR run IDs in a TSV file."
    )
    parser.add_argument(
        "input",
        type=str,
        help="Path to input TSV with columns including 'SRA_Experiment' and 'Run'",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional output TSV path (default: <input>_with_SRR.tsv)",
    )
    parser.add_argument(
        "--run-column",
        type=str,
        default="Run",
        help="Name of the run column to overwrite (default: Run)",
    )
    parser.add_argument(
        "--exp-column",
        type=str,
        default="SRA_Experiment",
        help="Name of the experiment column containing SRX IDs (default: SRA_Experiment)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None):
    if argv is None:
        argv = sys.argv[1:]

    args = parse_args(argv)

    input_file = Path(args.input)
    if args.output is None:
        output_file = input_file.with_name(input_file.stem + "_with_SRR.tsv")
    else:
        output_file = Path(args.output)

    if not input_file.exists():
        print(f"Error: {input_file} not found")
        return 1

    convert_file(
        input_path=input_file,
        output_path=output_file,
        run_column=args.run_column,
        exp_column=args.exp_column,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
