"""
Test Pipeline - Skip Scraping & Downloading
============================================
This test script processes existing PDFs without scraping/downloading.
Useful for testing LLM extraction and Excel writing with a small subset.

Current Test: 1 PDF from SN3 (downloaded_pdfs/SN3/)
- Will process the first PDF found in the folder

Processes ONLY 'Data to be captured' sheet (the only sheet that uses SN3).
config.py has been updated with all 5 sheets and their proper sources.
"""

import os
from config import SHEET_CONFIG  # Import the full config from config.py
from pdf_processor import extract_text_from_pdf 
from llm_data_extractor import extract_structured_data
from excel_handler import write_to_excel
import concurrent.futures

# --- Test Configuration ---
BASE_DOWNLOAD_DIR = "downloaded_pdfs"
TEMPLATE_EXCEL_FILE = "Connectivity Application Data.xlsx"
OUTPUT_EXCEL_FILE = "Connectivity_Application_Data_TEST_SN3_betterPrompts.xlsx"
MAX_WORKERS = 2

# Test Settings: Process only "Data to be captured" sheet with SN3 source
TEST_SHEET_NAME = "Data to be captured"  # Only sheet that uses SN3
TEST_SOURCE = "SN3"  # The source folder with your 2 PDFs


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


def process_pdf_file(pdf_path, prompt_for_sheet):
    """Extract text from a PDF, chunk it, run LLM on each chunk, and merge results."""
    try:
        print(f"\n    - Processing file: {os.path.basename(pdf_path)}")
        raw_text = extract_text_from_pdf(pdf_path)
        if not raw_text or len(raw_text.strip()) < 50:
            print("      [~] Insufficient text found. Skipping file.")
            return []
        records = []
        chunks = chunk_text(raw_text)
        print(f"      [*] Split into {len(chunks)} chunks")
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
        print(f"      [*] Total aggregated from file: {len(records)} records.")
        return records
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
    print(f"[*] From source: {TEST_SOURCE}")

    # Verify the sheet exists in config
    if TEST_SHEET_NAME not in SHEET_CONFIG:
        print(f"\n[!] ERROR: Sheet '{TEST_SHEET_NAME}' not found in SHEET_CONFIG")
        return
    
    sheet_config = SHEET_CONFIG[TEST_SHEET_NAME]
    
    # Verify SN3 is in the sources for this sheet
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
    
    # Limit to only 1 PDF for faster testing
    pdf_paths = pdf_paths[:1]
    
    print(f"  [+] Found {len(pdf_paths)} PDF(s) to process (limited to 1 for testing):")
    for pdf_path in pdf_paths:
        print(f"      - {os.path.basename(pdf_path)}")

    # Process PDFs (with parallelism for speed)
    print(f"\n  [*] Starting parallel processing (MAX_WORKERS={MAX_WORKERS})...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_pdf_file, p, prompt_for_sheet) for p in pdf_paths]
        for future in concurrent.futures.as_completed(futures):
            recs = future.result()
            if recs:
                sheet_records.extend(recs)

    print(f"\n  {'─'*60}")
    print(f"  [*] Total records collected for sheet '{TEST_SHEET_NAME}': {len(sheet_records)}")
    print(f"  {'─'*60}")
    
    # Write to Excel
    if sheet_records:
        print(f"\n  [*] Writing {len(sheet_records)} records to Excel sheet '{TEST_SHEET_NAME}'...")
        try:
            write_to_excel(sheet_records, TEMPLATE_EXCEL_FILE, OUTPUT_EXCEL_FILE, TEST_SHEET_NAME)
            print(f"  [+] Successfully wrote data to '{TEST_SHEET_NAME}'")
        except Exception as e:
            print(f"  [!] Error writing to Excel: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"  [~] No records extracted. Check LLM extraction logs above.")

    print(f"\n{'='*70}")
    print("=== TEST PIPELINE EXECUTION FINISHED ===")
    print(f"{'='*70}")
    print(f"\n[+] Output file: {OUTPUT_EXCEL_FILE}")
    print(f"[*] Review the output file to validate extraction quality.")
    print(f"\nTest Summary:")
    print(f"  - PDFs processed: {len(pdf_paths)} (from {TEST_SOURCE})")
    print(f"  - Sheet processed: '{TEST_SHEET_NAME}'")
    print(f"  - Total records extracted: {len(sheet_records)}")
    print(f"  - config.py now has all 5 sheets configured")


if __name__ == '__main__':
    run_test_pipeline()
