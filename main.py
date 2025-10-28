import os
import os
import pandas as pd
import io
from typing import List, Dict, Any
from config import DATA_SOURCES, SHEET_CONFIG
from scraper import scrape_all_sources
from downloader import download_all_pdfs
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

# --- Global Configuration ---
BASE_DOWNLOAD_DIR = "downloaded_pdfs"
TEMPLATE_EXCEL_FILE = "Connectivity Application Data.xlsx"
OUTPUT_EXCEL_FILE = "Connectivity_Application_Data_OUTPUT2.xlsx"
MAX_WORKERS = 2  # conservative parallelism to avoid overloading local LLM

def chunk_text(text, max_chars=6000, overlap=100):
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
            
            return ('camelot', records)
        
        # TIER 2/3: Fallback to LLM if no tables found
        print(f"      [~] No tables found by Camelot. Falling back to LLM extraction...")
        
        if not raw_text or len(raw_text.strip()) < 50:
            print("      [~] Insufficient text found. Skipping file.")
            return ('skip', [])
        
        print(f"      [*] Extracted {len(raw_text)} characters from PDF")
        
        chunks = chunk_text(raw_text)
        print(f"      [*] Processing with LLM ({len(chunks)} chunks)...")
        
        for i, chunk in enumerate(chunks):
            print(f"      [*] Chunk {i+1}/{len(chunks)} sending to LLM (len={len(chunk)})...")
            structured_data = extract_structured_data(chunk, prompt_for_sheet)
            if structured_data and 'extracted_data' in structured_data:
                data_list = structured_data['extracted_data']
                if isinstance(data_list, list):
                    print(f"      [+] Chunk {i+1}: {len(data_list)} records.")
                    records.extend(data_list)
                else:
                    print("      [!] LLM returned data in a non-list format for a chunk. Skipping chunk.")
            else:
                print("      [!] Failed to extract structured data for a chunk.")
        
        print(f"\n      {'='*60}")
        print(f"      [🤖] LLM EXTRACTION: {len(records)} records")
        print(f"      {'='*60}")
        
        return ('llm', records)
    except Exception as e:
        print(f"      [!] Error processing '{pdf_path}': {e}")
        return ('error', [])

def run_pipeline():
    """
    Executes the entire data extraction pipeline from start to finish.
    """
    print("=====================================================")
    print("=== STARTING CTU AUTOMATED DATA EXTRACTION PIPELINE ===")
    print("=====================================================")

    # Determine only the sources needed for the configured sheets (sheet-first)
    required_source_ids = set()
    for cfg in SHEET_CONFIG.values():
        required_source_ids.update(cfg.get("sources", []))
    filtered_sources = {sid: DATA_SOURCES[sid] for sid in required_source_ids if sid in DATA_SOURCES}

    # --- Phase 1: Scrape Required Sources ---
    print("\n[PHASE 1/4] Scraping required data sources for PDF links...")
    all_links = scrape_all_sources(filtered_sources)
    if not all_links:
        print("[!] No PDF links found across required sources. Exiting.")
        return
    print("[+] Scraping complete.")

    # --- Phase 2: Download PDFs into Organized Folders ---
    print("\n[PHASE 2/4] Downloading PDFs...")
    download_all_pdfs(all_links, BASE_DOWNLOAD_DIR)
    print("[+] All downloads are up-to-date.")
    
    # --- Phase 3: Process PDFs and Write Data Sheet by Sheet ---
    print("\n[PHASE 3/4] Processing PDFs and extracting data for each sheet...")
    
    # Ensure template exists before we start processing
    if not os.path.exists(TEMPLATE_EXCEL_FILE):
        print(f"[!] CRITICAL ERROR: Template file '{TEMPLATE_EXCEL_FILE}' not found. Cannot proceed.")
        return
        
    for sheet_name, config in SHEET_CONFIG.items():
        print(f"\n--- Processing data for sheet: '{sheet_name}' ---")
        
        required_sources = config["sources"]
        prompt_for_sheet = config["prompt"]
        sheet_records = []
        camelot_count = 0
        llm_count = 0

        for source_id in required_sources:
            source_folder = os.path.join(BASE_DOWNLOAD_DIR, source_id)
            if not os.path.exists(source_folder):
                print(f"  [~] Source folder '{source_folder}' not found. Skipping.")
                continue

            print(f"  [*] Reading PDFs from source: {source_id}")
            pdf_paths = [
                os.path.join(source_folder, f)
                for f in os.listdir(source_folder)
                if f.lower().endswith('.pdf')
            ]
            if not pdf_paths:
                print("  [~] No PDFs found in source folder.")
                continue

            # Parallel processing of PDFs for speed
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = [executor.submit(process_pdf_file, p, prompt_for_sheet, sheet_name) for p in pdf_paths]
                for future in concurrent.futures.as_completed(futures):
                    method, recs = future.result()
                    if method == 'camelot':
                        camelot_count += 1
                    elif method == 'llm':
                        llm_count += 1
                    if recs:
                        sheet_records.extend(recs)

        print(f"  [*] Total records collected for sheet '{sheet_name}': {len(sheet_records)}")
        print(f"  [*] Extraction methods used: {camelot_count} Camelot, {llm_count} LLM")
        # --- Phase 4: Write Collected Data for the Current Sheet to Excel ---
        print(f"\n[PHASE 4/4] Writing all collected data for '{sheet_name}' to Excel...")
        
        # Save to CSV first
        if sheet_records:
            csv_output_dir = "extraction_output"
            os.makedirs(csv_output_dir, exist_ok=True)
            csv_filename = f"{csv_output_dir}/{sheet_name.replace(' ', '_')}_extracted_data.csv"
            
            print(f"  [*] Saving to CSV: {csv_filename}")
            df = pd.DataFrame(sheet_records)
            df.to_csv(csv_filename, index=False)
            print(f"  [✅] Saved {len(sheet_records)} records to CSV")
        
        # Write to Excel
        write_to_excel(sheet_records, TEMPLATE_EXCEL_FILE, OUTPUT_EXCEL_FILE, sheet_name)

    print("\n========================================")
    print("=== PIPELINE EXECUTION FINISHED ===")
    print("========================================")


if __name__ == '__main__':
    run_pipeline()
