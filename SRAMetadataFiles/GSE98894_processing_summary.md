# GSE98894 Small Intestine Processing Summary

## Dataset Information
- **GEO Accession**: GSE98894
- **Study**: Expression profile of Gastro-Entero-Pancreatic Neuroendocrine Tumors (GEP-NET)
- **Total samples in study**: 212 (113 pancreas, 81 small intestine, 18 rectum)

## Processing Results
- **Filtered for**: Small Intestine Neuroendocrine Tumors (SI-NET) only
- **Output file**: `SmallIntestine_GSE98894.xlsx`
- **Total samples**: 81

### Sample Distribution
- **Primary tumors**: 44
- **Liver metastases**: 28
- **Lymph node metastases**: 8
- **Mesenteric metastasis**: 1

### Classification
- **top_label**: Tumor (all samples)
- **origin**: small intestine (all samples)
- **tumor_type**: primary, liver metastasis, lymph node metastasis, or mesenteric metastasis

## Files Created
1. `GSE98894_SmallIntestine.tsv` - Enriched TSV with metadata (39 KB)
2. `SmallIntestine_GSE98894.xlsx` - Excel workbook with Tumors sheet (27 KB)
3. `process_gse98894.py` - Processing script for future use

## Excel File Structure
The xlsx file contains one sheet:
- **Tumors**: 81 samples classified as tumors from small intestine origin

All samples include full SRA metadata plus GEO-derived classification fields.
