#!/usr/bin/env python3
"""
Automate HLA genotyping workflow for tumor bams/bams1 directories.
Runs the workflow described in HLA-scripts/README.md
"""

import os
import sys
import subprocess
import glob
import shutil
from pathlib import Path

# Configuration
POSEIDON_ROOT = "/data/salomonis-archive/FASTQs/NCI-R01/POSEIDON"
HLA_SCRIPTS_DIR = f"{POSEIDON_ROOT}/HLA-scripts"
TUMORS_DIR = f"{POSEIDON_ROOT}/Tumors"
SCRIPTS_TO_COPY = ["get_hla_all.py", "hla.sh", "run_optiplex_code3.sh"]


def find_bam_directories():
    """Find all bams and bams1 directories under Tumors."""
    bam_dirs = []
    for root, dirs, _ in os.walk(TUMORS_DIR):
        for d in dirs:
            if d in ["bams", "bams1"]:
                bam_dirs.append(os.path.join(root, d))
    return sorted(bam_dirs)


def copy_scripts(target_dir):
    """Copy HLA scripts to target directory."""
    print(f"  Copying scripts to {target_dir}")
    for script in SCRIPTS_TO_COPY:
        src = os.path.join(HLA_SCRIPTS_DIR, script)
        dst = os.path.join(target_dir, script)
        if not os.path.exists(src):
            print(f"    WARNING: {script} not found in {HLA_SCRIPTS_DIR}")
            continue
        try:
            shutil.copy(src, dst)  # Use copy instead of copy2 to avoid xattr issues
            os.chmod(dst, 0o755)
            print(f"    Copied {script}")
        except PermissionError:
            print(f"    Skipped {script} (already exists, permission denied)")


def count_bam_files(directory):
    """Count BAM files in directory."""
    return len(glob.glob(os.path.join(directory, "*.bam")))


def submit_chr6_extraction(directory):
    """Submit jobs to extract chromosome 6 reads from BAM files."""
    print(f"  Submitting chromosome 6 extraction jobs...")

    # Create logs and fastqs directories if they don't exist
    logs_dir = os.path.join(directory, "logs")
    fastqs_dir = os.path.join(directory, "fastqs")
    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(fastqs_dir, exist_ok=True)
    print(f"    Created logs and fastqs directories")

    bam_files = glob.glob(os.path.join(directory, "*.bam"))
    if not bam_files:
        print(f"    No BAM files found!")
        return False

    submitted = 0
    for bam in bam_files:
        bam_name = os.path.basename(bam)
        sample_name = os.path.splitext(bam_name)[0]

        # Build the actual command to run
        cmd = f"conda activate bio-cli && python3 /data/salomonis2/software/AltAnalyze/import_scripts/hla.py --i {bam} --o {fastqs_dir} && fd --exact-depth 1 --size -50b '{sample_name}_2.fastq.gz' {fastqs_dir} -x rm"

        # Submit directly to bsub with proper arguments
        try:
            result = subprocess.run(
                [
                    "bsub",
                    "-L", "/bin/bash",
                    "-W", "1:00",
                    "-n", "1",
                    "-R", "span[ptile=4]",
                    "-M", "16000",
                    "-o", f"{logs_dir}/%J.out",
                    "-e", f"{logs_dir}/%J.err",
                    "-J", sample_name,
                    "bash", "-lc", cmd
                ],
                cwd=directory,
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and "is submitted" in result.stdout:
                submitted += 1
            elif result.returncode != 0:
                print(f"    Failed {bam_name}: {result.stderr}")
        except Exception as e:
            print(f"    Error submitting {bam_name}: {e}")

    print(f"    Submitted {submitted}/{len(bam_files)} jobs")
    return submitted > 0


def submit_optitype_jobs(directory):
    """Submit OptiType jobs for fastq files."""
    print(f"  Submitting OptiType jobs...")

    fastq_dir = os.path.join(directory, "fastqs")
    if not os.path.exists(fastq_dir):
        print(f"    fastqs directory not found!")
        return False

    fastq_files = glob.glob(os.path.join(fastq_dir, "*_1.fastq.gz"))
    if not fastq_files:
        print(f"    No *_1.fastq.gz files found in fastqs/")
        return False

    # Create processed directory
    processed_dir = os.path.join(directory, "processed")
    os.makedirs(processed_dir, exist_ok=True)

    logs_dir = os.path.join(directory, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    sif_path = "/data/salomonis-archive/BAMs/NCI-R01/TCGA/TCGA-OV/optitype_container.sif"

    submitted = 0
    skipped = 0
    for file1 in fastq_files:
        file1_base = os.path.basename(file1)
        sample_name = file1_base.replace("_1.fastq.gz", "")
        file2 = file1.replace("_1.fastq.gz", "_2.fastq.gz")

        # Check if results already exist
        sample_processed_dir = os.path.join(processed_dir, sample_name)
        if os.path.exists(sample_processed_dir):
            result_files = glob.glob(os.path.join(sample_processed_dir, "*_result.tsv"))
            if result_files:
                skipped += 1
                continue

        # Create sample processed directory
        os.makedirs(sample_processed_dir, exist_ok=True)

        # Detect if this is paired-end or single-end
        # Check if _2.fastq.gz exists AND has meaningful content (> 50 bytes)
        is_paired_end = os.path.exists(file2) and os.path.getsize(file2) > 50

        # Create temporary wrapper script for this job
        wrapper_script = os.path.join(logs_dir, f"optitype_{sample_name}.sh")
        with open(wrapper_script, 'w') as f:
            if is_paired_end:
                file2_base = os.path.basename(file2)
                optitype_cmd = f"/usr/local/bin/OptiType/OptiTypePipeline.py -i fastqs/{file1_base} fastqs/{file2_base} --rna -v -o processed/{sample_name}"
            else:
                # Single-end mode - only pass _1.fastq.gz
                optitype_cmd = f"/usr/local/bin/OptiType/OptiTypePipeline.py -i fastqs/{file1_base} --rna -v -o processed/{sample_name}"

            f.write(f"""#!/bin/bash
                    module load singularity/3.7.0
                    cd {directory}
                    singularity exec -W /mnt -B {directory}:/mnt {sif_path} /bin/bash -c "cd /mnt && {optitype_cmd}"
                    """)
        os.chmod(wrapper_script, 0o755)

        # Submit the wrapper script to bsub
        try:
            result = subprocess.run(
                [
                    "bsub",
                    "-L", "/bin/bash",
                    "-W", "8:00",
                    "-M", "32000",
                    "-n", "4",
                    "-R", "span[hosts=1]",
                    "-o", f"{logs_dir}/OptiType_{sample_name}_%J.out",
                    "-e", f"{logs_dir}/OptiType_{sample_name}_%J.err",
                    "-J", f"OptiType_{sample_name}",
                    wrapper_script
                ],
                cwd=directory,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                submitted += 1
        except Exception as e:
            print(f"    Error submitting {sample_name}: {e}")

    if skipped > 0:
        print(f"    Skipped {skipped} samples (results already exist)")
    print(f"    Submitted {submitted}/{len(fastq_files)} jobs")
    return submitted > 0


def aggregate_results(directory):
    """Run get_hla_all.py to aggregate OptiType results."""
    print(f"  Aggregating HLA results...")
    try:
        result = subprocess.run(
            ["bash", "-lc", "conda activate bio-cli && python3 get_hla_all.py"],
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes for large cohorts
        )
        if result.returncode == 0:
            print(f"    Successfully aggregated results")
            return True
        else:
            print(f"    Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"    Error running get_hla_all.py: {e}")
        return False


def verify_results(directory, expected_count):
    """Verify aggregated_hla_genotypes.txt has expected number of samples."""
    output_file = os.path.join(directory, "aggregated_hla_genotypes.txt")
    if not os.path.exists(output_file):
        print(f"    ERROR: {output_file} not found!")
        return False

    with open(output_file) as f:
        lines = [l for l in f if l.strip() and not l.startswith("#")]
        # Subtract 1 for header if present
        sample_count = len(lines) - 1 if lines else 0

    print(f"    Found {sample_count} samples (expected {expected_count})")
    return sample_count == expected_count


def process_directory(bam_dir, step="all"):
    """Process a single bams/bams1 directory."""
    tumor_type = os.path.basename(os.path.dirname(bam_dir))
    dir_name = os.path.basename(bam_dir)
    print(f"\n{'='*60}")
    print(f"Processing: {tumor_type}/{dir_name}")
    print(f"{'='*60}")

    bam_count = count_bam_files(bam_dir)
    print(f"  Found {bam_count} BAM files")

    if bam_count == 0:
        print(f"  Skipping (no BAM files)")
        return

    if step in ["all", "copy"]:
        copy_scripts(bam_dir)

    if step in ["all", "extract"]:
        submit_chr6_extraction(bam_dir)

    if step in ["all", "optitype"]:
        submit_optitype_jobs(bam_dir)

    if step == "aggregate":
        aggregate_results(bam_dir)
        verify_results(bam_dir, bam_count)


def main():
    """Main workflow."""
    if len(sys.argv) > 1:
        step = sys.argv[1]
        if step not in ["copy", "extract", "optitype", "aggregate", "all"]:
            print("Usage: run_hla_workflow.py [copy|extract|optitype|aggregate|all]")
            print("\n  copy      - Copy scripts only (Step 1)")
            print("  extract   - Extract chromosome 6 reads (step 2)")
            print("  optitype  - Run OptiType (step 3)")
            print("  aggregate - Aggregate results (step 5-6)")
            print("  all       - Run all steps (default)")
            sys.exit(1)
    else:
        step = "all"

    print(f"HLA Genotyping Workflow - Step: {step}")
    print(f"Finding bams/bams1 directories...")

    bam_dirs = find_bam_directories()
    print(f"Found {len(bam_dirs)} directories\n")

    for bam_dir in bam_dirs:
        process_directory(bam_dir, step)

    print(f"\n{'='*60}")
    print(f"Workflow {step} completed for {len(bam_dirs)} directories")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()