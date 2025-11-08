#!/usr/bin/env python3
"""
Process GSE252291 (Meningioma) data from GEO series matrix.
Creates an enriched TSV file with classification metadata.
"""

import csv
import gzip
import sys
import urllib.request
from pathlib import Path
from typing import Dict, List, Tuple
import re


def download_and_parse_geo_matrix(geo_id: str = "GSE252291") -> Tuple[List[str], List[Dict[str, str]]]:
    """
    Download and parse GEO series matrix to extract sample metadata.
    Returns (fieldnames, list of sample dicts).
    """
    url = f"https://ftp.ncbi.nlm.nih.gov/geo/series/{geo_id[:-3]}nnn/{geo_id}/matrix/{geo_id}_series_matrix.txt.gz"

    print(f"Downloading GEO series matrix from {url}...")

    with urllib.request.urlopen(url) as response:
        with gzip.GzipFile(fileobj=response) as f:
            lines = [line.decode('utf-8').rstrip('\n') for line in f]

    # Parse the matrix file
    sample_data_by_field = {}  # field_name -> list of values
    characteristics_lines = []  # Multiple characteristics_ch1 lines
    relation_lines = []  # Multiple relation lines (BioSample, SRA, etc)

    for line in lines:
        if line.startswith('!Sample_characteristics_ch1'):
            # Collect all characteristics lines
            parts = line.split('\t')
            values = [v.strip('"') for v in parts[1:]]
            characteristics_lines.append(values)
        elif line.startswith('!Sample_relation'):
            # Collect all relation lines (multiple relations per sample)
            parts = line.split('\t')
            values = [v.strip('"') for v in parts[1:]]
            relation_lines.append(values)
        elif line.startswith('!Sample_'):
            parts = line.split('\t')
            field_name = parts[0].replace('!Sample_', '')
            values = [v.strip('"') for v in parts[1:]]
            sample_data_by_field[field_name] = values

    # Get number of samples
    if 'geo_accession' not in sample_data_by_field:
        raise ValueError("Could not find sample geo_accession in matrix")

    n_samples = len(sample_data_by_field['geo_accession'])
    print(f"Found {n_samples} samples in GEO series matrix")

    # Build list of sample dictionaries
    samples = []
    for i in range(n_samples):
        sample = {}
        for field_name, values in sample_data_by_field.items():
            if i < len(values):
                sample[field_name] = values[i]
            else:
                sample[field_name] = ''
        samples.append(sample)

    # Extract Run IDs and BioSample IDs from relation lines
    print("Extracting SRA Run IDs and BioSample IDs...")
    for i, sample in enumerate(samples):
        # Collect all relations for this sample
        all_relations = []
        for relation_line_values in relation_lines:
            if i < len(relation_line_values):
                all_relations.append(relation_line_values[i])

        # Combine all relation strings
        combined_relations = ' '.join(all_relations)

        # Extract SRX ID
        srx_match = re.search(r'SRX\d+', combined_relations)
        if srx_match:
            sample['SRA_Experiment'] = srx_match.group(0)
        else:
            sample['SRA_Experiment'] = ''

        # Extract BioSample (SAMN) ID
        samn_match = re.search(r'SAMN\d+', combined_relations)
        if samn_match:
            sample['BioSample'] = samn_match.group(0)
        else:
            sample['BioSample'] = ''

        # For now, use SRX as Run ID proxy
        sample['Run'] = sample['SRA_Experiment']  # Placeholder

    # Parse characteristics into separate fields
    print("Parsing sample characteristics...")
    for i, sample in enumerate(samples):
        # Collect all characteristics for this sample from all characteristic lines
        char_dict = {}
        for char_line_values in characteristics_lines:
            if i < len(char_line_values):
                char_str = char_line_values[i]
                if ': ' in char_str:
                    key, val = char_str.split(': ', 1)
                    char_dict[key.strip()] = val.strip()

        # Add parsed characteristics to sample
        sample['sample_id'] = char_dict.get('sample id', '')
        sample['tissue'] = char_dict.get('tissue', '')
        sample['who_grade'] = char_dict.get('who grade', '')
        sample['recurrence_status'] = char_dict.get('recurrence status', '')
        sample['disease_state'] = char_dict.get('disease state', '')

    # Define output fieldnames
    fieldnames = [
        'Run', 'SRA_Experiment', 'BioSample', 'geo_accession', 'title',
        'sample_id', 'tissue', 'who_grade', 'recurrence_status',
        'top_label', 'origin', 'sample_type'
    ]

    # Add classification fields
    for sample in samples:
        # All samples are meningioma tumors
        sample['top_label'] = 'Tumor'
        sample['origin'] = 'brain and CNS'
        sample['sample_type'] = 'meningioma'

    print(f"Parsed metadata for {len(samples)} samples")
    return fieldnames, samples


def write_tsv(samples: List[Dict[str, str]], fieldnames: List[str], output_path: Path) -> None:
    """Write samples to TSV file."""
    print(f"Writing data to {output_path}...")

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t', extrasaction='ignore')
        writer.writeheader()
        writer.writerows(samples)

    print(f"Wrote {len(samples)} samples to {output_path}")

    # Print summary
    grades = {}
    for sample in samples:
        grade = sample.get('who_grade', 'unknown')
        grades[grade] = grades.get(grade, 0) + 1

    print("\nSample distribution by WHO grade:")
    for grade, count in sorted(grades.items()):
        print(f"  {grade}: {count}")


def main():
    output_path = Path("GSE252291_MeningiomaBrain+CNS.tsv")

    # Download and parse GEO metadata
    fieldnames, samples = download_and_parse_geo_matrix("GSE252291")

    # Write TSV file
    write_tsv(samples, fieldnames, output_path)

    print(f"\nSuccess! Created {output_path}")
    print(f"Next step: Convert to xlsx using tsv_to_workbook.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
