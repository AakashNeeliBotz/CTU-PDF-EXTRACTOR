# CTU Automated PDF Data Extraction

This project automates the extraction of renewable energy and power grid data from PDF documents published by CTU (Central Transmission Utility of India) and CEA. It scrapes websites, downloads PDFs, extracts complex tables (using Camelot), and consolidates the data into structured Excel reports.

## Prerequisites

- **Python**: Version 3.10 or higher recommended.
- **Tools**: pip

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/AakashNeeliBotz/CTU-PDF-EXTRACTOR.git
    cd CTU-PDF-EXTRACTOR
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv myvenv
    ```

3.  **Activate the virtual environment:**
    *   **Windows**:
        ```bash
        .\myvenv\Scripts\activate
        ```
    *   **Linux/Mac**:
        ```bash
        source myvenv/bin/activate
        ```

4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: Ghostscript is required for Camelot. If you encounter issues, ensure Ghostscript is installed on your system.*

## Usage

### 🚀 Recommended Method: Skip Download (Fastest)

To run the extraction pipeline **without re-downloading PDFs** (using the provided/existing PDFs in `downloaded_pdfs/`), run:

```bash
python test_main_skip_download.py
```

**Why this is recommended:**
- It is significantly faster as it skips the scraping and downloading steps.
- It ensures you are testing against the exact same set of PDFs committed to the repo.
- It includes the latest logic for extracting "Agreed Substations" and other recent fixes.

### Full Pipeline (Production)

To run the full end-to-end pipeline (Scrape Links -> Download PDFs -> Extract Data -> Generate Excel):

```bash
python main.py
```
*Warning: This will attempt to download fresh PDFs from the source websites, which may take time.*

## Output Validation

After running the script, check the following files:

1.  **Main Output**: `Connectivity_Application_Data_TEST_ALL_SHEETS{N}.xlsx` (e.g., `...SHEETS31.xlsx`)
    *   This is the consolidated Excel file containing all extracted sheets.
    *   Compare this file against expectations.

2.  **Intermediate CSVs**: Located in `extraction_output/`
    *   `Data_to_be_captured_extracted_data.csv`
    *   `Margin_extracted_data.csv`
    *   `Transformation_Capacity_extracted_data.csv`
    *   `Non_RE_proposed_RE_Integration_extracted_data.csv`

## Project Structure

- `downloaded_pdfs/`: Contains the raw PDF files (now tracked in git).
- `extraction_output/`: Contains intermediate CSVs.
- `models/`: Contains model-related data (if any).
- `PROJECT_DOCUMENTATION.md`: Detailed technical documentation of the extraction logic.
- `field_mappings.py`: Definitions for column headers and data parsing rules.
- `pdf_processor.py`: Core logic for Camelot and PyMuPDF extraction.
