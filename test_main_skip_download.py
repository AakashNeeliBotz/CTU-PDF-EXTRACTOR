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
    DATA_TO_BE_CAPTURED_FIELDS,
    build_schema_alignment_prompt
)
import concurrent.futures

# --- Test Configuration ---
BASE_DOWNLOAD_DIR = "downloaded_pdfs"
TEMPLATE_EXCEL_FILE = "Connectivity Application Data.xlsx"
OUTPUT_EXCEL_FILE = "Connectivity_Application_Data_TEST_SN3_betterPrompts2.xlsx"
MAX_WORKERS = 2

# Test Settings: Process only "Data to be captured" sheet
TEST_SHEET_NAME = "Data to be captured"  # Default sheet for testing
TEST_SOURCE = None  # Will auto-detect first available source folder with PDFs
MAX_TEST_PDFS = 1  # Limit number of PDFs to process (faster testing)


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


def process_table_through_llm(table_df: pd.DataFrame, sheet_name: str, expected_fields: list) -> List[Dict[str, Any]]:
    """
    Route a Camelot table through LLM for schema alignment.
    
    Args:
        table_df: DataFrame from Camelot
        sheet_name: Target sheet name
        expected_fields: List of canonical field names in exact order
        
    Returns:
        List of normalized records
    """
    try:
        # Find header row
        header_row_idx = 0
        for idx in range(min(5, len(table_df))):
            row_text = ' '.join(table_df.iloc[idx].astype(str).str.lower())
            if any(indicator in row_text for indicator in ['sl. no', 'serial', 'application id', 'name of', 'applicant', 'region', 'type']):
                header_row_idx = idx
                break
        
        # Set header and get data rows
        table_df.columns = table_df.iloc[header_row_idx].astype(str)
        data_df = table_df.iloc[header_row_idx + 1:].reset_index(drop=True)
        data_df = data_df.dropna(how='all')
        
        input_row_count = len(data_df)
        
        if input_row_count == 0:
            print(f"      [~] No data rows after header, skipping table")
            return []
        
        print(f"      [*] Table has {input_row_count} data rows")
        
        # Convert to CSV for LLM input
        csv_buffer = io.StringIO()
        table_df.iloc[header_row_idx:].to_csv(csv_buffer, index=False, header=False)
        table_csv = csv_buffer.getvalue()
        
        # Build schema-alignment prompt
        alignment_prompt = build_schema_alignment_prompt(sheet_name, expected_fields, input_row_count)
        full_prompt = alignment_prompt + "\n" + table_csv
        
        print(f"      [*] Sending table to LLM for schema alignment...")
        
        # Call LLM with schema-alignment prompt
        llm_response = extract_structured_data(full_prompt, alignment_prompt)
        
        if not llm_response or 'extracted_data' not in llm_response:
            print(f"      [!] LLM failed to return structured data, falling back to direct normalization")
            return fallback_normalize_table(data_df, expected_fields)
        
        records = llm_response['extracted_data']
        output_row_count = len(records)
        
        # Validate row count
        if output_row_count != input_row_count:
            print(f"      [!] Row count mismatch: input={input_row_count}, output={output_row_count}")
            print(f"      [*] Retrying with stricter prompt...")
            
            # Retry once with even stricter prompt
            strict_prompt = alignment_prompt.replace(
                "CRITICAL:",
                f"ABSOLUTE REQUIREMENT - YOU MUST RETURN EXACTLY {input_row_count} DATA ROWS OR THE SYSTEM WILL FAIL:\n\nCRITICAL:"
            )
            full_prompt_retry = strict_prompt + "\n" + table_csv
            
            llm_response_retry = extract_structured_data(full_prompt_retry, strict_prompt)
            
            if llm_response_retry and 'extracted_data' in llm_response_retry:
                records_retry = llm_response_retry['extracted_data']
                if len(records_retry) == input_row_count:
                    print(f"      [✅] Retry successful: {len(records_retry)} rows")
                    records = records_retry
                else:
                    print(f"      [!] Retry still mismatched, falling back to direct normalization")
                    return fallback_normalize_table(data_df, expected_fields)
            else:
                print(f"      [!] Retry failed, falling back to direct normalization")
                return fallback_normalize_table(data_df, expected_fields)
        
        print(f"      [✅] LLM schema alignment successful: {len(records)} records")
        return records
        
    except Exception as e:
        print(f"      [!] Error in LLM table processing: {e}")
        import traceback
        traceback.print_exc()
        print(f"      [*] Falling back to direct normalization")
        # Use first row as header for fallback
        if len(table_df) > 0:
            table_df.columns = table_df.iloc[0].astype(str)
            data_df_fallback = table_df.iloc[1:].reset_index(drop=True).dropna(how='all')
            return fallback_normalize_table(data_df_fallback, expected_fields)
        return []


def fallback_normalize_table(data_df: pd.DataFrame, expected_fields: list) -> List[Dict[str, Any]]:
    """
    Fallback: direct normalization without LLM (legacy path).
    
    Args:
        data_df: DataFrame with data rows (no header)
        expected_fields: Expected field names
        
    Returns:
        List of records
    """
    print(f"      [*] Using fallback normalization (no LLM)")
    
    # Basic normalization
    records = data_df.to_dict('records')
    normalized_records = []
    
    for record in records:
        cleaned_record = {}
        for key, value in record.items():
            if pd.isna(value) or value == '' or value == 'nan':
                cleaned_record[key] = None
            else:
                cleaned_record[key] = value
        normalized_records.append(cleaned_record)
    
    return normalized_records


def process_camelot_tables_with_llm(tables: List[pd.DataFrame], sheet_name: str, expected_fields: list) -> List[Dict[str, Any]]:
    """
    Process all Camelot tables through LLM for schema alignment.
    
    Args:
        tables: List of DataFrames from Camelot
        sheet_name: Target sheet name
        expected_fields: List of canonical field names
        
    Returns:
        List of all normalized records
    """
    all_records = []
    
    for table_idx, table_df in enumerate(tables):
        if table_df.empty:
            continue
        
        print(f"      [*] Processing table {table_idx + 1}/{len(tables)}: {table_df.shape[0]} rows × {table_df.shape[1]} columns")
        
        records = process_table_through_llm(table_df, sheet_name, expected_fields)
        all_records.extend(records)
        
        print(f"      [+] Extracted {len(records)} records from table {table_idx + 1}")
    
    return all_records


def process_pdf_file(pdf_path, prompt_for_sheet, sheet_name):
    """Extract data from PDF using Camelot first, fallback to LLM if needed."""
    try:
        print(f"\n    - Processing file: {os.path.basename(pdf_path)}")
        
        # Extract using 3-tier approach (returns text AND tables)
        raw_text, tables = extract_text_from_pdf(pdf_path)
        
        records = []
        
        # TIER 1: Try to use Camelot tables first (fastest, most accurate)
        if tables and len(tables) > 0:
            print(f"      [+] Camelot found {len(tables)} table(s)! Using LLM schema alignment.")
            
            # Get expected fields for this sheet
            if sheet_name == "Data to be captured":
                expected_fields = DATA_TO_BE_CAPTURED_FIELDS
            else:
                # For other sheets, use DATA_TO_BE_CAPTURED_FIELDS as default
                # TODO: Add field lists for other sheets
                expected_fields = DATA_TO_BE_CAPTURED_FIELDS
            
            records = process_camelot_tables_with_llm(tables, sheet_name, expected_fields)
            
            print(f"\n      {'='*60}")
            print(f"      [✅] CAMELOT EXTRACTION: {len(records)} records")
            print(f"      {'='*60}")
            
            # Mark that we used Camelot (for summary reporting)
            return ('camelot', records)
        
        # TIER 2/3: Fallback to LLM if no tables found
        print(f"      [~] No tables found by Camelot. Falling back to LLM extraction...")
        
        if not raw_text or len(raw_text.strip()) < 50:
            print("      [~] Insufficient text found. Skipping file.")
        return ('llm', [])
        
        print(f"      [*] Extracted {len(raw_text)} characters from PDF")
        
        chunks = chunk_text(raw_text)
        print(f"      [*] Split into {len(chunks)} chunks (3000 chars each, 100 overlap)")
        print(f"      [*] Processing each chunk with LLM to extract records...")
        
        for i, chunk in enumerate(chunks):
            print(f"\n      [*] Chunk {i+1}/{len(chunks)} sending to LLM (len={len(chunk)})...")
            structured_data = extract_structured_data(chunk, prompt_for_sheet)
            if structured_data and 'extracted_data' in structured_data:
                data_list = structured_data['extracted_data']
                if isinstance(data_list, list):
                    print(f"      [+] Chunk {i+1}: Extracted {len(data_list)} records.")
                    records.extend(data_list)
                else:
                    print("      [!] LLM returned data in a non-list format for a chunk. Skipping chunk.")
            else:
                print("      [!] Failed to extract structured data for a chunk.")
        
        print(f"\n      {'='*60}")
        print(f"      [🤖] LLM EXTRACTION: {len(records)} records")
        print(f"      {'='*60}")
        print(f"      [!] NOTE: Overlapping chunks may create ~{len(chunks)-1} duplicate records")
        print(f"      [!] Consider deduplicating in Excel based on 'sr_no' or 'application_id'")
        
        return ('llm', records)
    except Exception as e:
        print(f"      [!] Error processing '{pdf_path}': {e}")
        import traceback
        traceback.print_exc()
        return []


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
    
    # Auto-detect source if not specified
    global TEST_SOURCE
    if TEST_SOURCE is None:
        print(f"\n[*] Auto-detecting source folder with PDFs...")
        available_sources = sheet_config["sources"]
        for source_id in available_sources:
            source_folder = os.path.join(BASE_DOWNLOAD_DIR, source_id)
            if os.path.exists(source_folder):
                pdfs = [f for f in os.listdir(source_folder) if f.lower().endswith('.pdf')]
                if pdfs:
                    TEST_SOURCE = source_id
                    print(f"    [+] Found {len(pdfs)} PDF(s) in {source_id}")
                    break
        
        if TEST_SOURCE is None:
            print(f"\n[!] ERROR: No PDFs found in any source folder for '{TEST_SHEET_NAME}'")
            print(f"    Expected sources: {available_sources}")
            print(f"\n    Please add PDFs to one of these folders:")
            for src in available_sources:
                print(f"      - {os.path.join(BASE_DOWNLOAD_DIR, src)}")
            return
    
    print(f"[*] Using source: {TEST_SOURCE}")

    # Verify the source is valid for this sheet
    if TEST_SOURCE not in sheet_config["sources"]:
        print(f"\n[!] ERROR: {TEST_SOURCE} not in sources for '{TEST_SHEET_NAME}'")
        print(f"    Expected sources: {sheet_config['sources']}")
        return

    # --- Process the Sheet ---
    print(f"\n{'='*70}")
    print("=== STARTING PDF PROCESSING & EXTRACTION ===")
    print(f"{'='*70}")
    
    print(f"\n{'─'*70}")
    print(f"--- Processing sheet: '{TEST_SHEET_NAME}' ---")
    print(f"{'─'*70}")
    
    prompt_for_sheet = sheet_config["prompt"]
    sheet_records = []
    used_camelot = False  # Track which extraction method was used

    # Process only SN3 source
    source_folder = os.path.join(BASE_DOWNLOAD_DIR, TEST_SOURCE)
    if not os.path.exists(source_folder):
        print(f"  [!] Source folder '{source_folder}' not found. Cannot proceed.")
        return

    print(f"  [*] Reading PDFs from source: {TEST_SOURCE}")
    pdf_paths = [
        os.path.join(source_folder, f)
        for f in os.listdir(source_folder)
        if f.lower().endswith('.pdf')
    ]
    
    if not pdf_paths:
        print("  [!] No PDFs found in source folder.")
        return
    
    # Limit to MAX_TEST_PDFS for faster testing
    pdf_paths = pdf_paths[:MAX_TEST_PDFS]
    
    print(f"  [+] Found {len(pdf_paths)} PDF(s) to process (limited to {MAX_TEST_PDFS} for testing):")
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

    print(f"\n  {'─'*60}")
    print(f"  [*] Total records collected for sheet '{TEST_SHEET_NAME}': {len(sheet_records)}")
    print(f"  {'─'*60}")
    
    # Save to CSV first (intermediate format)
    if sheet_records:
        csv_output_dir = "extraction_output"
        os.makedirs(csv_output_dir, exist_ok=True)
        csv_filename = f"{csv_output_dir}/{TEST_SHEET_NAME.replace(' ', '_')}_extracted_data.csv"
        
        print(f"\n  [*] Saving extracted data to CSV: {csv_filename}")
        try:
            df = pd.DataFrame(sheet_records)
            df.to_csv(csv_filename, index=False)
            print(f"  [✅] Saved {len(sheet_records)} records to CSV")
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
            print(f"  [✅] Successfully wrote data to '{TEST_SHEET_NAME}' in Excel")
        except Exception as e:
            print(f"  [!] Error writing to Excel: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"  [~] No records extracted. Check extraction logs above.")

    print(f"\n{'='*70}")
    print("=== TEST PIPELINE EXECUTION FINISHED ===")
    print(f"{'='*70}")
    print(f"\n📁 Output Files:")
    print(f"  - CSV: extraction_output/{TEST_SHEET_NAME.replace(' ', '_')}_extracted_data.csv")
    print(f"  - Excel: {OUTPUT_EXCEL_FILE}")
    print(f"\n📊 Test Summary:")
    print(f"  - PDFs processed: {len(pdf_paths)} (from {TEST_SOURCE})")
    print(f"  - Sheet processed: '{TEST_SHEET_NAME}'")
    print(f"  - Total records extracted: {len(sheet_records)}")
    print(f"  - Extraction method: {'Camelot (direct table extraction)' if used_camelot else 'LLM (text-based)'}")
    print(f"\n✅ Review the CSV file first to validate data, then check the Excel output.")
    print(f"\n🚀 Next steps:")
    print(f"  1. Open CSV in Excel to verify all data is captured")
    print(f"  2. Check Excel output matches template format")
    print(f"  3. If data looks good, process more PDFs or all sheets")


if __name__ == '__main__':
    run_test_pipeline()
