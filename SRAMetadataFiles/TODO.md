# POSEIDON Project TODO - Cancer Genomics Data Processing Pipeline

## Project Overview
**POSEIDON** is an NCI-R01 funded cancer genomics project focused on RNA-seq data analysis across multiple cancer types. The project involves downloading, processing, and analyzing bulk RNA-seq data from SRA, with samples organized into Controls, Premalignant, and Tumors categories.

## Current Status Summary
- **Total Cancer Types**: 15+ (Esophagus, Gallbladder, Pancreas, Mouth, Larynx, etc.)
- **Data Processing Pipeline**: SRA Download → FASTQ Conversion → STAR 2-pass Alignment
- **Current Phase**: Data download and initial processing (incomplete)

## Critical Issues Requiring Immediate Attention

### 1. Data Completeness Issues
- [ ] **Pancreas samples incomplete**: Missing samples need to be downloaded using Pancreas-SRA2 and sratoolkit_controlled4.sh
- [ ] **Download verification needed**: Only Gallbladder samples verified complete; all other directories need validation
- [ ] **Esophagus Adenocarcinoma**: Not tracked in download tracker, needs systematic review

### 2. Data Cleanup Tasks
- [ ] **Delete BAM folders**: Remove bam folders in all subdirectories due to BioSampleID issues and incomplete STAR alignments
- [ ] **File format corrections**: Convert Vagina metadata from CSV to Excel format (metadata annotations lost)
- [ ] **Directory reorganization**: Clean up mixed file types and incomplete processing artifacts

### 3. Metadata and Annotation Issues
- [ ] **Vagina metadata**: Re-annotate tumor samples (metadata lost during CSV conversion)
- [ ] **Esophagus cancer types**: Verify squamous cell vs adenocarcinoma classification
- [ ] **Gum+MouthOther**: Reconcile SRA file count vs sample list discrepancies
- [ ] **Mesothelioma**: Complete download of non-controlled access samples

## Action Plan by Priority

### Phase 1: Critical Data Issues (Week 1)
1. **Complete Pancreas downloads** using existing scripts
2. **Verify download completeness** for all cancer types
3. **Clean up BAM directories** to prevent processing conflicts
4. **Fix Vagina metadata** format and re-annotate

### Phase 2: Data Quality Control (Week 2)
1. **Systematic download verification** across all directories
2. **Reconcile sample counts** with metadata files
3. **Validate file integrity** for downloaded SRA files
4. **Complete missing downloads** identified in verification

### Phase 3: Pipeline Optimization (Week 3)
1. **Standardize metadata formats** across all cancer types
2. **Implement quality control checks** for download completeness
3. **Document processing status** for each cancer type
4. **Prepare for downstream analysis** phase

## Technical Notes
- **SRA Toolkit Version**: 3.1.1 (prefetch), 2.10.4 (fastq-dump)
- **Alignment Tool**: STAR 2-pass with GRCh38 reference
- **Compute Resources**: LSF job scheduler with 4-8 cores, 10-128GB RAM
- **Storage**: Organized by cancer type and sample category

## Communication
- **Team Members**: Trisha, Taylor, Valerii
- **Next Review**: Schedule systematic validation with Valerii
- **Status Updates**: Weekly progress reports on download completeness

## Success Metrics
- [ ] 100% download completeness for all cancer types
- [ ] Clean, organized directory structure
- [ ] Complete and accurate metadata for all samples
- [ ] Ready for downstream RNA-seq analysis