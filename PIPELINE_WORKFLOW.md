# CTU Automated PDF Extraction Pipeline - How It Works

## Quick Start

```bash
# Run the full pipeline
python main.py

# Or run test mode (processes only 1 PDF)
python test_main_skip_download.py
```

---

## Pipeline Overview

The pipeline extracts structured data from Indian government energy sector PDFs and consolidates it into a multi-sheet Excel report. It runs in 4 sequential phases:

```
Phase 1: Web Scraping → Phase 2: PDF Download → Phase 3: Data Extraction → Phase 4: Excel Output
```

---

## Phase 1: Web Scraping

**What happens:** The pipeline scrapes government websites to find PDF download links.

**How it works:**
1. Reads `SHEET_CONFIG` from `config.py` to determine which data sources are needed
2. Only scrapes required sources (e.g., if "Data to be captured" sheet needs SN3 & SN4, only those are scraped)
3. For each source, uses BeautifulSoup4 to parse HTML and extract PDF links
4. Filters links by patterns (e.g., "connectivity", "RE", "renewable")

**Output:** Dictionary mapping source IDs to lists of PDF URLs
```
{
  "SN3": ["http://example.com/report1.pdf", "http://example.com/report2.pdf"],
  "SN4": ["http://example.com/capacity.pdf"]
}
```

---

## Phase 2: PDF Download

**What happens:** Downloads PDFs into organized source-specific folders.

**How it works:**
1. Creates folder structure: `downloaded_pdfs/SN3/`, `downloaded_pdfs/SN4/`, etc.
2. For each PDF URL:
   - Generates sanitized filename
   - Checks if file already exists (skips if yes)
   - Downloads using streaming to handle large files
   - Retries up to 3 times on failure

**Key feature:** Incremental downloads - only fetches new PDFs, skips existing ones

**Folder structure:**
```
downloaded_pdfs/
├── SN3/
│   └── 175747952599June 25_RE.pdf
├── SN4/
│   └── capacity_report.pdf
```

---

## Phase 3: Data Extraction (Core Processing)

**What happens:** Extracts structured data from each PDF using a 3-tier extraction strategy.

### 3.1 Sheet-by-Sheet Processing

The pipeline processes each Excel sheet independently:
- Reads the sheet's configuration from `SHEET_CONFIG`
- Gets list of required sources (e.g., ["SN3", "SN4"])
- Gets the extraction prompt for that sheet
- Processes all PDFs from those sources

### 3.2 Per-PDF Processing with 3-Tier Extraction

For each PDF file, the pipeline tries extraction methods in priority order:

#### **TIER 1: Camelot Table Extraction** (Fastest, Most Accurate)
- **When:** PDF contains structured tables
- **How:**
  1. Camelot detects table boundaries using 'lattice' flavor (grid lines)
  2. Extracts 14 tables spanning multiple pages
  3. **Smart header detection:** Finds header row in Table 1 by matching keywords (sl. no, application, developer, etc.)
  4. **Unified headers:** Uses Table 1's headers for all 14 tables (they're one continuous table split across pages)
  5. Normalizes headers using `field_mappings.py` (e.g., "Sl. No" → "sr_no")
  6. Skips first 2 rows of Tables 2-14 (page breaks/continuation markers)
  7. Concatenates all tables into single DataFrame
  8. Converts to list of dictionaries (records)

**Example flow:**
```python
Table 1: Row 2 = ["Sl. No", "Application ID", ...] ← Headers detected here
         Rows 3-48 = Data

Table 2: Row 0-1 = Page break markers (skipped)
         Row 2+ = Data (uses Table 1 headers)

...continues for Tables 3-14

Result: 787 records with 10 normalized columns
```

#### **TIER 2: PyMuPDF Text Extraction** (Fallback for digital PDFs)
- **When:** No tables found by Camelot
- **How:**
  1. Extracts raw text using PyMuPDF (fitz)
  2. Splits text into 6000-character chunks with 100-char overlap
  3. Sends each chunk to Hugging Face Transformers LLM (google/gemma-3-4b-it)
  4. LLM extracts structured data using sheet-specific prompts
  5. Aggregates records from all chunks

#### **TIER 3: Docling OCR** (Fallback for scanned PDFs)
- **When:** Insufficient text extracted by PyMuPDF
- **How:**
  1. Uses Docling + Tesseract OCR to extract text from images
  2. Same LLM processing as Tier 2

### 3.3 Field Normalization & Region Inference

After extraction:
1. **Header normalization:** Maps PDF column variations to canonical names
   - "Sl. No" / "Serial No" / "S.No" → "sr_no"
   - "Application ID" / "App ID" → "application_id"
2. **Region inference:** Auto-fills missing region from state
   - Maharashtra → WR (Western Region)
   - Rajasthan → NR (Northern Region)

### 3.4 Parallel Processing

PDFs are processed in parallel using ThreadPoolExecutor (2 workers) to speed up extraction.

---

## Phase 4: Excel Output

**What happens:** Writes all extracted data to a multi-sheet Excel file.

**How it works:**

### 4.1 CSV Intermediate Output
First saves data to CSV for validation:
```
extraction_output/
└── Data_to_be_captured_extracted_data.csv
```

### 4.2 Excel Writing with Template Alignment
1. **Loads template:** `Connectivity Application Data.xlsx`
2. **Reindexes columns:** Matches extracted data columns to template's canonical field order
3. **Fills missing columns:** Any template column not in extracted data becomes None/blank
4. **Writes data:** 
   - If output file doesn't exist: Copies template, writes data starting at row 3, column B
   - If output file exists: Appends new data to existing sheet

**Template structure:**
```
Row 1: Empty
Row 2: Headers (Sr.no., Region, State, Substation, ...)
Row 3+: Data rows
```

### 4.3 Final Output
```
Connectivity_Application_Data_OUTPUT2.xlsx
├── Data to be captured (787 rows)
├── RE Potential
├── Margin
├── Transformation Capacity
└── Element Status
```

---

## Key Technical Details

### Data Flow Example (Camelot Path)

```
PDF File (14 tables)
    ↓
Camelot Extraction
    ↓
Table 1: Detect headers at row 2 ["Sl. No", "Application ID", ...]
    ↓
Normalize headers: ["sr_no", "application_id", "name_of_developers", ...]
    ↓
Tables 2-14: Skip first 2 rows, apply Table 1 headers
    ↓
Concatenate all tables → 787 records × 10 columns
    ↓
Infer missing regions from state
    ↓
Convert to records: [{sr_no: 1, application_id: "2200001878", ...}, ...]
    ↓
Save to CSV (validation)
    ↓
Reindex to template column order (43 columns)
    ↓
Write to Excel starting at row 3, column B
    ↓
Final: 789 total rows (2 header rows + 787 data rows)
```

### Why the Camelot Fix Was Critical

**Problem:** Originally, each of the 14 tables was treated independently:
- Table 1 header at row 2 ✓
- Table 2 treated row 0 as headers → **DATA VALUES became column names**
- Result: 107 garbage columns, only 46 rows survived after deduplication

**Solution:** Recognize that all 14 tables share the same headers:
- Extract headers once from Table 1
- Apply to all subsequent tables
- Result: 787 records with 10 clean columns

---

## Configuration Files

### `config.py`
Defines:
- `DATA_SOURCES`: URLs of government websites (SN1-SN14)
- `SHEET_CONFIG`: Maps each Excel sheet to its sources and extraction prompt
- `HF_MODEL`: LLM model name ("google/gemma-3-4b-it")

### `field_mappings.py`
Contains:
- `HEADER_MAPPINGS`: Dictionary mapping PDF header variations to canonical names
- `normalize_header()`: Function that cleans and normalizes headers
- Handles periods, newlines, underscores, hyphens

### `prompts.py`
Contains optimized prompts for LLM extraction, telling the model what fields to extract and how to structure the output.

---

## Performance Characteristics

- **Camelot extraction:** ~2 seconds per PDF (fastest)
- **LLM extraction:** ~30-60 seconds per PDF (CPU) / ~10-20 seconds (GPU)
- **Parallel processing:** 2 workers = ~50% faster than sequential
- **Memory usage:** 2-4 GB (Camelot) / 8-16 GB (LLM with Transformers)

---

## Test Mode vs Production Mode

### `test_main_skip_download.py` (Test Mode)
- Skips Phases 1-2 (scraping & downloading)
- Processes only 1 PDF from `downloaded_pdfs/SN3/`
- Only processes "Data to be captured" sheet
- Faster iteration for testing (completes in ~5-10 seconds)

### `main.py` (Production Mode)
- Runs all 4 phases
- Processes all PDFs from all configured sources
- Processes all 5 sheets
- Full pipeline execution (~10-30 minutes depending on PDF count)

---

## Output Verification

After pipeline completes:
1. Check terminal output for extraction counts
2. Verify CSV files in `extraction_output/`
3. Open Excel file and check:
   - Row count matches extraction count
   - Columns aligned with template
   - No duplicate/garbage columns
4. Run `python verify_excel_data.py` for automated validation

---

## Common Issues & Solutions

### Issue: Only partial data in Excel
**Cause:** Header normalization failed, columns didn't match template  
**Solution:** Check `field_mappings.py` has mappings for all PDF header variations

### Issue: Slow LLM extraction
**Cause:** Running on CPU without GPU acceleration  
**Solution:** Install CUDA-enabled PyTorch or reduce chunk size in `config.py`

### Issue: "No tables found"
**Cause:** PDF is scanned/image-based, Camelot can't detect tables  
**Solution:** Pipeline automatically falls back to OCR (Tier 3)

---

## File Locations

```
CTU-automated-pdf-extraction/
├── main.py                          # Production pipeline
├── test_main_skip_download.py       # Test pipeline
├── config.py                        # Configuration
├── pdf_processor.py                 # PDF extraction (3-tier)
├── llm_data_extractor.py            # LLM interface
├── excel_handler.py                 # Excel writing
├── field_mappings.py                # Header normalization
├── prompts.py                       # LLM prompts
├── downloaded_pdfs/                 # Downloaded PDFs (by source)
├── extraction_output/               # CSV intermediate files
└── Connectivity_Application_Data_OUTPUT2.xlsx  # Final output
```
