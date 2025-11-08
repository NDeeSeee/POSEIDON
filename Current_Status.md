Big Picture – Remaining Work (Focus on Tumors!)

  Only Bulk_CellTypes/Gum+MouthOther, Controls/Tongue, and Controls/Esophagus, Controls/MouthFloor, Controls/RenalPelvis, Tumors/Esophagus, and
  Tumors/Larynx are fully “green” (SRA = sample list matches and FASTQs already match sample count). Everything else still needs more SRA
  downloads and/or FASTQ conversion.
  Here’s the remaining workload per cancer type (rows sorted as in the summary):
  • `Bulk_CellTypes/Pancreas`: 14 samples expected, 0 .sra, 11 FASTQ pairs (from earlier staging). Need all 14 .sra and to convert to complete
    FASTQs.
  • `Controls/Gallbladder`: 76 samples, 0 .sra, 76 FASTQ pairs (existing). Need 76 .sra (if we want reproducibility) to re-convert or archive
    properly.
  • `Controls/Gum+MouthOther`: 60 samples, 73 .sra (extra 21), 73 FASTQ pairs. Need to trim out non-matching .sra and close 8 missing sample
    SRRs.
  • `Controls/Larynx`: 13 samples, 0 .sra, 13 FASTQ pairs; same issue as Gallbladder (FASTQs present, but .sra missing).
  • `Controls/Pancreas`: 69 samples, 1 .sra, 64 FASTQs – so 68 missing SRA runs.
  • `Controls/Salivary`: 60 samples, 53 .sra, 0 FASTQs – 7 missing SRRs & full FASTQ conversion pending once .sra align; no FASTQ yet.
  • `Premalignant/Esophagus`: 213 samples, 37 .sra, no FASTQ – 176 SRRs missing.
  • `Premalignant/Gum+MouthOther`: 103 samples, 0 .sra, no FASTQ – entire .sra dataset missing.
  • `Tumors/Gallbladder`: 78 samples, 13 .sra, 101 FASTQs (looks like extra conversions). Need 65 more .sra to match the sample list; also need
    to reconcile extra FASTQs.
  • `Tumors/Gum+MouthOther`: 330 samples, 376 .sra, 0 FASTQ – 22 missing sample SRRs, 68 extra .sra; FASTQ conversion pending after cleanup.
  • `Tumors/LungLargeCell`: 26 samples, 12 .sra, 0 FASTQ – 14 missing SRRs.
  • `Tumors/MouthFloor`: 11 samples, 4 .sra, 0 FASTQ – 11 missing, plus 4 extra .sra.
  • `Tumors/Oropharyngeal`: 242 samples, 32 .sra, 0 FASTQ – 210 SRRs missing.
  • `Tumors/Pancreas`: 693 samples, 32 .sra, 858 FASTQs (huge discrepancy) – 661 SRRs missing; multiple FASTQs obviously do not match SRA
    counts.
  • `Tumors/RenalPelvis`: 64 samples, 55 .sra, 0 FASTQ – 13 missing, 4 extra.
  • `Tumors/Salivary`: 195 samples, 209 .sra, 0 FASTQ – 13 missing, 27 extra.
  • `Tumors/SmallCellLung`: 103 samples, 65 .sra, 0 FASTQ – 64 missing, 26 extra.
  • `Tumors/Tongue`: 60 samples, 47 .sra, 0 FASTQ – 13 missing (we’re actively downloading these now).


  Recommended Focus (while queue is busy)

  1. Finish Tumors/Tongue: 13 SRRs left (very close).
  2. Controls/Gum+MouthOther: reconcile 8 missing + trim 21 extras (should be manageable); FASTQs already exist, so just cleanup.
  3. Controls/Salivary: fetch 7 missing .sra, prepare for eventual conversion.
  4. Tumors/RenalPelvis: fetch 13 missing, remove 4 extra.
  5. Gum+MouthOther Tumors: bigger job (22 missing, 68 extra) but next priority once the smaller ones stabilise.
  6. Pancreas Tumors: large but extremely important—over 600 SRRs missing; may need dedicated tooling or confirm controlled-access. This might
     be a major multi-day effort.

  Let me know which cancer type you’d like to tackle next after Tongue Tumors; I can begin building the missing SRR lists and plan the downloads
  immediately.


  Got it. Here’s how I’ll proceed under the updated definition:
  1. Catalog the Reference Lists
    • For every directory that contains a sample_list.txt and one or more *-SRA*.txt files (including *-SRA2.txt), extract the SRR IDs from both
       sources.
    • Treat the *-SRA*.txt files in that directory as a combined set (no merging into a single file, just union for comparison).
  2. Build a New Discrepancy Table
    • Produce discrepancies.csv with columns such as directory, srr_id, in_sample_list, in_sra_reference.
    • This flags SRRs that are listed only in the sample list, only in the SRA reference(s), or in both.
  3. Prepare Download Targets
    • For each directory, compute the intersection of sample-list SRRs and SRA-reference SRRs; that becomes the “authoritative” set to
      download/convert.
    • For these intersected IDs, note which .sra files are still missing so we can fetch them explicitly.
  4. Download All Required `.sra` Files
    • Iterate through the intersected SRR list, running prefetch -X 35000000 (or the controlled-access workflow where needed).
    • Normalize each download so the .sra ends up directly in the correct directory.
  5. FASTQ Conversion
    • Once the intersected .sra files are present, run fdump.sh sample_list.txt.
    • The script will skip SRRs that already have FASTQs and convert the rest; we’ll monitor for cluster slot limits and resume if we hit any.
  6. Document Progress
    • After conversions complete, append an update to Current_Status.md summarizing the downloads, conversions, and any outstanding
      discrepancies.

  If that matches what you want, I’ll start with step 1 (extracting SRRs from both sources and building discrepancies.csv).

## Overall Processing Status 

| Category | CancerType | Expected | SRRs | FASTQ pairs | BAMs | SNAF | Notes |
|---|---:|---:|---:|---:|---:|---:|---|
| Bulk_CellTypes | Gum+MouthOther | 19 | 19 | 19 | 0 | N/A |  |
| Bulk_CellTypes | Pancreas | 9 | 0 | 11 | 0 | N/A | FASTQs exist, SRAs missing (reproducibility risk) |
| Controls | Esophagus | 31 | 32 | 32 | 0 | N/A |  |
| Controls | Gallbladder | 76 | 73 | 76 | 0 | N/A |  |
| Controls | Gum+MouthOther | 60 | 74 | 74 | 0 | N/A | dbGaP blocks: 7 |
| Controls | Larynx | 13 | 11 | 13 | 0 | N/A |  |
| Controls | MouthFloor | 2 | 2 | 2 | 0 | N/A |  |
| Controls | Pancreas | 69 | 64 | 64 | 0 | N/A | dbGaP blocks: 5 |
| Controls | RenalPelvis | 5 | 4 | 4 | 0 | N/A |  |
| Controls | Salivary | 45 | 54 | 0 | 0 | N/A |  |
| Controls | Tongue | 13 | 20 | 20 | 0 | N/A |  |
| Premalignant | Esophagus | 213 | 37 | 0 | 0 | N/A |  |
| Premalignant | Gum+MouthOther | 103 | 0 | 0 | 0 | N/A |  |
| Tumors | Esophagus | 21 | 0 | 21 | 0 | N/A | dbGaP blocks: 4; FASTQs exist, SRAs missing (reproducibility risk) |
| Tumors | Gallbladder | 114 | 0 | 114 | 20 | N/A | BAMs present (cleanup pending); FASTQs exist, SRAs missing (reproducibility risk) |
| Tumors | Gum+MouthOther | 330 | 378 | 0 | 0 | N/A | dbGaP blocks: 20 |
| Tumors | Larynx | 17 | 17 | 17 | 0 | N/A |  |
| Tumors | LungLargeCell | 26 | 12 | 0 | 0 | N/A | dbGaP blocks: 14 |
| Tumors | MouthFloor | 11 | 15 | 0 | 0 | N/A |  |
| Tumors | Oropharyngeal | 238 | 32 | 0 | 0 | N/A | dbGaP blocks: 204 |
| Tumors | Pancreas | 696 | 696 | 858 | 0 | N/A | dbGaP blocks: 10 |
| Tumors | RenalPelvis | 65 | 57 | 0 | 0 | N/A | dbGaP blocks: 9 |
| Tumors | Salivary | 195 | 213 | 0 | 0 | N/A | dbGaP blocks: 9 |
| Tumors | SmallCellLung | 103 | 66 | 0 | 0 | N/A | dbGaP blocks: 62 |
| Tumors | Tongue | 55 | 60 | 0 | 0 | N/A |  |

Totals:
- Expected samples: 2533
- SRRs downloaded: 1936
- FASTQ pairs: 1315
- BAMs present: 20

Notes
- Counts reflect on-disk state at generation time; SRAs/FASTQs are counted only at the cancer-type directory (not nested caches).
- SNAF: Not tracked via on-disk markers in this repo; left as N/A.
- dbGaP blocks: parsed from the latest download log only (`logs/sra_download_20251028_234318.log`). Additional older logs may contain more blocks.