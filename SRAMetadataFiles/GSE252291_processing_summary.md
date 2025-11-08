# GSE252291 Meningioma Processing Summary

## Dataset Information
- **GEO Accession**: GSE252291
- **Study**: Meningioma transcriptomic landscape demonstrates novel subtypes with regional associated biology and patient outcome
- **Institution**: University of Washington / Fred Hutchinson Cancer Center
- **Total samples**: 279

## Processing Results
- **Output file**: `MeningiomaBrain+CNS.xlsx`
- **Total samples**: 279 meningioma tumor samples

### Sample Characteristics
- **Tissue origin**: Brain (all 279 samples)
- **Disease state**: Meningioma tumor (all samples)
- **Sample type**: Fresh frozen tumor tissue

### Classification
- **top_label**: Tumor (all samples)
- **origin**: brain and CNS (all samples)
- **sample_type**: meningioma (all samples)

## Files Created
1. `GSE252291_MeningiomaBrain+CNS.tsv` - Enriched TSV with metadata (23 KB)
2. `MeningiomaBrain+CNS.xlsx` - Excel workbook with Tumors sheet (18 KB)
3. `process_gse252291.py` - Processing script for future use

## Excel File Structure
The xlsx file contains one sheet:
- **Tumors**: 279 meningioma tumor samples from brain tissue

All samples include GEO metadata and classification fields for integration with the POSEIDON project workflow.

## Notes
- This dataset includes meningiomas of various WHO grades and recurrence statuses
- Part of a larger transcriptomic landscape study combining 13 datasets totaling ~1,300 meningiomas
- All samples sequenced at UW/FHCC between 1998-2023
