#!/usr/bin/env python3
"""Re-run OptiType for SmallIntestine and RenalPelvis only."""

import sys
from run_hla_workflow import submit_optitype_jobs, count_bam_files

dirs = [
    '/data/salomonis-archive/FASTQs/NCI-R01/POSEIDON/Tumors/SmallIntestine/bams',
    '/data/salomonis-archive/FASTQs/NCI-R01/POSEIDON/Tumors/RenalPelvis/bams'
]

for bam_dir in dirs:
    tumor_type = bam_dir.split('/')[-2]
    print('\n' + '='*60)
    print(f'Processing: {tumor_type}/bams')
    print('='*60)

    bam_count = count_bam_files(bam_dir)
    print(f'  Found {bam_count} BAM files')

    submit_optitype_jobs(bam_dir)

print('\n' + '='*60)
print('OptiType workflow completed for SmallIntestine and RenalPelvis')
print('='*60)
