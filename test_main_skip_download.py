"""
Test Pipeline - Skip Scraping & Downloading (v3.0)
====================================================
This test script processes existing PDFs without scraping/downloading.
Useful for testing LLM extraction and Excel writing with a small subset.

Updated for v3.0:
- Uses Hugging Face Transformers (GPU-accelerated LLM)
- Uses Docling + Tesseract for OCR (lightweight)
- Auto-finds PDFs in any source folder

Current Test: 1-2 PDFs from any available source folder
- Automatically finds the first available source with PDFs
- Processes up to 2 PDFs for faster testing

Note: First run will download Gemma 3 4B model (~8GB, one-time)
"""

import os
import pandas as pd
import io
from typing import List, Dict, Any
from config import SHEET_CONFIG  # Import the full config from config.py
from pdf_processor import extract_text_from_pdf
from llm_data_extractor import extract_structured_data, _parse_csv_to_records
from excel_handler import write_to_excel
from field_mappings import (
    normalize_header, 
    infer_region_from_state, 
    DATA_TO_BE_CAPTURED_FIELDS
)
import concurrent.futures

# --- Test Configuration ---
BASE_DOWNLOAD_DIR = "downloaded_pdfs"
TEMPLATE_EXCEL_FILE = "Connectivity Application Data.xlsx"
OUTPUT_EXCEL_FILE = "Connectivity_Application_Data_TEST_SN3_betterPrompts3.xlsx"
MAX_WORKERS = 1  # Set to 1 to avoid pypdfium2 threading issues on Windows

# Test Settings: Process only "Data to be captured" sheet
TEST_SHEET_NAME = "Data to be captured"  # Default sheet for testing
TEST_SOURCE = None  # Will auto-detect first available source folder with PDFs
MAX_TEST_PDFS = None  # Process ALL PDFs (set to None for unlimited)


def chunk_text(text, max_chars=3000, overlap=100):
    """Split text into overlapping chunks to avoid LLM context overflow."""
    if not text:
        return []
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + max_chars, n)
        chunks.append(text[start:end])
        if end >= n:
            break
        start = max(0, end - overlap)
    return chunks


def process_pdf_file(pdf_path, prompt_for_sheet, sheet_name):
    """Extract data from PDF using Camelot first, fallback to LLM if needed."""
    try:
        print(f"\n    - Processing file: {os.path.basename(pdf_path)}")
        
        # Extract using 3-tier approach (returns text AND tables)
        raw_text, tables = extract_text_from_pdf(pdf_path)
        
        records = []
        
        # TIER 1: Try to use Camelot tables first (fastest, most accurate)
        if tables and len(tables) > 0:
            print(f"      [+] Camelot found {len(tables)} table(s)! Converting directly to records.")
            
            # First, extract header rows and data from each table
            import pandas as pd
            processed_tables = []
            
            # Find the header row from the first table (assume all tables share same headers)
            first_table_headers = None
            if len(tables) > 0 and not tables[0].empty:
                table_df = tables[0]
                header_row_idx = 0
                
                # Find header row in first table
                for idx in range(min(5, len(table_df))):
                    row_text = ' '.join(table_df.iloc[idx].astype(str).str.lower())
                    non_null_count = table_df.iloc[idx].notna().sum()
                    if non_null_count < 3:
                        continue
                    
                    # Count how many header keywords are found
                    keyword_matches = 0
                    if any(kw in row_text for kw in ['sl. no', 'sl.no', 'serial', 's.no', 's no']):
                        keyword_matches += 1
                    if any(kw in row_text for kw in ['application id', 'app id', 'applicant']):
                        keyword_matches += 1
                    if any(kw in row_text for kw in ['name of', 'developer', 'company']):
                        keyword_matches += 1
                    if any(kw in row_text for kw in ['region', 'state']):
                        keyword_matches += 1
                    if any(kw in row_text for kw in ['substation', 'connectivity', 'date']):
                        keyword_matches += 1
                    if any(kw in row_text for kw in ['capacity', 'quantum', 'mw']):
                        keyword_matches += 1
                    
                    # Require at least 3 keyword matches to consider it a header row
                    if keyword_matches >= 3:
                        header_row_idx = idx
                        print(f"      [DEBUG] Table 1: Found header at row {idx} with {keyword_matches} keyword matches")
                        break
                
                if header_row_idx == 0 and len(table_df) > 2:
                    # If still at row 0, default to row 2 (common case for these PDFs)
                    header_row_idx = 2
                    print(f"      [DEBUG] Table 1: No header keywords found, defaulting to row 2")
                
                # Extract and normalize headers from first table
                raw_headers = table_df.iloc[header_row_idx].astype(str).tolist()
                normalized_headers = [normalize_header(h) for h in raw_headers]
                
                # Handle duplicate column names by making them unique
                seen = {}
                unique_headers = []
                for header in normalized_headers:
                    if header in seen:
                        seen[header] += 1
                        unique_headers.append(f"{header}_{seen[header]}")
                    else:
                        seen[header] = 0
                        unique_headers.append(header)
                
                first_table_headers = unique_headers
                
                # Process first table data
                data_df = table_df.iloc[header_row_idx + 1:].reset_index(drop=True)
                data_df.columns = unique_headers
                data_df = data_df.dropna(how='all')
                if not data_df.empty:
                    processed_tables.append(data_df)
                    print(f"      [*] Table 1: {len(unique_headers)} columns, {len(data_df)} rows")
            
            # Process remaining tables using the same headers
            if first_table_headers:
                for table_idx in range(1, len(tables)):
                    table_df = tables[table_idx]
                    if table_df.empty:
                        continue
                    
                    # Skip first 2 rows (likely continuation markers or page breaks)
                    data_df = table_df.iloc[2:].reset_index(drop=True) if len(table_df) > 2 else table_df
                    
                    # Only apply headers if column count matches
                    if len(data_df.columns) != len(first_table_headers):
                        print(f"      [~] Table {table_idx + 1}: Skipping - column count mismatch ({len(data_df.columns)} vs {len(first_table_headers)} expected)")
                        continue
                    
                    data_df.columns = first_table_headers  # Use same headers as Table 1
                    data_df = data_df.dropna(how='all')
                    
                    if not data_df.empty:
                        processed_tables.append(data_df)
                        print(f"      [*] Table {table_idx + 1}: {len(first_table_headers)} columns, {len(data_df)} rows (using Table 1 headers)")
            
            # Merge all processed tables into one DataFrame with unified columns
            # This prevents each table from having different column sets
            if processed_tables:
                import pandas as pd
                # Concatenate all tables - pandas will align columns automatically
                combined_df = pd.concat(processed_tables, ignore_index=True)
                # Convert to records
                records = combined_df.to_dict('records')
            else:
                records = []
            
            print(f"      [*] Total records extracted: {len(records)}")
            
            # Auto-infer region from state if missing
            for record in records:
                if 'state' in record and ('region' not in record or not record.get('region')):
                    state_value = record.get('state')
                    if state_value:
                        region = infer_region_from_state(str(state_value))
                        if region:
                            record['region'] = region
            
            print(f"\n      {'='*60}")
            print(f"      [OK] CAMELOT EXTRACTION: {len(records)} records")
            print(f"      {'='*60}")
            
            return ('camelot', records)
        
        # TIER 2/3: Skip LLM extraction for now - only use Camelot tables
        print(f"      [~] No tables found by Camelot. Skipping PDF (Camelot-only mode).")
        return ('skip', [])
        
    except Exception as e:
        print(f"      [!] Error processing '{pdf_path}': {e}")
        import traceback
        traceback.print_exc()
        return ('error', [])


def run_test_pipeline():
    """
    Test pipeline that skips scraping/downloading.
    Processes existing PDFs from SN3 folder only.
    """
    print("=" * 70)
    print("="*70)
    print("=== TEST PIPELINE - SKIP SCRAPING/DOWNLOADING ===")
    print("=== Processing 1 PDF from SN3 for 'Data to be captured' sheet ===")
    print("="*70)

    # Ensure template exists
    if not os.path.exists(TEMPLATE_EXCEL_FILE):
        print(f"[!] CRITICAL ERROR: Template file '{TEMPLATE_EXCEL_FILE}' not found. Cannot proceed.")
        return
    
    print(f"\n[*] Template file found: {TEMPLATE_EXCEL_FILE}")
    print(f"[*] Output will be saved to: {OUTPUT_EXCEL_FILE}")
    print(f"\n[*] Config has {len(SHEET_CONFIG)} sheets configured")
    print(f"[*] This test processes ONLY: '{TEST_SHEET_NAME}'")
    
    # Verify the sheet exists in config FIRST
    if TEST_SHEET_NAME not in SHEET_CONFIG:
        print(f"\n[!] ERROR: Sheet '{TEST_SHEET_NAME}' not found in SHEET_CONFIG")
        return
    
    # Get sheet config early
    sheet_config = SHEET_CONFIG[TEST_SHEET_NAME]
    
    # Auto-detect sources if not specified - find ALL sources with PDFs
    global TEST_SOURCE
    sources_to_process = []
    if TEST_SOURCE is None:
        print(f"\n[*] Auto-detecting source folders with PDFs...")
        available_sources = sheet_config["sources"]
        for source_id in available_sources:
            source_folder = os.path.join(BASE_DOWNLOAD_DIR, source_id)
            if os.path.exists(source_folder):
                pdfs = [f for f in os.listdir(source_folder) if f.lower().endswith('.pdf')]
                if pdfs:
                    sources_to_process.append(source_id)
                    print(f"    [+] Found {len(pdfs)} PDF(s) in {source_id}")
        
        if not sources_to_process:
            print(f"\n[!] ERROR: No PDFs found in any source folder for '{TEST_SHEET_NAME}'")
            print(f"    Expected sources: {available_sources}")
            print(f"\n    Please add PDFs to one of these folders:")
            for src in available_sources:
                print(f"      - {os.path.join(BASE_DOWNLOAD_DIR, src)}")
            return
    else:
        # Use specified source
        sources_to_process = [TEST_SOURCE]
    
    print(f"[*] Will process sources: {sources_to_process}")

    # --- Process the Sheet ---
    print(f"\n{'='*70}")
    print("=== STARTING PDF PROCESSING & EXTRACTION ===")
    print(f"{'='*70}")
    
    print(f"\n{'-'*70}")
    print(f"--- Processing sheet: '{TEST_SHEET_NAME}' ---")
    print(f"{'-'*70}")
    
    prompt_for_sheet = sheet_config["prompt"]
    sheet_records = []
    used_camelot = False  # Track which extraction method was used

    # Process all detected sources
    for TEST_SOURCE in sources_to_process:
        source_folder = os.path.join(BASE_DOWNLOAD_DIR, TEST_SOURCE)
        if not os.path.exists(source_folder):
            print(f"  [!] Source folder '{source_folder}' not found. Skipping.")
            continue

        print(f"  [*] Reading PDFs from source: {TEST_SOURCE}")
        pdf_paths = [
            os.path.join(source_folder, f)
            for f in os.listdir(source_folder)
            if f.lower().endswith('.pdf')
        ]
        
        if not pdf_paths:
            print("  [!] No PDFs found in source folder.")
            continue
        
        # Limit to MAX_TEST_PDFS for faster testing (None = process all)
        if MAX_TEST_PDFS is not None:
            pdf_paths = pdf_paths[:MAX_TEST_PDFS]
            print(f"  [+] Found {len(pdf_paths)} PDF(s) to process (limited to {MAX_TEST_PDFS} for testing):")
        else:
            print(f"  [+] Found {len(pdf_paths)} PDF(s) to process (processing ALL):")
        for pdf_path in pdf_paths:
            print(f"      - {os.path.basename(pdf_path)}")

        # Process PDFs (with parallelism for speed)
        print(f"\n  [*] Starting parallel processing (MAX_WORKERS={MAX_WORKERS})...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(process_pdf_file, p, prompt_for_sheet, TEST_SHEET_NAME) for p in pdf_paths]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    method, recs = result
                    if method == 'camelot':
                        used_camelot = True
                    if recs:
                        sheet_records.extend(recs)

    print(f"\n  {'-'*60}")
    print(f"  [*] Total records collected for sheet '{TEST_SHEET_NAME}': {len(sheet_records)}")
    print(f"  {'-'*60}")
    
    # Save to CSV first (intermediate format)
    if sheet_records:
        csv_output_dir = "extraction_output"
        os.makedirs(csv_output_dir, exist_ok=True)
        csv_filename = f"{csv_output_dir}/{TEST_SHEET_NAME.replace(' ', '_')}_extracted_data.csv"
        
        print(f"\n  [*] Saving extracted data to CSV: {csv_filename}")
        try:
            df = pd.DataFrame(sheet_records)
            df.to_csv(csv_filename, index=False)
            print(f"  [OK] Saved {len(sheet_records)} records to CSV")
            print(f"      File: {csv_filename}")
            print(f"      Columns: {list(df.columns)}")
            print(f"\n  [*] CSV Preview (first 5 rows):")
            print(df.head().to_string())
        except Exception as e:
            print(f"  [!] Error saving to CSV: {e}")
    
    # Write to Excel
    if sheet_records:
        print(f"\n  [*] Writing {len(sheet_records)} records to Excel sheet '{TEST_SHEET_NAME}'...")
        try:
            write_to_excel(sheet_records, TEMPLATE_EXCEL_FILE, OUTPUT_EXCEL_FILE, TEST_SHEET_NAME)
            print(f"  [OK] Successfully wrote data to '{TEST_SHEET_NAME}' in Excel")
        except Exception as e:
            print(f"  [!] Error writing to Excel: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"  [~] No records extracted. Check extraction logs above.")

    print(f"\n{'='*70}")
    print("=== TEST PIPELINE EXECUTION FINISHED ===")
    print(f"{'='*70}")
    print(f"\n[Output Files]")
    print(f"  - CSV: extraction_output/{TEST_SHEET_NAME.replace(' ', '_')}_extracted_data.csv")
    print(f"  - Excel: {OUTPUT_EXCEL_FILE}")
    print(f"\n[Test Summary]")
    print(f"  - PDFs processed: {len(sheet_records)} records from sources: {sources_to_process}")
    print(f"  - Sheet processed: '{TEST_SHEET_NAME}'")
    print(f"  - Total records extracted: {len(sheet_records)}")
    print(f"  - Extraction method: {'Camelot (direct table extraction)' if used_camelot else 'LLM (text-based)'}")
    print(f"\n>> Review the CSV file first to validate data, then check the Excel output.")
    print(f"\n[Next steps]")
    print(f"  1. Open CSV in Excel to verify all data is captured")
    print(f"  2. Check Excel output matches template format")
    print(f"  3. If data looks good, process more PDFs or all sheets")


if __name__ == '__main__':
    run_test_pipeline()
