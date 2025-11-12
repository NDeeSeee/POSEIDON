#!/usr/bin/env python3
"""Re-run OptiType for RenalPelvis only."""

import sys
from run_hla_workflow import submit_optitype_jobs, count_bam_files

bam_dir = '/data/salomonis-archive/FASTQs/NCI-R01/POSEIDON/Tumors/RenalPelvis/bams'
tumor_type = 'RenalPelvis'

print('\n' + '='*60)
print(f'Re-running OptiType for: {tumor_type}')
print('='*60)

bam_count = count_bam_files(bam_dir)
print(f'  Found {bam_count} BAM files')

submit_optitype_jobs(bam_dir)

print('\n' + '='*60)
print('OptiType jobs submitted for RenalPelvis')
print('='*60)
