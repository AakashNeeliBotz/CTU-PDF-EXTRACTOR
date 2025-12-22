import os
import fitz  # PyMuPDF
from pathlib import Path
import os
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple

# --- Camelot for table extraction ---
try:
    import camelot
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False
    print("[!] Camelot not installed. Table extraction will be limited.")
    print("    Install with: pip install camelot-py[base]")

# --- Docling imports for OCR ---
try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import (
        PdfPipelineOptions,
        TesseractCliOcrOptions,
    )
    from docling.document_converter import PdfFormatOption
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    print("[!] Docling not installed. OCR will not be available.")
    print("    Install with: pip install docling")

# --- Configuration ---
print(f"--- PDF Processor initialized ---")
print(f"--- Camelot table extraction available: {CAMELOT_AVAILABLE} ---")
print(f"--- Docling OCR available: {DOCLING_AVAILABLE} ---")

# --- Camelot Table Extraction ---

def extract_tables_with_camelot(pdf_path: str, flavor: str = 'lattice') -> List[pd.DataFrame]:
    """
    Extract tables from PDF using Camelot.
    
    Args:
        pdf_path: Path to PDF file
        flavor: 'lattice' (more accurate, needs Ghostscript) or 'stream' (simpler)
        
    Returns:
        List of pandas DataFrames, one per table found
    """
    if not CAMELOT_AVAILABLE:
        print("[!] Camelot not available. Cannot extract tables.")
        return []
    
    try:
        print(f"    [*] Attempting Camelot table extraction (flavor='{flavor}')...")
        
        # Try to extract tables
        tables = camelot.read_pdf(
            pdf_path,
            pages='all',
            flavor=flavor,
            suppress_stdout=True,  # Reduce noise
        )
        
        if len(tables) == 0:
            print(f"    [~] No tables found with flavor='{flavor}'.")
            
            # Try alternate flavor as fallback
            if flavor == 'lattice':
                print("    [*] Retrying with flavor='stream'...")
                return extract_tables_with_camelot(pdf_path, flavor='stream')
            
            return []
        
        print(f"    [+] Found {len(tables)} table(s) using Camelot!")
        
        # Convert to DataFrames
        dataframes = []
        for i, table in enumerate(tables):
            df = table.df
            
            # Basic cleaning: remove empty rows/columns
            df = df.replace('', pd.NA).dropna(how='all').dropna(axis=1, how='all')
            
            if not df.empty:
                print(f"      Table {i+1}: {df.shape[0]} rows × {df.shape[1]} columns")
                dataframes.append(df)
        
        return dataframes
    
    except Exception as e:
        error_str = str(e).lower()
        print(f"    [!] Camelot extraction failed: {e}")
        
        # Fallback to 'stream' flavor if lattice fails
        if flavor == 'lattice':
            # Check for common lattice flavor issues
            if 'ghostscript' in error_str:
                print("    [!] Ghostscript not found. Falling back to 'stream' flavor...")
                return extract_tables_with_camelot(pdf_path, flavor='stream')
            elif 'memory' in error_str or 'insufficient' in error_str:
                print("    [!] OpenCV memory error with lattice. Falling back to 'stream' flavor...")
                return extract_tables_with_camelot(pdf_path, flavor='stream')
            elif 'opencv' in error_str:
                print("    [!] OpenCV error with lattice. Falling back to 'stream' flavor...")
                return extract_tables_with_camelot(pdf_path, flavor='stream')
        
        return []


def convert_tables_to_records(tables: List[pd.DataFrame], skip_header_detection: bool = False) -> List[Dict[str, Any]]:
    """
    Convert Camelot-extracted tables to list of records.
    Intelligently finds the header row unless skip_header_detection=True.
    
    Args:
        tables: List of DataFrames from Camelot
        skip_header_detection: If True, assumes columns are already named correctly
        
    Returns:
        List of dictionaries (records)
    """
    all_records = []
    
    for table_idx, df in enumerate(tables):
        if df.empty:
            continue
        
        if not skip_header_detection:
            # Find the header row by looking for common header indicators
            header_row_idx = 0
            for idx in range(min(5, len(df))):
                # Convert row to string and check for header indicators
                row_text = ' '.join(df.iloc[idx].astype(str).str.lower())
                
                # Skip title rows (usually have very few columns filled or are too long)
                non_null_count = df.iloc[idx].notna().sum()
                if non_null_count < 3:  # Skip rows with less than 3 non-null values
                    continue
                
                # Look for common header keywords
                if any(indicator in row_text for indicator in [
                    'sl. no', 'sl.no', 'serial', 's.no', 's no',
                    'application', 'app id', 'applicant',
                    'name of', 'developer', 'company',
                    'region', 'state', 'substation',
                    'capacity', 'quantum', 'mw',
                    'date', 'expected', 'connectivity'
                ]):
                    header_row_idx = idx
                    print(f"      [*] Found header row at index {idx} for table {table_idx + 1}")
                    break
            
            # Use identified row as header
            df.columns = df.iloc[header_row_idx].astype(str)
            # Get data rows (everything after header)
            df = df.iloc[header_row_idx + 1:].reset_index(drop=True)
        
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        if len(df) == 0:
            print(f"      [~] No data rows found after header in table {table_idx + 1}")
            continue
        
        # Convert to records
        records = df.to_dict('records')
        print(f"      [*] Extracted {len(records)} records from table {table_idx + 1}")
        
        all_records.extend(records)
    
    return all_records

# --- Lazy Docling Converter Loader ---
_docling_converter = None
docling_load_failed = False  # Track if Docling loading failed to avoid retry loops

def _ensure_docling_loaded():
    """Load Docling converter on-demand only when needed (lazy loading)."""
    global _docling_converter, docling_load_failed
    
    if not DOCLING_AVAILABLE:
        print("[!] Docling not available. Cannot perform OCR.")
        return False
    
    # If we already tried and failed, don't retry
    if docling_load_failed:
        print("[!] Docling loading previously failed, skipping retry.")
        return False
    
    if _docling_converter is not None:
        print("[*] Docling converter already loaded, reusing...")
        return True
    
    try:
        print("[*] Initializing Docling converter with Tesseract OCR...")
        print("    Note: Ensure Tesseract is installed on your system.")
        print("    Install: https://tesseract-ocr.github.io/tessdoc/Installation.html")
        
        # Configure Tesseract OCR with auto language detection
        ocr_options = TesseractCliOcrOptions(lang=["eng"])  # English, can use ["auto"] for auto-detect
        
        # Set up PDF pipeline with OCR enabled
        pipeline_options = PdfPipelineOptions(
            do_ocr=True,
            force_full_page_ocr=True,  # Force OCR for all pages
            ocr_options=ocr_options
        )
        
        # Create converter with PDF options
        _docling_converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options,
                )
            }
        )
        
        print("[+] Docling converter initialized successfully!")
        return True
        
    except KeyboardInterrupt:
        print("\n[!] Docling initialization interrupted by user.")
        _docling_converter = None
        docling_load_failed = True
        return False
    except Exception as e:
        print(f"[!] ERROR initializing Docling: {e}")
        print(f"[!] Error type: {type(e).__name__}")
        print("[!] Make sure Tesseract is installed and in your system PATH.")
        import traceback
        traceback.print_exc()
        _docling_converter = None
        docling_load_failed = True
        return False

def run_ocr_with_docling(pdf_path):
    """
    Performs OCR on a PDF file using Docling with Tesseract.
    Returns the extracted text as a string.
    """
    success = _ensure_docling_loaded()
    if not success or _docling_converter is None:
        print("[!] Docling converter not available. Skipping OCR.")
        return ""

    try:
        print(f"    [*] Running Docling OCR on PDF...")
        
        # Convert PDF using Docling
        result = _docling_converter.convert(pdf_path)
        doc = result.document
        
        # Export to markdown format (clean and structured)
        text = doc.export_to_markdown()
        
        print(f"    [+] Docling OCR completed. Extracted {len(text)} characters.")
        return text
    
    except Exception as e:
        print(f"[!] Error during Docling OCR: {e}")
        import traceback
        traceback.print_exc()
        return ""

def extract_text_from_pdf(pdf_path: str) -> Tuple[str, List[pd.DataFrame]]:
    """
    Extracts data from a PDF using a 3-tier approach:
    1. Camelot (for tabular PDFs)
    2. PyMuPDF (for digital text PDFs  
    3. Docling OCR (for scanned PDFs)
    
    Returns:
        Tuple of (text_content, list_of_table_dataframes)
    """
    tables = []
    full_text = ""
    
    try:
        # --- TIER 1: Try Camelot for table extraction first ---
        if CAMELOT_AVAILABLE:
            tables = extract_tables_with_camelot(pdf_path)
            
            if tables:
                print(f"  [+] Camelot extracted {len(tables)} table(s) from '{os.path.basename(pdf_path)}'.")
                print(f"  [*] Tabular PDF detected - skipping text extraction for optimal speed.")
                return "", tables  # Early return: skip PyMuPDF and OCR for tabular PDFs
                
        # --- TIER 2: PyMuPDF for digital text extraction ---
        doc = fitz.open(pdf_path)
        for pno in range(doc.page_count):
            page = doc.load_page(pno)
            txt = page.get_text("text")
            if isinstance(txt, str):
                full_text += txt
            else:
                full_text += str(txt)
        doc.close()

        # --- TIER 3: If minimal text, use Docling OCR ---
        if len(full_text.strip()) < 100:
            print(f"  [~] Minimal text found in '{os.path.basename(pdf_path)}'. Switching to Docling OCR.")
            
            # Check if Docling is available before attempting
            if not DOCLING_AVAILABLE or docling_load_failed:
                print(f"  [!] Docling OCR unavailable. Skipping file '{os.path.basename(pdf_path)}'.")
                return full_text, tables
            
            # Use Docling to OCR the entire PDF
            full_text = run_ocr_with_docling(pdf_path)
            
            if not full_text.strip():
                print(f"  [!] Docling OCR failed to extract text from '{os.path.basename(pdf_path)}'.")
            else:
                # After OCR, try Camelot again on the OCR'd content if no tables found yet
                if CAMELOT_AVAILABLE and not tables:
                    print("  [*] Retrying Camelot extraction after OCR...")
                    tables = extract_tables_with_camelot(pdf_path)
        else:
            print(f"  [+] Successfully extracted text directly from '{os.path.basename(pdf_path)}'.")

    except Exception as e:
        print(f"  [!] An error occurred while processing {pdf_path}: {e}")
    
    return full_text, tables

if __name__ == '__main__':
    # ==============================================================================
    # --- For Testing ---
    # This block allows you to test the processor on a single PDF file.
    # ==============================================================================
    
    # --- STEP 1: Find a PDF in 'downloaded_pdfs' folder ---
    download_dir = "downloaded_pdfs"
    
    # Try to find any PDF file for testing
    test_pdf_path = None
    if os.path.exists(download_dir):
        for root, dirs, files in os.walk(download_dir):
            for file in files:
                if file.lower().endswith('.pdf'):
                    test_pdf_path = os.path.join(root, file)
                    break
            if test_pdf_path:
                break
    
    if test_pdf_path and os.path.exists(test_pdf_path):
        print(f"\n--- Testing Docling PDF Processor ---")
        print(f"--- File: {os.path.basename(test_pdf_path)} ---")
        print(f"--- Path: {test_pdf_path} ---\n")
        
        extracted_content = extract_text_from_pdf(test_pdf_path)
        
        print("\n" + "="*60)
        print("--- Extracted Content (First 1000 Chars) ---")
        print("="*60)
        print(extracted_content[:1000])
        if len(extracted_content) > 1000:
            print(f"\n... (truncated, total {len(extracted_content)} characters)")
    else:
        print("\n[!] No PDF files found in 'downloaded_pdfs' directory.")
        print("    Please run the scraper/downloader first or place a test PDF in the folder.")
