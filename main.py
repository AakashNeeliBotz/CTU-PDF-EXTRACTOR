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
    DATA_TO_BE_CAPTURED_FIELDS
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
                        break
                
                if header_row_idx == 0 and len(table_df) > 2:
                    # If still at row 0, default to row 2 (common case for these PDFs)
                    header_row_idx = 2
                
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
            
            # Process remaining tables using the same headers
            if first_table_headers:
                for table_idx in range(1, len(tables)):
                    table_df = tables[table_idx]
                    if table_df.empty:
                        continue
                    
                    # Skip first 2 rows (likely continuation markers or page breaks)
                    data_df = table_df.iloc[2:].reset_index(drop=True) if len(table_df) > 2 else table_df
                    data_df.columns = first_table_headers  # Use same headers as Table 1
                    data_df = data_df.dropna(how='all')
                    
                    if not data_df.empty:
                        processed_tables.append(data_df)
            
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
