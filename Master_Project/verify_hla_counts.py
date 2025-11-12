#!/usr/bin/env python3
"""Verify aggregated_hla_genotypes.txt sample counts match BAM file counts."""

import os
import glob

TUMORS_DIR = "/data/salomonis-archive/FASTQs/NCI-R01/POSEIDON/Tumors"

def count_bams(directory):
    """Count BAM files in directory."""
    return len(glob.glob(os.path.join(directory, "*.bam")))

def count_aggregated_samples(agg_file):
    """Count samples in aggregated_hla_genotypes.txt (excluding header)."""
    if not os.path.exists(agg_file):
        return 0
    with open(agg_file) as f:
        lines = [l for l in f if l.strip() and not l.startswith("#")]
        return len(lines) - 1 if lines else 0

def main():
    print(f"{'Directory':<30} {'BAMs':<8} {'Aggregated':<12} {'Status'}")
    print("=" * 70)
    
    total_bams = 0
    total_aggregated = 0
    perfect_match = 0
    
    # Find all bams/bams1 directories
    for root, dirs, _ in os.walk(TUMORS_DIR):
        for d in dirs:
            if d in ["bams", "bams1"]:
                bam_dir = os.path.join(root, d)
                tumor_type = os.path.basename(os.path.dirname(bam_dir))
                dir_name = f"{tumor_type}/{d}"
                
                bam_count = count_bams(bam_dir)
                agg_file = os.path.join(bam_dir, "aggregated_hla_genotypes.txt")
                agg_count = count_aggregated_samples(agg_file)
                
                total_bams += bam_count
                total_aggregated += agg_count
                
                status = "✓ MATCH" if bam_count == agg_count else f"✗ MISSING {bam_count - agg_count}"
                if bam_count == agg_count:
                    perfect_match += 1
                
                print(f"{dir_name:<30} {bam_count:<8} {agg_count:<12} {status}")
    
    print("=" * 70)
    print(f"{'TOTAL':<30} {total_bams:<8} {total_aggregated:<12} "
          f"{perfect_match} perfect matches")
    print(f"\nSuccess rate: {total_aggregated}/{total_bams} ({100*total_aggregated/total_bams:.1f}%)")

if __name__ == "__main__":
    main()
