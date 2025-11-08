#!/usr/bin/env python3
"""
Process GSE98894 data by adding classification metadata from GEO.
Creates an enriched TSV file with top_label and tissue origin information.
"""

import csv
import gzip
import sys
import urllib.request
from pathlib import Path
from typing import Dict


def download_and_parse_geo_matrix(geo_id: str = "GSE98894") -> Dict[str, Dict[str, str]]:
    """
    Download and parse GEO series matrix to extract sample metadata.
    Returns dict mapping GSM IDs to their characteristics.
    """
    url = f"https://ftp.ncbi.nlm.nih.gov/geo/series/{geo_id[:-3]}nnn/{geo_id}/matrix/{geo_id}_series_matrix.txt.gz"

    print(f"Downloading GEO series matrix from {url}...")

    with urllib.request.urlopen(url) as response:
        with gzip.GzipFile(fileobj=response) as f:
            lines = [line.decode('utf-8').rstrip('\n') for line in f]

    # Find the lines with sample metadata
    sample_geo_line = None
    characteristics_lines = []

    for line in lines:
        if line.startswith('!Sample_geo_accession'):
            sample_geo_line = line
        elif line.startswith('!Sample_characteristics_ch1'):
            characteristics_lines.append(line)

    if not sample_geo_line or not characteristics_lines:
        raise ValueError("Could not find sample metadata in GEO series matrix")

    # Parse GSM IDs
    gsm_ids = sample_geo_line.split('\t')[1:]  # Skip the label
    gsm_ids = [gsm.strip('"') for gsm in gsm_ids]

    # Parse characteristics
    sample_data = {gsm: {} for gsm in gsm_ids}

    for char_line in characteristics_lines:
        parts = char_line.split('\t')[1:]  # Skip the label
        parts = [p.strip('"') for p in parts]

        for gsm, value in zip(gsm_ids, parts):
            # Parse key: value format
            if ': ' in value:
                key, val = value.split(': ', 1)
                sample_data[gsm][key] = val

    print(f"Parsed metadata for {len(sample_data)} samples")
    return sample_data


def enrich_runinfo_with_geo_metadata(
    runinfo_path: Path,
    geo_metadata: Dict[str, Dict[str, str]],
    output_path: Path,
    filter_origin: str = None
) -> None:
    """
    Read runinfo CSV, enrich with GEO metadata, and write as TSV.
    Optionally filter by tissue origin (e.g., 'small intestine').
    """
    print(f"Reading {runinfo_path}...")

    # Read the CSV file
    with open(runinfo_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        rows = list(reader)

    print(f"Read {len(rows)} rows")

    # Add new columns for classification
    new_fieldnames = fieldnames + ['top_label', 'origin', 'tumor_type']

    # Enrich each row
    enriched_rows = []
    filtered_count = 0
    for row in rows:
        sample_name = row.get('SampleName', '')

        # Get GEO metadata for this sample
        sample_meta = geo_metadata.get(sample_name, {})
        origin = sample_meta.get('origin', 'unknown')

        # Filter by origin if specified
        if filter_origin and origin != filter_origin:
            filtered_count += 1
            continue

        # Add classification columns
        row['top_label'] = 'Tumor'  # All samples in this dataset are tumors
        row['origin'] = origin
        row['tumor_type'] = sample_meta.get('type', 'unknown')

        enriched_rows.append(row)

    if filter_origin:
        print(f"Filtered to {len(enriched_rows)} samples with origin='{filter_origin}' (excluded {filtered_count})")

    # Write as TSV
    print(f"Writing enriched data to {output_path}...")
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames, delimiter='\t')
        writer.writeheader()
        writer.writerows(enriched_rows)

    print(f"Wrote {len(enriched_rows)} enriched rows to {output_path}")

    # Print summary
    origins = {}
    for row in enriched_rows:
        origin = row['origin']
        origins[origin] = origins.get(origin, 0) + 1

    print("\nSample distribution by origin:")
    for origin, count in sorted(origins.items()):
        print(f"  {origin}: {count}")


def main():
    # Paths
    runinfo_path = Path("GSE98894_runinfo.csv")
    output_path = Path("GSE98894_SmallIntestine.tsv")

    if not runinfo_path.exists():
        print(f"Error: {runinfo_path} not found")
        return 1

    # Download and parse GEO metadata
    geo_metadata = download_and_parse_geo_matrix("GSE98894")

    # Enrich runinfo data with GEO metadata, filtering for small intestine only
    enrich_runinfo_with_geo_metadata(
        runinfo_path,
        geo_metadata,
        output_path,
        filter_origin='small intestine'
    )

    print(f"\nSuccess! Created {output_path}")
    print(f"Next step: Convert to xlsx using tsv_to_workbook.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
