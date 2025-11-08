#!/usr/bin/env python3
"""
Generate a standardized TSV from an SRA BioProject accession using NCBI E-utilities.
Outputs columns aligned with other project TSVs and includes classification fields.
"""

import csv
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re


EFETCH_BATCH_SIZE = 200  # E-utilities recomm. <= 200 IDs per efetch
RATE_LIMIT_S = 0.4       # ~2-3 requests/sec to be polite


def eutils_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "bio-cli/1.0 (contact: lab)"})
    with urllib.request.urlopen(req) as resp:
        return resp.read()


def esearch_sra_ids_for_bioproject(bioproject: str) -> List[str]:
    term = f"{bioproject}[BioProject]"
    params = {
        "db": "sra",
        "term": term,
        "retmax": "100000",
        "retmode": "json",
    }
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + urllib.parse.urlencode(params)
    data = eutils_get(url)
    import json
    obj = json.loads(data)
    ids = obj.get("esearchresult", {}).get("idlist", [])
    return [str(x) for x in ids]


def parse_experiment_packages(xml_data: bytes, *, require_rna_seq: bool = True, exclude_normals: bool = True) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    root = ET.fromstring(xml_data)

    # Keyword filters
    normal_pat = re.compile(r"\b(non[- ]?tumou?r|normal|benign|control|healthy|adjacent|blood|pbmc|plasma|serum)\b", re.I)
    cellline_pat = re.compile(r"\b(cell\s*line|mcf-?7|t47d|bt-?474|skbr3|md-?mba|zr-?75|sum|mda-?mb)\b", re.I)

    for pkg in root.findall('.//EXPERIMENT_PACKAGE'):
        # Extract experiment (SRX)
        exp = pkg.find('.//EXPERIMENT')
        srx = exp.get('accession') if exp is not None else ''
        exp_title = exp.findtext('TITLE') if exp is not None else ''

        # Library strategy
        lib_strategy = pkg.findtext('.//LIBRARY_STRATEGY') or ''

        # Extract sample info (BioSample SAMN, title, alias)
        sample = pkg.find('.//SAMPLE')
        sample_title = sample.findtext('TITLE') if sample is not None else ''
        sample_alias = sample.get('alias') if sample is not None else ''

        # Organism (ensure human)
        organism = pkg.findtext('.//SAMPLE/SAMPLE_NAME/SCIENTIFIC_NAME') or ''

        bio_sample = ''
        if sample is not None:
            for xid in sample.findall('.//EXTERNAL_ID'):
                if xid.get('namespace', '').lower() == 'biosample' and (xid.text or '').startswith('SAMN'):
                    bio_sample = xid.text.strip()
                    break
            if not bio_sample:
                # Sometimes BioSample appears elsewhere; fallback regex
                xml_str = ET.tostring(sample, encoding='unicode')
                m = re.search(r'SAMN\d+', xml_str)
                if m:
                    bio_sample = m.group(0)

        # Prefer sample title; fallback to experiment title
        title = sample_title or exp_title or sample_alias

        # Build a blob for keyword evaluation
        blob = ' '.join([title, sample_alias, organism, lib_strategy])

        # Filters
        if require_rna_seq and 'RNA' not in lib_strategy.upper():
            continue
        if organism and organism.lower() not in {'homo sapiens', 'human'}:
            continue
        if exclude_normals and (normal_pat.search(blob) or cellline_pat.search(blob)):
            continue

        # For each RUN under this package, emit a row
        for run in pkg.findall('.//RUN_SET/RUN'):
            srr = run.get('accession', '')
            if not srr:
                continue
            row: Dict[str, str] = {
                'Run': srr,
                'SRA_Experiment': srx or '',
                'BioSample': bio_sample,
                'geo_accession': '',
                'title': title,
                'sample_id': sample_alias,
                'tissue': 'breast',
                'who_grade': '',
                'recurrence_status': '',
                'top_label': 'Tumor',
                'origin': 'breast',
                'sample_type': 'HR+HER2+Breast',
            }
            rows.append(row)

    return rows


def fetch_rows_for_bioproject(bioproject: str, *, require_rna_seq: bool = True, exclude_normals: bool = True) -> List[Dict[str, str]]:
    ids = esearch_sra_ids_for_bioproject(bioproject)
    print(f"Found {len(ids)} SRA records for {bioproject}")
    rows: List[Dict[str, str]] = []

    for i in range(0, len(ids), EFETCH_BATCH_SIZE):
        batch = ids[i:i+EFETCH_BATCH_SIZE]
        params = {
            "db": "sra",
            "id": ",".join(batch),
            "retmode": "xml",
        }
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?" + urllib.parse.urlencode(params)
        xml_bytes = eutils_get(url)
        rows.extend(parse_experiment_packages(xml_bytes, require_rna_seq=require_rna_seq, exclude_normals=exclude_normals))
        print(f"  Parsed {len(rows)} rows so far...")
        time.sleep(RATE_LIMIT_S)

    return rows


def write_tsv(output_path: Path, rows: List[Dict[str, str]]) -> None:
    fieldnames = [
        'Run', 'SRA_Experiment', 'BioSample', 'geo_accession', 'title',
        'sample_id', 'tissue', 'who_grade', 'recurrence_status',
        'top_label', 'origin', 'sample_type'
    ]
    with output_path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t', extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)


def main(argv: Optional[List[str]] = None) -> int:
    import argparse
    if argv is None:
        argv = sys.argv[1:]

    ap = argparse.ArgumentParser(description="Generate TSV from SRA BioProject accession")
    ap.add_argument("bioproject", help="BioProject accession, e.g., PRJNA157235")
    ap.add_argument("--output", "-o", default=None, help="Output TSV path")
    ap.add_argument("--no-rna-filter", action="store_true", help="Do not require LIBRARY_STRATEGY to be RNA-Seq")
    ap.add_argument("--include-normals", action="store_true", help="Do not exclude normals/controls/blood/cell lines")
    args = ap.parse_args(argv)

    out = Path(args.output) if args.output else Path(f"{args.bioproject}_HR+HER2+Breast.tsv")

    print(f"Fetching metadata for {args.bioproject} via E-utilities...")
    rows = fetch_rows_for_bioproject(
        args.bioproject,
        require_rna_seq=not args.no_rna_filter,
        exclude_normals=not args.include_normals,
    )
    print(f"Total rows: {len(rows)}")

    print(f"Writing {out}...")
    write_tsv(out, rows)

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
