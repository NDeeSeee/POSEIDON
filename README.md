# POSEIDON: Comprehensive Cancer Genomics Data Processing Pipeline

## Project Overview

**POSEIDON** is an NCI-R01 funded cancer genomics research project focused on large-scale RNA-seq data analysis across multiple cancer types. The project implements a comprehensive pipeline for downloading, processing, and analyzing bulk RNA-seq data from SRA/ENA databases, with samples organized into four main categories: Controls, Tumors, Premalignant, and Bulk_CellTypes.

## Project Structure

```
POSEIDON/
├── SRAMetadataFiles/           # Excel metadata files for each cancer type
│   ├── Pancreas.xlsx          # Contains 4 sheets: Tumors, Controls, Bulk_CellTypes, Premalignant
│   ├── Gallbladder-SRA.xlsx   # Gallbladder cancer metadata
│   ├── Esophagus.xlsx         # Esophageal cancer metadata
│   └── ...                    # Other cancer type metadata files
├── Controls/                   # Control samples organized by cancer type
│   ├── Pancreas/              # Pancreas control samples
│   │   ├── sample_list.txt    # BioSample -> FASTQ mapping
│   │   ├── sratoolkit.sh      # SRA download script
│   │   ├── fdump.sh           # FASTQ conversion script
│   │   ├── star_2pass-paired.sh # STAR alignment script
│   │   ├── *.fastq.gz         # FASTQ files
│   │   └── bams/              # BAM files (to be deleted)
│   └── ...                    # Other cancer control directories
├── Tumors/                    # Tumor samples organized by cancer type
│   ├── Pancreas/              # Pancreas tumor samples
│   │   ├── sample_list.txt    # BioSample -> FASTQ mapping
│   │   ├── *.fastq.gz         # FASTQ files
│   │   └── bams/              # BAM files (to be deleted)
│   └── ...                    # Other cancer tumor directories
├── Premalignant/              # Pre-malignant samples
├── Bulk_CellTypes/            # Bulk cell type samples
└── ValeriiGitRepo/           # Alternative automated pipeline scripts
    ├── scripts/               # Python scripts for automated processing
    └── README.md             # Documentation for automated pipeline
```

## Data Processing Pipeline

### Current Manual Pipeline (Primary Approach)

The project currently uses a **manual, Excel-based approach** for sample selection and organization:

#### 1. **Metadata Preparation**
- **Input**: Excel files in `SRAMetadataFiles/` with 4 sheets per cancer type:
  - `Tumors`: Malignant samples
  - `Controls`: Healthy/control samples  
  - `Bulk_CellTypes`: Bulk cell type samples
  - `Premalignant`: Pre-malignant samples (e.g., Barrett's esophagus)

#### 2. **Sample List Generation**
- **Script**: `ValeriiGitRepo/scripts/GEO_sampleSetup_enhanced_VP.py`
- **Input**: Excel metadata file (e.g., `Pancreas.xlsx`)
- **Output**: `sample_list.txt` files in each category directory
- **Format**: `BioSample_ID\tFASTQ_R1\tFASTQ_R2`
- **Example**:
  ```
  SAMN37100986	SRR25716763_1.fastq.gz	SRR25716763_2.fastq.gz
  SAMN37100987	SRR25716765_1.fastq.gz	SRR25716765_2.fastq.gz
  ```

#### 3. **SRA Download**
- **Script**: `sratoolkit.sh` (per cancer type directory)
- **Tool**: SRA Toolkit `prefetch`
- **Input**: `sample_list.txt` or SRA list file
- **Output**: `.sra` files

#### 4. **FASTQ Conversion**
- **Script**: `fdump.sh` (per cancer type directory)
- **Tool**: SRA Toolkit `fastq-dump`
- **Input**: `.sra` files
- **Output**: `*_1.fastq.gz` and `*_2.fastq.gz` files

#### 5. **STAR Alignment**
- **Script**: `star_2pass-paired.sh` (per cancer type directory)
- **Tool**: STAR 2-pass alignment
- **Reference**: GRCh38
- **Input**: FASTQ files
- **Output**: BAM files (stored in `bams/` directories)

#### 6. **Downstream Analysis**
- **Junction Analysis**: `/software/LabShellScripts/RunAltAnalyze.from.bams/index-junction_hg38.sh`
- **AltAnalyze**: `/software/LabShellScripts/RunAltAnalyze.from.bams/AltAnalyze.sh`

### Alternative Automated Pipeline (ValeriiGitRepo)

The `ValeriiGitRepo` contains an **automated, database-driven approach**:

#### 1. **Cancer Type Search**
- **Script**: `cancer_type_search.py`
- **Function**: Search SRA/ENA databases by cancer type name
- **Input**: Cancer type (e.g., "pancreatic cancer")
- **Output**: List of SRR IDs

#### 2. **Comprehensive Metadata Collection**
- **Script**: `comprehensive_metadata_pipeline.sh`
- **Sources**: ENA (192 fields), RunInfo, BioSample, BioProject, GEO, SRA XML, ffq
- **Output**: `comprehensive_metadata.tsv` (238+ columns)

#### 3. **Metadata Merging**
- **Script**: `merge_metadata_maximum.py`
- **Function**: Merge all metadata sources into unified dataset
- **Output**: `ultimate_metadata.tsv`

#### 4. **Cancer Classification**
- **Script**: `cancer_classification.py`
- **Function**: Classify samples into tumor/normal/cell line categories
- **Features**: Cell line reference database integration
- **Output**: `classified_metadata.tsv`

#### 5. **FASTQ Download by Category**
- **Script**: `download_fastq_by_category.py`
- **Function**: Download FASTQ files organized by classification
- **Categories**: Tumor, Pre-malignant, Normal, Cell_line, Unknown

## Current Project Status

### Data Completeness Issues
- **Pancreas samples incomplete**: Missing samples need to be downloaded using `Pancreas-SRA2` and `sratoolkit_controlled4.sh`
- **Download verification needed**: Only Gallbladder samples verified complete
- **Esophagus Adenocarcinoma**: Not tracked in download tracker

### Data Organization Issues
- **BAM directories need cleanup**: 5.5TB of BAM files need deletion due to:
  - BioSampleID issues during processing
  - Incomplete STAR alignments (samples added after alignment started)
  - Mixed processing states

### Metadata Issues
- **Vagina metadata**: Lost annotations due to CSV conversion error
- **File format inconsistencies**: Some metadata files in wrong format
- **Sample count discrepancies**: Some directories have more SRA files than listed samples

## Technical Specifications

### Software Versions
- **SRA Toolkit**: 3.1.1 (prefetch), 2.10.4 (fastq-dump)
- **STAR**: 2.4.0h (2-pass alignment)
- **Reference Genome**: GRCh38
- **Compute Resources**: LSF job scheduler, 4-8 cores, 10-128GB RAM

### Data Storage
- **Total Size**: ~5.5TB of BAM files (to be deleted)
- **Organization**: By cancer type and sample category
- **File Formats**: SRA, FASTQ, BAM, Excel metadata

## Script Documentation

### Core Processing Scripts

#### `GEO_sampleSetup_enhanced_VP.py`
- **Purpose**: Generate sample_list.txt from Excel metadata
- **Input**: Excel file with 4 sheets (Tumors, Controls, Bulk_CellTypes, Premalignant)
- **Output**: sample_list.txt files in POSEIDON/<sheet>/<cancer_type>/
- **Usage**: `python GEO_sampleSetup_enhanced_VP.py metadata_file.xlsx`

#### `sratoolkit.sh`
- **Purpose**: Download SRA files using prefetch
- **Input**: SRA list file
- **Output**: .sra files
- **Usage**: `./sratoolkit.sh | bsub`

#### `fdump.sh`
- **Purpose**: Convert SRA to FASTQ
- **Input**: .sra files
- **Output**: *_1.fastq.gz, *_2.fastq.gz files
- **Usage**: `for i in *.sra; do ./fdump.sh $i | bsub; done`

#### `star_2pass-paired.sh`
- **Purpose**: STAR 2-pass alignment
- **Input**: FASTQ files
- **Output**: BAM files
- **Usage**: `for i in *1.fastq.gz; do bash star_2pass-paired.sh $i | bsub; done`

### Alternative Pipeline Scripts

#### `cancer_type_search.py`
- **Purpose**: Search SRA/ENA for cancer types
- **Input**: Cancer type name
- **Output**: SRR ID list
- **Usage**: `python cancer_type_search.py -c "pancreatic cancer" -o output.txt`

#### `merge_metadata_maximum.py`
- **Purpose**: Merge all metadata sources
- **Input**: Raw metadata files
- **Output**: Comprehensive metadata TSV
- **Usage**: `python merge_metadata_maximum.py -i raw/ -o ultimate_metadata.tsv`

#### `cancer_classification.py`
- **Purpose**: Classify samples by type
- **Input**: Comprehensive metadata
- **Output**: Classified metadata
- **Usage**: `python cancer_classification.py -i metadata.tsv -o classified.tsv`

#### `download_fastq_by_category.py`
- **Purpose**: Download FASTQ by classification
- **Input**: Classified metadata
- **Output**: Organized FASTQ files
- **Usage**: `python download_fastq_by_category.py -i classified.tsv -o fastq_downloads/`

## Recommended Workflow

### Phase 1: Data Cleanup (Immediate)
1. **Delete BAM directories** across all cancer types (5.5TB cleanup)
2. **Verify download completeness** for all cancer types
3. **Fix metadata format issues** (Vagina CSV → Excel)
4. **Complete missing downloads** (Pancreas samples)

### Phase 2: Pipeline Standardization
1. **Choose primary approach**: Manual Excel-based vs Automated database-driven
2. **Standardize metadata formats** across all cancer types
3. **Implement quality control checks**
4. **Document processing status** for each cancer type

### Phase 3: Downstream Analysis
1. **Re-run STAR alignments** with clean data
2. **Execute junction analysis** pipeline
3. **Run AltAnalyze** for alternative splicing analysis
4. **Prepare for statistical analysis**

## Critical Decisions Required

1. **Primary Pipeline**: Should the project use the manual Excel-based approach or switch to the automated database-driven approach?

2. **BAM Cleanup**: Confirm deletion of 5.5TB of BAM files before proceeding with fresh alignments.

3. **Sample Completeness**: How to handle incomplete downloads and missing samples?

4. **Metadata Standardization**: How to reconcile differences between manual curation and automated classification?

## Success Metrics

- [ ] 100% download completeness for all cancer types
- [ ] Clean, organized directory structure
- [ ] Complete and accurate metadata for all samples
- [ ] Successful STAR alignments for all samples
- [ ] Ready for downstream RNA-seq analysis

## Team and Communication

- **Primary Team**: Trisha, Taylor, Valerii
- **Next Review**: Schedule systematic validation with Valerii
- **Status Updates**: Weekly progress reports on download completeness

---

*This README provides a comprehensive overview of the POSEIDON project structure, data processing pipeline, and current status. It should be updated as the project progresses and decisions are made about the preferred workflow approach.*