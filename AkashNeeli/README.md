# PDF Table Extraction Tool

This project extracts tables from PDF files and processes them into structured Excel files with specific required fields.

## Prerequisites

- Python 3.7 or higher
- pip package manager

## Setup

1. **Clone or download the project** to your local machine

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv pdf_extraction_env
   ```

3. **Activate the virtual environment**:
   - On Windows:
     ```bash
     pdf_extraction_env\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source pdf_extraction_env/bin/activate
     ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Execution

To run the PDF table extraction tool with default settings:

```bash
python main.py
```

This will:
1. Extract tables from the PDF file in the `pdfs/` directory
2. Create a consolidated Excel file in `extracted_tables/`
3. Extract required fields and create a formatted output file
4. Generate extraction summary files

### Input Files

- Place your PDF files in the `pdfs/` directory
- The tool will process the first PDF file found in this directory

### Output Files

The processed files will be saved in the `extracted_tables/` directory:
- `*_consolidated.xlsx` - All extracted tables in one file
- `*_consolidated_required_fields.xlsx` - Structured data with required fields
- `extraction_summary.json` - Summary of the extraction process
- `extraction_summary.txt` - Text summary of the extraction process

## Features

- Automatic table detection and extraction from PDFs
- Mapping of extracted data to required field templates
- Special handling for "Applicant" to "Name of Developers" mapping
- Special handling for "Criterion for applying" to "Mode(Criteria for applying)" mapping
- Detailed logging and summary generation

## Project Structure

```
├── main.py                   # Main execution script
├── requirements.txt          # Python dependencies
├── pdf_extractor/            # Core extraction modules
│   ├── __init__.py
│   ├── config.py             # Configuration settings
│   ├── core.py               # Core extraction logic
│   ├── summary.py            # Summary generation
│   └── utils.py              # Utility functions
├── pdfs/                     # Input PDF files
├── extracted_tables/         # Output Excel files
└── data_files/               # Template files
```

## Dependencies

The project requires the following Python packages (installed via requirements.txt):
- camelot-py
- pandas
- openpyxl
- loguru

## Troubleshooting

If you encounter any issues:
1. Ensure all dependencies are installed correctly
2. Verify that your PDF file is in the `pdfs/` directory
3. Check that you have write permissions for the `extracted_tables/` directory
4. Review the log output for specific error messages