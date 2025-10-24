import os
from config import DATA_SOURCES, SHEET_CONFIG
from scraper import scrape_all_sources
from downloader import download_all_pdfs
from pdf_processor import extract_text_from_pdf 
from llm_data_extractor import extract_structured_data
from excel_handler import write_to_excel
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

def process_pdf_file(pdf_path, prompt_for_sheet):
    """Extract text from a PDF, chunk it, run LLM on each chunk, and merge results."""
    try:
        print(f"\n    - Processing file: {os.path.basename(pdf_path)}")
        raw_text = extract_text_from_pdf(pdf_path)
        if not raw_text or len(raw_text.strip()) < 50:
            print("      [~] Insufficient text found. Skipping file.")
            return []
        records = []
        for i, chunk in enumerate(chunk_text(raw_text)):
            print(f"      [*] Chunk {i+1} sending to LLM (len={len(chunk)})...")
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
        return []

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
                futures = [executor.submit(process_pdf_file, p, prompt_for_sheet) for p in pdf_paths]
                for future in concurrent.futures.as_completed(futures):
                    recs = future.result()
                    if recs:
                        sheet_records.extend(recs)

        print(f"  [*] Total records collected for sheet '{sheet_name}': {len(sheet_records)}")
        # --- Phase 4: Write Collected Data for the Current Sheet to Excel ---
        print(f"\n[PHASE 4/4] Writing all collected data for '{sheet_name}' to Excel...")
        write_to_excel(sheet_records, TEMPLATE_EXCEL_FILE, OUTPUT_EXCEL_FILE, sheet_name)

    print("\n========================================")
    print("=== PIPELINE EXECUTION FINISHED ===")
    print("========================================")


if __name__ == '__main__':
    run_pipeline()
