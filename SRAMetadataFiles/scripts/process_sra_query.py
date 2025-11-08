#!/usr/bin/env python3
import sys, time, json, urllib.parse, urllib.request, xml.etree.ElementTree as ET, re, csv
from pathlib import Path
from typing import List, Optional, Dict

RATE_LIMIT_S = 0.4
BATCH = 200

def eget(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "bio-cli/1.0"})
    with urllib.request.urlopen(req) as r:
        return r.read()

def esearch_ids(term: str) -> List[str]:
    url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?' + urllib.parse.urlencode({
        'db':'sra','term':term,'retmax':'100000','retmode':'json'
    })
    return json.loads(eget(url)).get('esearchresult',{}).get('idlist',[])

def parse_pkgs(xmlb: bytes, *, require_rna: bool=True, exclude_normals: bool=True) -> List[Dict[str,str]]:
    root = ET.fromstring(xmlb)
    rows = []
    normal_pat = re.compile(r"\b(non[- ]?tumou?r|normal|benign|control|healthy|adjacent|blood|pbmc|plasma|serum)\b", re.I)
    cellline_pat = re.compile(r"\b(cell\s*line|mcf-?7|t47d|bt-?474|skbr3|md-?mba|zr-?75|sum|mda-?mb)\b", re.I)
    for pkg in root.findall('.//EXPERIMENT_PACKAGE'):
        lib = (pkg.findtext('.//LIBRARY_STRATEGY') or '')
        if require_rna and 'RNA' not in lib.upper():
            continue
        org = (pkg.findtext('.//SAMPLE/SAMPLE_NAME/SCIENTIFIC_NAME') or '').lower()
        if org and org not in {'homo sapiens','human'}:
            continue
        exp = pkg.find('.//EXPERIMENT')
        srx = exp.get('accession') if exp is not None else ''
        title = pkg.findtext('.//SAMPLE/TITLE') or (exp.findtext('TITLE') if exp is not None else '')
        alias = pkg.find('.//SAMPLE')
        alias = alias.get('alias') if alias is not None else ''
        blob = ' '.join([title, alias, lib])
        if exclude_normals and (normal_pat.search(blob) or cellline_pat.search(blob)):
            continue
        biosample = ''
        s = pkg.find('.//SAMPLE')
        if s is not None:
            for xid in s.findall('.//EXTERNAL_ID'):
                if xid.get('namespace','').lower()=='biosample' and (xid.text or '').startswith('SAMN'):
                    biosample = xid.text.strip(); break
            if not biosample:
                m = re.search(r'SAMN\d+', ET.tostring(s, encoding='unicode'))
                if m: biosample = m.group(0)
        for run in pkg.findall('.//RUN_SET/RUN'):
            srr = run.get('accession','')
            if not srr: continue
            rows.append({
                'Run': srr,
                'SRA_Experiment': srx,
                'BioSample': biosample,
                'geo_accession': '',
                'title': title,
                'sample_id': alias,
                'tissue': 'breast',
                'who_grade': '',
                'recurrence_status': '',
                'top_label': 'Tumor',
                'origin': 'breast',
                'sample_type': 'HR+HER2+Breast',
            })
    return rows

def main(argv: Optional[List[str]] = None) -> int:
    import argparse
    if argv is None: argv = sys.argv[1:]
    ap = argparse.ArgumentParser(description='Generate TSV from SRA query term')
    ap.add_argument('term', help='Entrez SRA search term, e.g., GSE45419')
    ap.add_argument('--output','-o', default=None)
    ap.add_argument('--no-rna-filter', action='store_true')
    ap.add_argument('--include-normals', action='store_true')
    args = ap.parse_args(argv)
    ids = esearch_ids(args.term)
    rows = []
    for i in range(0, len(ids), BATCH):
        batch = ids[i:i+BATCH]
        url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?' + urllib.parse.urlencode({'db':'sra','id':','.join(batch),'retmode':'xml'})
        rows.extend(parse_pkgs(eget(url), require_rna=not args.no_rna_filter, exclude_normals=not args.include_normals))
        time.sleep(RATE_LIMIT_S)
    out = Path(args.output) if args.output else Path('sra_query.tsv')
    fields = ['Run','SRA_Experiment','BioSample','geo_accession','title','sample_id','tissue','who_grade','recurrence_status','top_label','origin','sample_type']
    with out.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter='\t')
        w.writeheader(); w.writerows(rows)
    print(f'Wrote {len(rows)} rows to {out}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
