#!/usr/bin/env python3

import sys
from collections import defaultdict

if len(sys.argv) != 3:
    print("Usage: python3 merge_srrs.py <input_file.txt> <output_file.txt>")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]

# Dictionary mapping sample IDs → list of SRR IDs
sample_to_srrs = defaultdict(list)

with open(input_file, "r") as infile:
    for line in infile:
        parts = line.strip().split("\t")
        if len(parts) != 2:
            continue
        srr, sample = parts
        sample_to_srrs[sample].append(srr)

with open(output_file, "w") as outfile:
    for sample, srrs in sample_to_srrs.items():
        r1_files = ",".join([f"{srr}_1.fastq.gz" for srr in srrs])
        r2_files = ",".join([f"{srr}_2.fastq.gz" for srr in srrs])
        outfile.write(f"{sample}\t{r1_files}\t{r2_files}\n")
