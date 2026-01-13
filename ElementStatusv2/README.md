# Element Status Pipeline

Automated pipeline to extract data from PDF reports and populate Excel sheets.

## Input Files

| File | Description |
|------|-------------|
| `Report_TBCB_UC.pdf` | TBCB monitoring report |
| `172838877090Minutes of meeting...pdf` | Minutes of Meeting with Annexures |
| `Connectivity Application Data 1.xlsx` | Target Excel file |

## Usage

### Run Full Pipeline
```powershell
python run_pipeline.py
```

This will:
1. Extract TBCB data from PDF
2. Populate Excel with TBCB data (Mode = "TBCB")
3. Append Annexures from Minutes of Meeting
4. Generate `Connectivity Application Data 1_Updated.xlsx`

### Run Individual Steps

**TBCB Population only:**
```powershell
python populate_excel_v2.py
```

**Annexure Extraction only:**
```powershell
python annexure_pipeline.py
```

## Output

`Connectivity Application Data 1_Updated.xlsx` - Contains:
- TBCB project data with Mode = "TBCB"
- Annexure content appended at the end

## Project Structure

```
ElementStatusv2/
├── run_pipeline.py        # Main entry point
├── populate_excel_v2.py   # TBCB data population
├── annexure_pipeline.py   # Annexure extraction
├── modules/
│   ├── extractor.py       # PDF table extraction
│   └── pdf_processor.py   # Annexure text extraction
└── venv/                  # Python environment
```

## Requirements

- Python 3.x
- pdfplumber
- openpyxl
- pandas
