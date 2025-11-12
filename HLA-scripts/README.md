# Convert this into .md format to copy-paste

## Steps

1. Copy scripts in this directory to the tumor bams or bams1 file directory.
```
   /data/salomonis-archive/FASTQs/NCI-R01/POSEIDON/HLA-scripts
```

2. cd to the bams directory

3. Generate fastq files for chromosome 6 reads from an aligned BAM file (requisite for OptiType)
```bash
   for i in *.bam; do ./hla.sh $i | bsub; done
```
   This creates a folder named `fastq` that has chromosome 6 fastq files. Will take only a few minutes.

4. Run optitype on the generated fastq files:
```bash
   for f in fastqs/*_1.fastq.gz; do ./run_optiplex_code3.sh $f | bsub; done
```

5. Combine the OptiType results and check to make sure all samples are present in the output
```bash
   python3 get_hla_all.py
```

6. Confirm `aggregated_hla_genotypes.txt` has the same number of samples as BAM files


# Cancers:
- AnusAnorectum: 215 BAMs
- Bones+Joints: 27 BAMs
- Esophagus: 19 BAMs
- Gallbladder: 108 BAMs
- Gum+MouthOther: 244 BAMs
- HRposHER2posBreast: 8 BAMs
- Larynx: 17 BAMs
- LungLargeCell: 12 BAMs
- MeningiomaBrain+CNS: 238 BAMs
- Mesothelioma: 191 BAMs
- MouthFloor: 36 BAMs
- Oropharyngeal: 30 BAMs
- Pancreas: 292 BAMs
- RenalPelvis: 46 BAMs
- Salivary: 147 BAMs
- SmallCellLung: 30 BAMs
- SmallIntestine: 81 BAMs
- Tongue: 67 BAMs
- Vagina: 31 BAMs