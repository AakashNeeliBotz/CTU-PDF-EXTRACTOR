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
    MARGIN_FIELDS,
    TRANSFORMATION_CAPACITY_FIELDS,
    NON_RE_FIELDS,
    split_lta_from_application_id,  # Add the new function
    extract_additional_info_from_pooling_ss,  # Add the pooling S/s parser
    clean_substation_name,  # Add substation name cleaner
    lookup_state_from_margin,  # Add state lookup function from Margin sheet
    lookup_state_from_data_to_be_captured,  # Add state lookup function from Data to be captured sheet
    normalize_regional_hub_to_state,  # Add regional hub normalizer
    split_transformation_capacity_row  # Add transformation capacity row splitter
)
import concurrent.futures

# State name normalization mapping
STATE_NAME_MAP = {
    # Full names (keep as-is)
    'Andhra Pradesh': 'Andhra Pradesh',
    'Arunachal Pradesh': 'Arunachal Pradesh',
    'Assam': 'Assam',
    'Bihar': 'Bihar',
    'Chhattisgarh': 'Chhattisgarh',
    'Goa': 'Goa',
    'Gujarat': 'Gujarat',
    'Haryana': 'Haryana',
    'Himachal Pradesh': 'Himachal Pradesh',
    'Jharkhand': 'Jharkhand',
    'Karnataka': 'Karnataka',
    'Kerala': 'Kerala',
    'Madhya Pradesh': 'Madhya Pradesh',
    'Maharashtra': 'Maharashtra',
    'Manipur': 'Manipur',
    'Meghalaya': 'Meghalaya',
    'Mizoram': 'Mizoram',
    'Nagaland': 'Nagaland',
    'Odisha': 'Odisha',
    'Punjab': 'Punjab',
    'Rajasthan': 'Rajasthan',
    'Sikkim': 'Sikkim',
    'Tamil Nadu': 'Tamil Nadu',
    'Telangana': 'Telangana',
    'Tripura': 'Tripura',
    'Uttar Pradesh': 'Uttar Pradesh',
    'Uttarakhand': 'Uttarakhand',
    'West Bengal': 'West Bengal',
    'Ladakh': 'Ladakh',
    'Jammu and Kashmir': 'Jammu and Kashmir',
    
    # Abbreviations to full names
    'AP': 'Andhra Pradesh',
    'AR': 'Arunachal Pradesh',
    'AS': 'Assam',
    'BR': 'Bihar',
    'CG': 'Chhattisgarh',
    'GA': 'Goa',
    'GJ': 'Gujarat',
    'HR': 'Haryana',
    'HP': 'Himachal Pradesh',
    'JH': 'Jharkhand',
    'KA': 'Karnataka',
    'KL': 'Kerala',
    'MP': 'Madhya Pradesh',
    'MH': 'Maharashtra',
    'MN': 'Manipur',
    'ML': 'Meghalaya',
    'MZ': 'Mizoram',
    'NL': 'Nagaland',
    'OD': 'Odisha',
    'OR': 'Odisha',  # Alternative abbreviation
    'PB': 'Punjab',
    'RJ': 'Rajasthan',
    'SK': 'Sikkim',
    'TN': 'Tamil Nadu',
    'TS': 'Telangana',
    'TG': 'Telangana',  # Alternative abbreviation
    'TR': 'Tripura',
    'UP': 'Uttar Pradesh',
    'UK': 'Uttarakhand',
    'UT': 'Uttarakhand',  # Alternative abbreviation
    'WB': 'West Bengal',
    'LA': 'Ladakh',
    'JK': 'Jammu and Kashmir',
}

def normalize_state_name(state_value):
    """
    Normalize state name to full official name.
    Handles abbreviations and ensures consistency.
    
    Args:
        state_value: State name (can be full name or abbreviation)
        
    Returns:
        Normalized full state name or None if invalid
    """
    if not state_value or pd.isna(state_value):
        return None
    
    state_str = str(state_value).strip()
    
    # Check if it's in the mapping (case-insensitive)
    for key, normalized in STATE_NAME_MAP.items():
        if state_str.upper() == key.upper():
            return normalized
    
    # If not found in mapping, return as-is (might be a valid full name with different casing)
    return state_str


def propagate_state_to_parent_complex(records):
    """
    Propagate state from sub-rows to parent complex rows that have missing states.
    
    For Margin sheet hierarchical data:
    - Parent rows have numeric sl_no (e.g., "1", "2", "9")
    - Sub-rows have alphanumeric sl_no (e.g., "1a", "1b", "9a", "9b", "9c")
    - If a parent row has no state but its sub-rows do, copy the state from sub-rows to parent
    
    Args:
        records: List of record dictionaries from Margin sheet extraction
    
    Returns:
        Modified records list with propagated states
    """
    if not records:
        return records
    
    # Build a mapping of parent sl_no to their sub-rows
    # parent_map: {"1": [rec_1a, rec_1b, ...], "9": [rec_9a, rec_9b, rec_9c], ...}
    parent_map = {}
    parent_records = {}
    
    for record in records:
        sl_no = record.get('sl_no', '')
        if not sl_no:
            continue
        
        sl_no_str = str(sl_no).strip()
        
        # Check if this is a parent row (numeric only) or sub-row (has letters)
        if sl_no_str.isdigit():
            # This is a parent row (e.g., "1", "2", "9")
            parent_records[sl_no_str] = record
            if sl_no_str not in parent_map:
                parent_map[sl_no_str] = []
        elif len(sl_no_str) > 1 and sl_no_str[0].isdigit():
            # This is a sub-row (e.g., "1a", "1b", "9a", "9b", "9c")
            # Extract the parent number (e.g., "1" from "1a", "9" from "9c")
            parent_num = ''
            for char in sl_no_str:
                if char.isdigit():
                    parent_num += char
                else:
                    break
            
            if parent_num:
                if parent_num not in parent_map:
                    parent_map[parent_num] = []
                parent_map[parent_num].append(record)
    
    # Now propagate states from sub-rows to parent rows
    propagation_count = 0
    for parent_num, sub_rows in parent_map.items():
        if parent_num not in parent_records:
            continue
        
        parent_record = parent_records[parent_num]
        parent_state = parent_record.get('state')
        
        # Check if parent has no state (None, empty string, or 'nan')
        if not parent_state or str(parent_state).strip() in ['', 'nan', 'None']:
            # Find the state from sub-rows
            sub_states = []
            for sub_row in sub_rows:
                sub_state = sub_row.get('state')
                if sub_state and str(sub_state).strip() not in ['', 'nan', 'None']:
                    sub_states.append(str(sub_state).strip())
            
            if sub_states:
                # Use the most common state (or first if all same)
                from collections import Counter
                most_common_state = Counter(sub_states).most_common(1)[0][0]
                parent_record['state'] = most_common_state
                propagation_count += 1
                print(f"      [State Propagation] sl_no={parent_num}: Set state to '{most_common_state}' from sub-rows")
    
    if propagation_count > 0:
        print(f"      [State Propagation] Total: {propagation_count} parent complex rows updated with states from sub-rows")
    
    return records

# --- Test Configuration ---
BASE_DOWNLOAD_DIR = "downloaded_pdfs"
TEMPLATE_EXCEL_FILE = "Connectivity Application Data.xlsx"
OUTPUT_EXCEL_FILE = "Connectivity_Application_Data_TEST_ALL_SHEETS26.xlsx"
MAX_WORKERS = 1  # Set to 1 to avoid pypdfium2 threading issues on Windows

# Test Settings: Process multiple sheets from different sources
TEST_SHEETS = ["Data to be captured", "Margin", "Transformation Capacity", "Non RE proposed RE Integration"]  # All sheets to test
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
        
        # Extract folder name from PDF path for folder-specific logic
        pdf_folder = os.path.dirname(pdf_path)
        folder_name = os.path.basename(pdf_folder)
        # Handle nested folders (e.g., SN9/subfolder)
        if folder_name and not folder_name.startswith('SN'):
            # Check parent folder
            parent_folder = os.path.dirname(pdf_folder)
            parent_name = os.path.basename(parent_folder)
            if parent_name.startswith('SN'):
                folder_name = parent_name
        
        # Get the correct field list for this sheet
        if sheet_name == "Data to be captured":
            canonical_fields = DATA_TO_BE_CAPTURED_FIELDS
        elif sheet_name == "Margin":
            canonical_fields = MARGIN_FIELDS
        elif sheet_name == "Transformation Capacity":
            canonical_fields = TRANSFORMATION_CAPACITY_FIELDS
        elif sheet_name == "Non RE proposed RE Integration":
            canonical_fields = NON_RE_FIELDS
        else:
            canonical_fields = DATA_TO_BE_CAPTURED_FIELDS  # Default
        
        # Extract using 3-tier approach (returns text AND tables)
        # For SN9 Transformation Capacity and Margin PDFs, try lattice flavor first for clean column separation
        # For SN1 PDFs, use stream flavor as they have complex table structures
        if folder_name == "SN1":
            print(f"      [*] SN1 folder detected - using stream flavor for pages 11-25 (application data tables start from page 11)...")
            try:
                import camelot
                # Extract only from pages 11-25 where application data tables are located
                # Application table starts on page 11 as per user confirmation
                tables = camelot.read_pdf(pdf_path, pages='11-25', flavor='stream', suppress_stdout=True)
                tables = [t.df for t in tables]  # Convert to DataFrames
                raw_text = ""  # Not needed for Camelot extraction
                print(f"      [+] Stream extraction from pages 11-25 successful! Found {len(tables)} table(s)")
            except Exception as e:
                print(f"      [!] SN1 extraction failed ({e}), falling back to normal stream extraction...")
                raw_text, tables = extract_text_from_pdf(pdf_path)
        elif sheet_name == "Transformation Capacity" or sheet_name == "Margin" or sheet_name == "Non RE proposed RE Integration":
            print(f"      [*] {sheet_name} sheet - trying lattice flavor for clean column separation...")
            try:
                import camelot
                tables = camelot.read_pdf(pdf_path, pages='all', flavor='lattice', suppress_stdout=True)
                tables = [t.df for t in tables]  # Convert to DataFrames
                raw_text = ""  # Not needed for Camelot extraction
                print(f"      [+] Lattice extraction successful! Found {len(tables)} table(s)")
            except Exception as e:
                print(f"      [!] Lattice failed ({e}), falling back to stream flavor...")
                raw_text, tables = extract_text_from_pdf(pdf_path)
        else:
            raw_text, tables = extract_text_from_pdf(pdf_path)
        
        records = []
        
        # TIER 1: Try to use Camelot tables first (fastest, most accurate)
        if tables and len(tables) > 0:
            print(f"      [+] Camelot found {len(tables)} table(s)! Converting directly to records.")
            
            # First, extract header rows and data from each table
            import pandas as pd
            processed_tables = []
            
            # Initialize context trackers OUTSIDE table loop to persist across all tables
            current_region = None
            current_timeline = None
            parent_sl_no = None
            custom_serial_counter = 0
            
            # Find the header row from the first table (assume all tables share same headers)
            first_table_headers = None
            is_sn9_pdf = False  # Track if this is an SN9 PDF
            skip_this_pdf = False  # Track if we should skip this entire PDF
            
            # Check folder path to determine which sheet this PDF belongs to
            is_margin_folder = 'Connectivity Margin' in pdf_folder or 'margin' in pdf_folder.lower()
            is_non_re_folder = 'non RE' in pdf_folder or 'non re' in pdf_folder.lower()
            
            # Skip PDF if it's in the wrong folder for this sheet
            if sheet_name == "Margin" and not is_margin_folder:
                # This PDF is NOT in the Margin folder, skip it for Margin sheet
                skip_this_pdf = True
                print(f"      [DEBUG] Skipping non-Margin folder PDF for Margin sheet (folder: {os.path.basename(pdf_folder)})")
            elif sheet_name == "Transformation Capacity" and is_margin_folder:
                # This PDF IS in the Margin folder, skip it for Transformation Capacity sheet
                skip_this_pdf = True
                print(f"      [DEBUG] Skipping Margin folder PDF for Transformation Capacity sheet (folder: {os.path.basename(pdf_folder)})")
            elif sheet_name == "Non RE proposed RE Integration" and not is_non_re_folder:
                # This PDF is NOT in the Non RE folder, skip it for Non RE sheet
                skip_this_pdf = True
                print(f"      [DEBUG] Skipping non-Non RE folder PDF for Non RE sheet (folder: {os.path.basename(pdf_folder)})")
            elif sheet_name != "Non RE proposed RE Integration" and is_non_re_folder:
                # This PDF IS in the Non RE folder, skip it for other sheets
                skip_this_pdf = True
                print(f"      [DEBUG] Skipping Non RE folder PDF for {sheet_name} sheet (folder: {os.path.basename(pdf_folder)})")
            
            if skip_this_pdf:
                # Return empty result to avoid processing
                print(f"      [*] Skipping this PDF for sheet '{sheet_name}'")
                return pd.DataFrame()  # Return empty DataFrame
            
            if len(tables) > 0 and not tables[0].empty:
                table_df = tables[0]
                header_row_idx = 0
                
                # **SPECIAL HANDLING FOR SN9 MARGIN PDFs**
                # SN9 Margin PDFs have 20 columns in lattice mode
                # Lattice has 4 header rows (0-3), data starts at row 4
                # Check if this is actually a Margin PDF by looking at the title row
                is_sn9_margin_pdf = False
                if len(table_df.columns) == 20 and sheet_name == "Margin":
                    # Check first few rows for "Margin" or "Connectivity Margin" keywords
                    # Check header rows (0-3) for margin-specific keywords
                    header_text = ' '.join(table_df.iloc[0:4].astype(str).values.flatten()).lower()
                    
                    # Margin PDF should have "margin for connectivity" or "pooling station" in headers
                    if ('margin for connectivity' in header_text or 
                        ('margin' in header_text and 'pooling station' in header_text)):
                        # Additional check: NOT a bay allocation PDF
                        if not ('allocation' in header_text and 'bay' in header_text):
                            is_sn9_margin_pdf = True
                
                if is_sn9_margin_pdf:
                    is_sn9_pdf = True  # Mark as SN9 PDF to skip normal header detection
                    print(f"      [DEBUG] Detected SN9 Margin PDF ({len(table_df.columns)} columns, LATTICE mode)")
                    print(f"      [DEBUG] Skipping 2 header rows, data/timeline headers start at row 2")
                    
                    # Extract rows starting from row 2 (skip only column header rows 0-1)
                    # Rows 2+ contain region headers, timeline headers, and data rows
                    data_df = table_df.iloc[2:].reset_index(drop=True)
                    
                    # Build records with region and timeline context
                    # Note: current_region, current_timeline, parent_sl_no, custom_serial_counter
                    # are initialized OUTSIDE the table loop to persist across all tables
                    margin_records = []
                    
                    # Helper function to extract Pooling S/s value after "Complex"
                    def extract_pooling_ss(raw_value):
                        """Extract text after 'Complex' if present, otherwise return as-is"""
                        if not raw_value:
                            return raw_value
                        
                        # Check if value contains "Complex"
                        if "Complex" in raw_value:
                            # Find position of "Complex"
                            idx = raw_value.find("Complex")
                            # Get everything after "Complex" (7 characters)
                            after_complex = raw_value[idx + 7:].strip()
                            
                            # If there's meaningful content after "Complex", extract it
                            if after_complex:
                                # Remove leading parenthesis, newlines, and whitespace
                                # Then extract the actual content
                                cleaned = after_complex.lstrip('(\n \t')
                                # Remove closing parenthesis at the start if present (from patterns like "Complex)Value")
                                if cleaned.startswith(')'):
                                    cleaned = cleaned[1:].strip()
                                
                                # Remove trailing closing parenthesis if the value is wrapped in parentheses
                                # (for patterns like "Complex\n(Jalore)" → we want "Jalore" not "Jalore)")
                                if cleaned.endswith(')'):
                                    cleaned = cleaned.rstrip(')')
                                
                                # If we still have content, return it
                                if cleaned:
                                    return cleaned
                        
                        # If no "Complex" found or nothing after it, return original value
                        return raw_value
                    
                    for idx, row in data_df.iterrows():
                        # Get sl_no from column 0
                        sl_no_val = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
                        # Extract pooling_ss with Complex) pattern handling
                        raw_pooling_ss = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
                        pooling_ss_val = extract_pooling_ss(raw_pooling_ss)
                        
                        # Handle cases where sl_no contains newline with station name (e.g., "1\nBokajan")
                        # In this case: sl_no should be the number before \n, pooling_ss should be the text after \n
                        if sl_no_val and '\n' in sl_no_val:
                            parts = sl_no_val.split('\n', 1)  # Split only on first newline
                            if len(parts) == 2:
                                # parts[0] might be a number or letter, parts[1] is the station name
                                potential_sl_no = parts[0].strip()
                                station_name = parts[1].strip()
                                
                                # If we don't have pooling_ss yet, use the station name from sl_no
                                if not pooling_ss_val and station_name:
                                    pooling_ss_val = station_name
                                    sl_no_val = potential_sl_no if potential_sl_no else ""
                                    print(f"      [Split sl_no] '{parts[0]}\\n{parts[1]}' → sl_no='{sl_no_val}', pooling_ss='{pooling_ss_val}'")
                        
                        # Check both columns for headers (timeline headers can be in column 0 OR column 1)
                        sl_no_lower = sl_no_val.lower()
                        pooling_ss_lower = pooling_ss_val.lower()
                        combined_text = f"{sl_no_val} {pooling_ss_val}".lower()
                        
                        # Detect region headers (e.g., "Northern Region", "Southern Region")
                        if "northern region" in combined_text:
                            current_region = "NR"
                            continue  # Skip this row, it's a header
                        elif "southern region" in combined_text:
                            current_region = "SR"
                            continue
                        elif "western region" in combined_text:
                            current_region = "WR"
                            continue
                        elif "north eastern region" in combined_text or "northeastern region" in combined_text:
                            current_region = "NER"
                            continue
                        
                        # Detect timeline headers - Extract exact timeline from PDF middle rows
                        # Timeline text can be in EITHER column 0 or column 1
                        if "existing re pooling station" in combined_text or "existing ps" in combined_text:
                            current_timeline = "Existing"
                            continue
                        elif "commissioning between" in combined_text or "commissioning by" in combined_text:
                            # Extract the exact timeline text - it's in column 0 (sl_no_val) or column 1 (pooling_ss_val)
                            timeline_text = sl_no_val if "commissioning" in sl_no_lower else pooling_ss_val
                            # Remove prefix (A., B., C., etc.) if present
                            if timeline_text and len(timeline_text) > 2 and timeline_text[1] == '.':
                                timeline_text = timeline_text[3:].strip()
                            # The timeline should be "Between Jul-25 to Dec-25" (keep the exact format from PDF)
                            if "between" in timeline_text.lower():
                                # Extract everything after "between" keyword
                                find_idx = timeline_text.lower().find("between")
                                if find_idx != -1:
                                    # Get the part after "between" (e.g., "Jul-25 to Dec-25")
                                    date_part = timeline_text[find_idx + 7:].strip()  # Skip "between" (7 chars)
                                    # Format: "Between Jul-25 to Dec-25" with proper capitalization
                                    current_timeline = f"Between {date_part}"
                            elif "by" in timeline_text.lower():
                                # Handle patterns like "Commissioning by Jun'25" or "by Dec-31"
                                find_idx = timeline_text.lower().find("by")
                                if find_idx != -1:
                                    # Get the part after "by" (e.g., "Jun'25", "Dec-31")
                                    date_part = timeline_text[find_idx + 2:].strip()  # Skip "by" (2 chars)
                                    # Format: "Between Jul-26 to Dec-31" style based on date
                                    current_timeline = f"Between Jul-26 to {date_part}"
                            continue
                        elif "beyond dec" in combined_text:
                            current_timeline = "Beyond Dec-25"
                            continue
                        
                        # Skip Sub-Total rows (NO - Keep them! User wants them)
                        # if "sub-total" in combined_text or "sub total" in combined_text:
                        #     continue
                        
                        # Skip rows that are just timeline markers (like "NIL", "NA", etc.)
                        if sl_no_val.upper() in ['NIL', 'NA', 'N/A', 'NONE'] and not pooling_ss_val:
                            continue
                        
                        # Skip empty rows
                        if not sl_no_val and not pooling_ss_val:
                            continue
                        
                        # Skip subtotal and total rows - check both sl_no and pooling_ss columns
                        if 'subtotal' in sl_no_lower or 'total' in sl_no_lower:
                            continue
                        if 'subtotal' in pooling_ss_lower or 'total' in pooling_ss_lower:
                            continue
                        
                        # Skip footer notes/comments that span across columns
                        # These are typically long explanatory text that starts with "In WR", "Note:", etc.
                        # Check BOTH sl_no and pooling_ss columns for very long text (>50 chars) with specific patterns
                        note_patterns = ['in wr,', 'in sr,', 'in nr,', 'in er,', 'note:', 'notes:', 
                                       'tr. system', 'transmission system', 'planned w/o']
                        
                        if sl_no_val and len(sl_no_val) > 50:
                            if any(pattern in sl_no_lower for pattern in note_patterns):
                                print(f"      [Skipping Footer Note in sl_no] {sl_no_val[:80]}...")
                                continue
                        
                        if pooling_ss_val and len(pooling_ss_val) > 50:
                            if any(pattern in pooling_ss_lower for pattern in note_patterns):
                                print(f"      [Skipping Footer Note in pooling_ss] {pooling_ss_val[:80]}...")
                                continue
                        
                        # Custom serial numbering logic (1, 1a, 1b, 2, 2a, etc.)
                        if sl_no_val and sl_no_val.isdigit():
                            # New parent row - increment counter
                            custom_serial_counter += 1
                            parent_sl_no = custom_serial_counter
                            final_sl_no = str(custom_serial_counter)
                        elif sl_no_val and sl_no_val.isalpha() and len(sl_no_val) == 1:
                            # Sub-row (a, b, c) - combine with parent
                            final_sl_no = f"{parent_sl_no}{sl_no_val}" if parent_sl_no else sl_no_val
                        elif not sl_no_val and pooling_ss_val:
                            # Missing sl_no but has pooling_ss
                            # Check if this is a Subtotal or Total row
                            if 'subtotal' in pooling_ss_lower or 'total' in pooling_ss_lower:
                                # Use the pooling_ss value as sl_no for Subtotal/Total rows
                                final_sl_no = pooling_ss_val
                            else:
                                # For rows with missing sl_no, treat as NEW independent row (not sub-row)
                                # These should get the next sequential number
                                custom_serial_counter += 1
                                parent_sl_no = custom_serial_counter
                                final_sl_no = str(custom_serial_counter)
                        else:
                            # Keep as-is for other cases
                            final_sl_no = sl_no_val if sl_no_val else None
                        
                        # Helper function to convert to numeric if possible
                        def to_numeric(val):
                            """Convert value to numeric type if possible, otherwise return as string"""
                            if pd.isna(val):
                                return None
                            val_str = str(val).strip()
                            if val_str in ['', 'nan', 'None']:
                                return None
                            # Try to convert to number
                            try:
                                # Remove commas and try float conversion
                                cleaned = val_str.replace(',', '')
                                return float(cleaned)
                            except:
                                # Return as string if not numeric
                                return val_str
                        
                        # Extract additional information from pooling_ss
                        # This splits station names with parenthetical info or descriptive text
                        # Example: "Fatehgarh-III (Section-I)" -> pooling_ss="Fatehgarh-III", additional_info="Section-I"
                        clean_pooling_ss, additional_info = extract_additional_info_from_pooling_ss(pooling_ss_val)
                        
                        # Build the record with column mapping - NUMERIC VALUES
                        num_cols = len(row)
                        record = {
                            'sl_no': final_sl_no,
                            'state': normalize_state_name(row.iloc[2]) if num_cols > 2 and pd.notna(row.iloc[2]) else None,
                            'region': current_region,
                            'pooling_ss': clean_pooling_ss if clean_pooling_ss else None,
                            'additional_information_of_pooling_ss': additional_info,  # New field
                            'timelines': current_timeline,
                            're_potential_mw': to_numeric(row.iloc[3]) if num_cols > 3 else None,  # Column 3: RE Potential (MW) [A]
                            'bess_mw': to_numeric(row.iloc[4]) if num_cols > 4 else None,  # Column 4: BESS (MW) [B]
                            'ss_evacuation_capacity_mw': to_numeric(row.iloc[5]) if num_cols > 5 else None,  # Column 5: S/s Evacuation Capacity (RE Potential - BESS [A-B])
                            'expected_cod_of_pooling_station': str(row.iloc[6]).strip() if num_cols > 6 and pd.notna(row.iloc[6]) and str(row.iloc[6]).strip() not in ['', 'nan'] else None,
                            'connectivity_granted_1_200kv_mw': to_numeric(row.iloc[7]) if num_cols > 7 else None,
                            'connectivity_granted_1_400kv_mw': to_numeric(row.iloc[8]) if num_cols > 8 else None,
                            'connectivity_granted_1_total_mw': to_numeric(row.iloc[9]) if num_cols > 9 else None,
                            'connectivity_granted_2_200kv_mw': to_numeric(row.iloc[10]) if num_cols > 10 else None,
                            'connectivity_granted_2_400kv_mw': to_numeric(row.iloc[11]) if num_cols > 11 else None,
                            'connectivity_granted_2_total_mw': to_numeric(row.iloc[12]) if num_cols > 12 else None,
                            'margin_for_connectivity_200kv_mw': to_numeric(row.iloc[13]) if num_cols > 13 else None,
                            'margin_for_connectivity_400kv_mw': to_numeric(row.iloc[14]) if num_cols > 14 else None,
                            'margin_for_connectivity_total_mw': to_numeric(row.iloc[15]) if num_cols > 15 else None,
                            'additional_margin_200kv_mw': to_numeric(row.iloc[16]) if num_cols > 16 else None,
                            'additional_margin_400kv_mw': to_numeric(row.iloc[17]) if num_cols > 17 else None,
                            'additional_margin_total_mw': to_numeric(row.iloc[18]) if num_cols > 18 else None,
                            'effectiveness_of_gna': str(row.iloc[19]).strip() if num_cols > 19 and pd.notna(row.iloc[19]) and str(row.iloc[19]).strip() not in ['', 'nan'] else None,
                            'remarks': None  # No remarks column in Margin sheet
                        }
                        
                        margin_records.append(record)
                    
                    # Convert to DataFrame and add to processed tables
                    if margin_records:
                        extracted_data = pd.DataFrame(margin_records)
                        # Reindex to canonical MARGIN_FIELDS order
                        extracted_data = extracted_data.reindex(columns=MARGIN_FIELDS)
                        processed_tables.append(extracted_data)
                        print(f"      [*] Table 1: Extracted {len(extracted_data)} rows using SN9 Margin manual column mapping")
                    
                    # Skip the normal header detection and processing for SN9 Margin PDFs
                    first_table_headers = MARGIN_FIELDS
                    
                elif (len(table_df.columns) == 13 and sheet_name == "Non RE proposed RE Integration" and is_non_re_folder):
                    # **SPECIAL HANDLING FOR SN9 NON RE PDFs**
                    # Non RE PDFs from subfolder: "Connectivity margins at existing ISTS (non RE) substations for future RE integration"
                    # Has 13 columns in lattice mode with 3 header rows (0-2), data starts at row 3
                    is_sn9_pdf = True  # Mark to skip normal header detection
                    print(f"      [DEBUG] Detected SN9 Non RE PDF ({len(table_df.columns)} columns, LATTICE mode)")
                    print(f"      [DEBUG] Skipping 3 header rows, data starts at row 3")
                    
                    # Extract data rows (skip first 3 header rows)
                    data_df = table_df.iloc[3:].reset_index(drop=True)
                    
                    # Track current state (detected from data rows)
                    current_state = None
                    non_re_records = []
                    
                    for idx, row in data_df.iterrows():
                        # Get first column value to check for state names
                        first_col = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
                        
                        # Check if this row is a state/region name (includes actual states and regional hubs)
                        # These appear as section headers in the PDF
                        state_names = ['Gujarat', 'Maharashtra', 'Madhya Pradesh', 'Chhattisgarh',
                                     'Andhra Pradesh', 'Karnataka', 'Kerala', 'Tamil Nadu',
                                     'Rajasthan', 'Haryana', 'Uttar Pradesh', 'Odisha',
                                     'Jharkhand', 'Bihar', 'West Bengal',
                                     'Neemarana', 'Paradeep', 'Patna']  # Add regional hubs that appear as section headers
                        
                        if first_col in state_names:
                            # Check if this is ONLY a state header (no data in other columns)
                            # or if it's both a state name AND a data row (station name same as state)
                            has_data = False
                            # Check ALL columns (1 to end) for any data, not just first 5
                            for col_idx in range(1, len(row)):
                                val = str(row.iloc[col_idx]).strip() if pd.notna(row.iloc[col_idx]) else ""
                                if val and val not in ['nan', '', 'None']:
                                    has_data = True
                                    break
                            
                            if not has_data:
                                # This is ONLY a state header, update current_state and skip
                                current_state = normalize_state_name(first_col)
                                print(f"      [+] State header detected: {current_state}")
                                continue
                            else:
                                # This row has both state name AND data - treat as data row
                                # Update current_state but also extract the data
                                current_state = normalize_state_name(first_col)
                                print(f"      [+] State name with data detected: {current_state} (treating as both header and data row)")
                                # Fall through to data extraction below
                        
                        # Check if this is a data row (any non-empty row that's not a state name)
                        if first_col and current_state:
                            # Skip Total rows (e.g., "Total", "Total Jh:", "Total Bh:", etc.)
                            if 'total' in first_col.lower():
                                print(f"      [Skipping Total Row] {first_col}")
                                continue
                            
                            # This is a data row (substation name)
                            num_cols = len(row)
                            
                            # Clean the substation name (remove voltage levels, GIS/AIS, special chars)
                            clean_station_name = clean_substation_name(first_col)
                            
                            # Normalize state (convert regional hubs to actual states)
                            normalized_state = normalize_regional_hub_to_state(current_state)
                            
                            record = {
                                'state': normalize_state_name(normalized_state),
                                'name_of_station': clean_station_name,
                                'capacity_mva': str(row.iloc[1]).strip() if num_cols > 1 and pd.notna(row.iloc[1]) else None,
                                'capacity_allocated_mw': str(row.iloc[2]).strip() if num_cols > 2 and pd.notna(row.iloc[2]) else None,
                                'margin_existing_220kv': str(row.iloc[3]).strip() if num_cols > 3 and pd.notna(row.iloc[3]) else None,
                                'margin_existing_400kv': str(row.iloc[4]).strip() if num_cols > 4 and pd.notna(row.iloc[4]) else None,
                                'line_bays_220kv': str(row.iloc[5]).strip() if num_cols > 5 and pd.notna(row.iloc[5]) else None,
                                'line_bays_400kv': str(row.iloc[6]).strip() if num_cols > 6 and pd.notna(row.iloc[6]) else None,
                                'margin_with_ict_220kv': str(row.iloc[7]).strip() if num_cols > 7 and pd.notna(row.iloc[7]) else None,
                                'margin_with_ict_400kv': str(row.iloc[8]).strip() if num_cols > 8 and pd.notna(row.iloc[8]) else None,
                                'line_bays_with_ict_220kv': str(row.iloc[9]).strip() if num_cols > 9 and pd.notna(row.iloc[9]) else None,
                                'line_bays_with_ict_400kv': str(row.iloc[10]).strip() if num_cols > 10 and pd.notna(row.iloc[10]) else None,
                                'no_of_transformers_required': str(row.iloc[11]).strip() if num_cols > 11 and pd.notna(row.iloc[11]) else None,
                                'remarks': str(row.iloc[12]).strip() if num_cols > 12 and pd.notna(row.iloc[12]) else None
                            }
                            non_re_records.append(record)
                    
                    # Convert to DataFrame
                    if non_re_records:
                        extracted_data = pd.DataFrame(non_re_records)
                        # Reindex to canonical NON_RE_FIELDS order
                        extracted_data = extracted_data.reindex(columns=NON_RE_FIELDS)
                        processed_tables.append(extracted_data)
                        print(f"      [*] Table 1: Extracted {len(extracted_data)} rows using Non RE manual column mapping")
                    
                    # Skip the normal header detection and processing for Non RE PDFs
                    first_table_headers = NON_RE_FIELDS
                    
                elif (len(table_df.columns) == 11 and folder_name == "SN1" and sheet_name == "Data to be captured"):
                    # **SPECIAL HANDLING FOR SN1 APPLICATION DATA TABLE**
                    # SN1 has 11-column table with multi-row headers (rows 1-5) and narrative text (rows 6-9)
                    is_sn9_pdf = True  # Mark to skip normal header detection
                    print(f"      [DEBUG] Detected SN1 application data table (11 columns)")
                    print(f"      [DEBUG] Combining multi-row headers from rows 1-5")
                    
                    # Combine header rows 1-5 to create full column names
                    combined_headers = []
                    for col_idx in range(11):
                        parts = []
                        for row_idx in range(6):  # Check rows 0-5
                            val = table_df.iloc[row_idx, col_idx]
                            if val and str(val).strip() and str(val).strip() not in ['nan', 'Minutes', 'of', 'Transmission']:
                                parts.append(str(val).strip())
                        combined = ' '.join(parts) if parts else f'Column_{col_idx}'
                        combined_headers.append(combined)
                    
                    print(f"      [DEBUG] Combined headers: {combined_headers}")
                    
                    # Normalize headers to canonical field names
                    normalized_headers = [normalize_header(h) for h in combined_headers]
                    print(f"      [DEBUG] Normalized headers: {normalized_headers}")
                    
                    # Skip narrative rows (6-9) and extract data from row 10 onwards
                    data_start_row = 10
                    for row_idx in range(6, min(15, len(table_df))):
                        row_text = ' '.join(str(v) for v in table_df.iloc[row_idx].tolist() if v and str(v).strip())
                        # If we find a row that looks like data (starts with number), that's our data start
                        first_col = str(table_df.iloc[row_idx, 0]).strip()
                        if first_col and (first_col.isdigit() or (len(first_col) <= 3 and first_col[0].isdigit())):
                            data_start_row = row_idx
                            print(f"      [DEBUG] Data starts at row {data_start_row}")
                            break
                    
                    # Extract data rows
                    data_df = table_df.iloc[data_start_row:].reset_index(drop=True)
                    data_df.columns = normalized_headers
                    data_df = data_df.dropna(how='all')
                    
                    # Apply SN1 narrative filtering
                    if len(normalized_headers) > 0:
                        first_col = normalized_headers[0]
                        if first_col in data_df.columns:
                            narrative_keywords = ['it was informed', 'it was mentioned', 'it was also', 'accordingly',
                                                 'm/s', 'details of transmission', 'associated transmission system',
                                                 'applicant was asked', 'upon evolution']
                            mask = data_df[first_col].astype(str).apply(
                                lambda x: len(str(x).strip()) > 100 or
                                         any(kw in str(x).lower()[:80] for kw in narrative_keywords)
                            )
                            filtered_count = mask.sum()
                            data_df = data_df[~mask]
                            if filtered_count > 0:
                                print(f"      [SN1 Filter] Removed {filtered_count} narrative rows")
                    
                    if not data_df.empty:
                        processed_tables.append(data_df)
                        print(f"      [*] Table 1: Extracted {len(data_df)} rows using SN1 11-column mapping")
                    
                    # Set headers for continuation tables
                    first_table_headers = normalized_headers
                    
                elif (18 <= len(table_df.columns) <= 20 and sheet_name == "Transformation Capacity"):
                    # SN9 Transformation Capacity PDF detection
                    is_sn9_pdf = True
                    is_lattice_mode = (len(table_df.columns) == 20)  # Lattice preserves all 20 columns
                    # Skip header rows based on extraction mode
                    header_skip = 4 if is_lattice_mode else 2
                    mode_str = "LATTICE" if is_lattice_mode else "STREAM"
                    print(f"      [DEBUG] Detected SN9 Transformation Capacity PDF ({len(table_df.columns)} columns, {mode_str} mode)")
                    print(f"      [DEBUG] Skipping {header_skip} header rows, data starts at row {header_skip}")
                    header_row_idx = None  # We'll manually create headers
                    
                    # Extract data rows
                    data_df = table_df.iloc[header_skip:].reset_index(drop=True)
                    
                    # Safely extract columns with bounds checking
                    # IMPORTANT: Create DataFrame with columns in CANONICAL order to match TRANSFORMATION_CAPACITY_FIELDS
                    # ONLY 7 fields: s_no, region, state, substation, existing_mva, under_implementation_mva, planned_mva
                    num_cols = len(data_df.columns)
                    
                    if is_lattice_mode:
                        # LATTICE MODE: Clean column separation
                        # Column 4: Planned, Column 5: Existing, Column 6: Under Implementation
                        print(f"      [*] Using LATTICE mode extraction - separate columns for Planned/Existing/Under Implementation")
                        extracted_data = pd.DataFrame({
                            's_no': data_df.iloc[:, 0] if num_cols > 0 else None,
                            'region': data_df.iloc[:, 3] if num_cols > 3 else None,
                            'state': None,  # Not in SN9 PDF
                            'substation': data_df.iloc[:, 1] if num_cols > 1 else None,
                            'existing_mva': data_df.iloc[:, 5] if num_cols > 5 else None,  # Column 5: Existing
                            'under_implementation_mva': data_df.iloc[:, 6] if num_cols > 6 else None,  # Column 6: Under Implementation
                            'planned_mva': data_df.iloc[:, 4] if num_cols > 4 else None  # Column 4: Planned
                        })
                    else:
                        # STREAM MODE: Columns are merged, combine 4 & 5
                        print(f"      [*] Using STREAM mode extraction - merging columns 4 & 5")
                        col4 = data_df.iloc[:, 4] if num_cols > 4 else pd.Series([None] * len(data_df))
                        col5 = data_df.iloc[:, 5] if num_cols > 5 else pd.Series([None] * len(data_df))
                        
                        combined_capacity = []
                        for v4, v5 in zip(col4, col5):
                            parts = []
                            if pd.notna(v4) and str(v4).strip() and str(v4).strip() != 'nan':
                                parts.append(str(v4).strip())
                            if pd.notna(v5) and str(v5).strip() and str(v5).strip() != 'nan':
                                parts.append(str(v5).strip())
                            combined_capacity.append(' | '.join(parts) if parts else None)
                        
                        extracted_data = pd.DataFrame({
                            's_no': data_df.iloc[:, 0] if num_cols > 0 else None,
                            'region': data_df.iloc[:, 3] if num_cols > 3 else None,
                            'state': None,  # Not in SN9 PDF
                            'substation': data_df.iloc[:, 1] if num_cols > 1 else None,
                            'existing_mva': combined_capacity,  # Combined capacity from col 4 & 5
                            'under_implementation_mva': None,  # Cannot reliably separate in stream mode
                            'planned_mva': None  # Cannot reliably separate in stream mode
                        })
                    
                    # Remove empty rows
                    extracted_data = extracted_data.dropna(how='all')
                    
                    # Remove header rows (rows that contain header keywords)
                    header_keywords = ['sl. no', 'serial', 'name of substation', 'transformation capacity (mva)', 
                                      'planned', 'existing', 'under implementation', 'region', 'state']
                    for col in ['s_no', 'substation', 'existing_mva']:
                        if col in extracted_data.columns:
                            mask = extracted_data[col].astype(str).str.lower().isin(header_keywords)
                            extracted_data = extracted_data[~mask]
                    
                    # **CRITICAL FIX**: Forward-fill s_no, substation, region for continuation rows
                    # Each row is a SEPARATE record (e.g., different bays), don't merge them!
                    if not extracted_data.empty:
                        # Forward-fill key fields from previous row when they're empty
                        fill_columns = ['s_no', 'substation', 'region']
                        for col in fill_columns:
                            if col in extracted_data.columns:
                                extracted_data[col] = extracted_data[col].replace('', None)
                                extracted_data[col] = extracted_data[col].ffill()
                        
                        print(f"      [*] Forward-filled key fields for continuation rows")
                        
                        # FILTER OUT rows where all capacity columns are empty
                        # These are bay/margin rows, not transformation capacity rows
                        def has_real_value(val):
                            """Check if value is not None, NaN, empty string, or 'nan' string"""
                            if pd.isna(val):
                                return False
                            val_str = str(val).strip()
                            return val_str and val_str.lower() != 'nan' and val_str != ''
                        
                        capacity_cols = ['existing_mva', 'under_implementation_mva', 'planned_mva']
                        has_capacity_data = extracted_data[capacity_cols].apply(lambda row: any(has_real_value(v) for v in row), axis=1)
                        
                        rows_before = len(extracted_data)
                        extracted_data = extracted_data[has_capacity_data]
                        rows_after = len(extracted_data)
                        print(f"      [*] Filtered from {rows_before} to {rows_after} rows (removed {rows_before - rows_after} rows without capacity data)")
                    
                    if not extracted_data.empty:
                        processed_tables.append(extracted_data)
                        print(f"      [*] Table 1: Extracted {len(extracted_data)} rows using SN9 manual column mapping")
                    
                    # Skip the normal header detection and processing for SN9 PDFs
                    first_table_headers = list(extracted_data.columns)
                
                else:
                    # Normal header detection for non-SN9 PDFs
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
                        if any(kw in row_text for kw in ['name of', 'developer', 'company', 'name of substation']):
                            keyword_matches += 1
                        if any(kw in row_text for kw in ['region', 'state']):
                            keyword_matches += 1
                        if any(kw in row_text for kw in ['substation', 'connectivity', 'date']):
                            keyword_matches += 1
                        if any(kw in row_text for kw in ['capacity', 'quantum', 'mw', 'transformation', 'existing', 'planned']):
                            keyword_matches += 1
                        
                        # Require at least 3 keyword matches to consider it a header row
                        if keyword_matches >= 3:
                            header_row_idx = idx
                            print(f"      [DEBUG] Table 1: Found header at row {idx} with {keyword_matches} keyword matches")
                            break
                    
                    if header_row_idx == 0 and len(table_df) > 2:
                        header_row_idx = 2
                        print(f"      [DEBUG] Table 1: No header keywords found, defaulting to row 2")
                
                # Only process headers for non-SN9 PDFs (SN9 already handled above)
                # Skip entirely if this PDF should not be processed by this sheet
                if skip_this_pdf:
                    print(f"      [*] Skipping this PDF for sheet '{sheet_name}'")
                    # Return empty result to avoid processing
                    return pd.DataFrame()  # Return empty DataFrame
                
                if not is_sn9_pdf:
                    # Extract and normalize headers from first table
                    raw_headers = table_df.iloc[header_row_idx].astype(str).tolist()
                    
                    # Print raw headers for debugging
                    print(f"      [DEBUG] Raw headers extracted: {raw_headers[:10]}{'...' if len(raw_headers) > 10 else ''}")
                    
                    # Normalize all headers using the field_mappings
                    normalized_headers = [normalize_header(h) for h in raw_headers]
                    print(f"      [DEBUG] Normalized headers: {normalized_headers[:10]}{'...' if len(normalized_headers) > 10 else ''}")
                    
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
                    
                    # SN1-specific filtering: Remove narrative text rows
                    # SN1 tables contain meeting minutes mixed with data
                    # Filter out rows where first column contains long narrative text
                    if folder_name == "SN1":
                        # Check first column for narrative patterns
                        first_col = unique_headers[0] if len(unique_headers) > 0 else None
                        if first_col and first_col in data_df.columns:
                            # Narrative rows typically have long text (>100 chars) in first column or start with phrases like "It was"
                            narrative_keywords = ['it was informed', 'it was mentioned', 'it was also', 'accordingly', 
                                                 'm/s', 'details of transmission', 'associated transmission system']
                            mask = data_df[first_col].astype(str).apply(
                                lambda x: len(str(x).strip()) > 100 or 
                                         any(kw in str(x).lower()[:50] for kw in narrative_keywords)
                            )
                            data_df = data_df[~mask]
                            print(f"      [SN1 Filter] Removed {mask.sum()} narrative rows")
                    
                    if not data_df.empty:
                        processed_tables.append(data_df)
                        print(f"      [*] Table 1: {len(unique_headers)} columns, {len(data_df)} rows")
            
            # Process remaining tables using the same headers OR adaptive mapping
            if first_table_headers:
                for table_idx in range(1, len(tables)):
                    table_df = tables[table_idx]
                    if table_df.empty:
                        continue
                    
                    # Check if this is a Non RE continuation table (13 columns)
                    is_non_re_continuation = (len(table_df.columns) == 13 and sheet_name == "Non RE proposed RE Integration" and is_non_re_folder)
                    
                    if is_non_re_continuation:
                        print(f"      [*] Table {table_idx + 1}: Non RE continuation (13 columns), processing with Non RE logic")
                        # Use the same Non RE extraction logic
                        data_df = table_df.iloc[3:].reset_index(drop=True)  # Skip 3 header rows
                        
                        # DO NOT reset current_state - preserve it from previous table to maintain state context
                        # across table boundaries (e.g., Sundargarh rows in Table 4 belong to Paradeep from Table 3)
                        # current_state is already initialized from the first table or will be set when we encounter a state header
                        non_re_records = []
                        
                        for idx, row in data_df.iterrows():
                            first_col = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
                            
                            # Check if this row is a state/region name
                            state_names = ['Gujarat', 'Maharashtra', 'Madhya Pradesh', 'Chhattisgarh',
                                         'Andhra Pradesh', 'Karnataka', 'Kerala', 'Tamil Nadu',
                                         'Rajasthan', 'Haryana', 'Uttar Pradesh', 'Odisha',
                                         'Jharkhand', 'Bihar', 'West Bengal',
                                         'Neemarana', 'Paradeep', 'Patna']
                            
                            if first_col in state_names:
                                # Check if this is ONLY a state header (no data in other columns)
                                # or if it's both a state name AND a data row (station name same as state)
                                has_data = False
                                # Check ALL columns (1 to end) for any data, not just first 5
                                for col_idx in range(1, len(row)):
                                    val = str(row.iloc[col_idx]).strip() if pd.notna(row.iloc[col_idx]) else ""
                                    if val and val not in ['nan', '', 'None']:
                                        has_data = True
                                        break
                                
                                if not has_data:
                                    # This is ONLY a state header, update current_state and skip
                                    current_state = normalize_state_name(first_col)
                                    print(f"      [+] State header detected: {current_state}")
                                    continue
                                else:
                                    # This row has both state name AND data - treat as data row
                                    # Update current_state but also extract the data
                                    current_state = normalize_state_name(first_col)
                                    print(f"      [+] State name with data detected: {current_state} (treating as both header and data row)")
                                    # Fall through to data extraction below
                            
                            # Check if this is a data row
                            if first_col and current_state:
                                # Skip Total rows (e.g., "Total", "Total Jh:", "Total Bh:", etc.)
                                if 'total' in first_col.lower():
                                    print(f"      [Skipping Total Row] {first_col}")
                                    continue
                                
                                num_cols = len(row)
                                
                                # Clean the substation name (remove voltage levels, GIS/AIS, special chars)
                                clean_station_name = clean_substation_name(first_col)
                                
                                # Normalize state (convert regional hubs to actual states)
                                normalized_state = normalize_regional_hub_to_state(current_state)
                                
                                record = {
                                    'state': normalize_state_name(normalized_state),
                                    'name_of_station': clean_station_name,
                                    'capacity_mva': str(row.iloc[1]).strip() if num_cols > 1 and pd.notna(row.iloc[1]) else None,
                                    'capacity_allocated_mw': str(row.iloc[2]).strip() if num_cols > 2 and pd.notna(row.iloc[2]) else None,
                                    'margin_existing_220kv': str(row.iloc[3]).strip() if num_cols > 3 and pd.notna(row.iloc[3]) else None,
                                    'margin_existing_400kv': str(row.iloc[4]).strip() if num_cols > 4 and pd.notna(row.iloc[4]) else None,
                                    'line_bays_220kv': str(row.iloc[5]).strip() if num_cols > 5 and pd.notna(row.iloc[5]) else None,
                                    'line_bays_400kv': str(row.iloc[6]).strip() if num_cols > 6 and pd.notna(row.iloc[6]) else None,
                                    'margin_with_ict_220kv': str(row.iloc[7]).strip() if num_cols > 7 and pd.notna(row.iloc[7]) else None,
                                    'margin_with_ict_400kv': str(row.iloc[8]).strip() if num_cols > 8 and pd.notna(row.iloc[8]) else None,
                                    'line_bays_with_ict_220kv': str(row.iloc[9]).strip() if num_cols > 9 and pd.notna(row.iloc[9]) else None,
                                    'line_bays_with_ict_400kv': str(row.iloc[10]).strip() if num_cols > 10 and pd.notna(row.iloc[10]) else None,
                                    'no_of_transformers_required': str(row.iloc[11]).strip() if num_cols > 11 and pd.notna(row.iloc[11]) else None,
                                    'remarks': str(row.iloc[12]).strip() if num_cols > 12 and pd.notna(row.iloc[12]) else None
                                }
                                non_re_records.append(record)
                        
                        if non_re_records:
                            extracted_data = pd.DataFrame(non_re_records)
                            extracted_data = extracted_data.reindex(columns=NON_RE_FIELDS)
                            processed_tables.append(extracted_data)
                            print(f"      [*] Table {table_idx + 1}: Extracted {len(extracted_data)} rows using Non RE mapping")
                        continue
                    
                    # Check if this is a Margin continuation table (20 columns)
                    is_margin_continuation = (len(table_df.columns) == 20 and sheet_name == "Margin" and is_margin_folder)
                    
                    if is_margin_continuation:
                        print(f"      [*] Table {table_idx + 1}: Margin continuation (20 columns), processing with SN9 Margin logic")
                        # Use the same SN9 Margin extraction logic - skip only 2 column header rows
                        data_df = table_df.iloc[2:].reset_index(drop=True)  # Skip 2 header rows, keep region/timeline headers
                        
                        # Build records with persisted context from previous tables
                        # Note: current_region, current_timeline, parent_sl_no, custom_serial_counter
                        # persist across all tables (initialized outside the table loop)
                        margin_records = []
                        
                        # Helper function to extract Pooling S/s value after "Complex"
                        def extract_pooling_ss(raw_value):
                            """Extract text after 'Complex' if present, otherwise return as-is"""
                            if not raw_value:
                                return raw_value
                            
                            # Check if value contains "Complex"
                            if "Complex" in raw_value:
                                # Find position of "Complex"
                                idx = raw_value.find("Complex")
                                # Get everything after "Complex" (7 characters)
                                after_complex = raw_value[idx + 7:].strip()
                                
                                # If there's meaningful content after "Complex", extract it
                                if after_complex:
                                    # Remove leading parenthesis, newlines, and whitespace
                                    # Then extract the actual content
                                    cleaned = after_complex.lstrip('(\n \t')
                                    # Remove closing parenthesis at the start if present (from patterns like "Complex)Value")
                                    if cleaned.startswith(')'):
                                        cleaned = cleaned[1:].strip()
                                    
                                    # Remove trailing closing parenthesis if the value is wrapped in parentheses
                                    # (for patterns like "Complex\n(Jalore)" → we want "Jalore" not "Jalore)")
                                    if cleaned.endswith(')'):
                                        cleaned = cleaned.rstrip(')')
                                    
                                    # If we still have content, return it
                                    if cleaned:
                                        return cleaned
                            
                            # If no "Complex" found or nothing after it, return original value
                            return raw_value
                        
                        for idx, row in data_df.iterrows():
                            sl_no_val = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
                            # Extract pooling_ss with Complex) pattern handling
                            raw_pooling_ss = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
                            pooling_ss_val = extract_pooling_ss(raw_pooling_ss)
                            
                            # Handle cases where sl_no contains newline with station name (e.g., "1\nBokajan")
                            # In this case: sl_no should be the number before \n, pooling_ss should be the text after \n
                            if sl_no_val and '\n' in sl_no_val:
                                parts = sl_no_val.split('\n', 1)  # Split only on first newline
                                if len(parts) == 2:
                                    # parts[0] might be a number or letter, parts[1] is the station name
                                    potential_sl_no = parts[0].strip()
                                    station_name = parts[1].strip()
                                    
                                    # If we don't have pooling_ss yet, use the station name from sl_no
                                    if not pooling_ss_val and station_name:
                                        pooling_ss_val = station_name
                                        sl_no_val = potential_sl_no if potential_sl_no else ""
                                        print(f"      [Split sl_no] '{parts[0]}\\n{parts[1]}' → sl_no='{sl_no_val}', pooling_ss='{pooling_ss_val}'")
                            
                            # Check both columns for headers (timeline headers can be in column 0 OR column 1)
                            sl_no_lower = sl_no_val.lower()
                            pooling_ss_lower = pooling_ss_val.lower()
                            combined_text = f"{sl_no_val} {pooling_ss_val}".lower()
                            
                            # Detect region headers
                            if "northern region" in combined_text:
                                current_region = "NR"
                                continue
                            elif "southern region" in combined_text:
                                current_region = "SR"
                                continue
                            elif "western region" in combined_text:
                                current_region = "WR"
                                continue
                            elif "north eastern region" in combined_text or "northeastern region" in combined_text:
                                current_region = "NER"
                                continue
                            
                            # Detect timeline headers - Extract exact timeline from PDF middle rows
                            # Timeline text can be in EITHER column 0 or column 1
                            if "existing re pooling station" in combined_text or "existing ps" in combined_text:
                                current_timeline = "Existing"
                                continue
                            elif "commissioning between" in combined_text or "commissioning by" in combined_text:
                                # Extract the exact timeline text - it's in column 0 (sl_no_val) or column 1 (pooling_ss_val)
                                timeline_text = sl_no_val if "commissioning" in sl_no_lower else pooling_ss_val
                                # Remove prefix (A., B., C., etc.) if present
                                if timeline_text and len(timeline_text) > 2 and timeline_text[1] == '.':
                                    timeline_text = timeline_text[3:].strip()
                                # The timeline should be "Between Jul-25 to Dec-25" (keep the exact format from PDF)
                                if "between" in timeline_text.lower():
                                    # Extract everything after "between" keyword
                                    find_idx = timeline_text.lower().find("between")
                                    if find_idx != -1:
                                        # Get the part after "between" (e.g., "Jul-25 to Dec-25")
                                        date_part = timeline_text[find_idx + 7:].strip()  # Skip "between" (7 chars)
                                        # Format: "Between Jul-25 to Dec-25" with proper capitalization
                                        current_timeline = f"Between {date_part}"
                                elif "by" in timeline_text.lower():
                                    # Handle patterns like "Commissioning by Jun'25" or "by Dec-31"
                                    find_idx = timeline_text.lower().find("by")
                                    if find_idx != -1:
                                        # Get the part after "by" (e.g., "Jun'25", "Dec-31")
                                        date_part = timeline_text[find_idx + 2:].strip()  # Skip "by" (2 chars)
                                        # Format: "Between Jul-26 to Dec-31" style based on date
                                        current_timeline = f"Between Jul-26 to {date_part}"
                                continue
                            elif "beyond dec" in combined_text:
                                current_timeline = "Beyond Dec-25"
                                continue
                            
                            # Skip Sub-Total rows (NO - Keep them! User wants them)
                            # if "sub-total" in combined_text or "sub total" in combined_text:
                            #     continue
                            
                            # Skip rows that are just timeline markers (like "NIL", "NA", etc.)
                            if sl_no_val.upper() in ['NIL', 'NA', 'N/A', 'NONE'] and not pooling_ss_val:
                                continue
                            
                            # Skip empty rows
                            if not sl_no_val and not pooling_ss_val:
                                continue
                            
                            # Skip subtotal and total rows - check both sl_no and pooling_ss columns
                            if 'subtotal' in sl_no_lower or 'total' in sl_no_lower:
                                continue
                            if 'subtotal' in pooling_ss_lower or 'total' in pooling_ss_lower:
                                continue
                            
                            # Skip footer notes/comments that span across columns
                            # These are typically long explanatory text that starts with "In WR", "Note:", etc.
                            # Check BOTH sl_no and pooling_ss columns for very long text (>50 chars) with specific patterns
                            note_patterns = ['in wr,', 'in sr,', 'in nr,', 'in er,', 'note:', 'notes:', 
                                           'tr. system', 'transmission system', 'planned w/o']
                            
                            if sl_no_val and len(sl_no_val) > 50:
                                if any(pattern in sl_no_lower for pattern in note_patterns):
                                    print(f"      [Skipping Footer Note in sl_no] {sl_no_val[:80]}...")
                                    continue
                            
                            if pooling_ss_val and len(pooling_ss_val) > 50:
                                if any(pattern in pooling_ss_lower for pattern in note_patterns):
                                    print(f"      [Skipping Footer Note in pooling_ss] {pooling_ss_val[:80]}...")
                                    continue
                            
                            # Custom serial numbering logic (1, 1a, 1b, 2, 2a, etc.)
                            if sl_no_val and sl_no_val.isdigit():
                                custom_serial_counter += 1
                                parent_sl_no = custom_serial_counter
                                final_sl_no = str(custom_serial_counter)
                            elif sl_no_val and sl_no_val.isalpha() and len(sl_no_val) == 1:
                                final_sl_no = f"{parent_sl_no}{sl_no_val}" if parent_sl_no else sl_no_val
                            elif not sl_no_val and pooling_ss_val:
                                # Missing sl_no but has pooling_ss
                                # Check if this is a Subtotal or Total row
                                if 'subtotal' in pooling_ss_lower or 'total' in pooling_ss_lower:
                                    # Use the pooling_ss value as sl_no for Subtotal/Total rows
                                    final_sl_no = pooling_ss_val
                                else:
                                    # For rows with missing sl_no, treat as NEW independent row (not sub-row)
                                    # These should get the next sequential number
                                    custom_serial_counter += 1
                                    parent_sl_no = custom_serial_counter
                                    final_sl_no = str(custom_serial_counter)
                            else:
                                final_sl_no = sl_no_val if sl_no_val else None
                            
                            # Helper function to convert to numeric
                            def to_numeric(val):
                                """Convert value to numeric type if possible"""
                                if pd.isna(val):
                                    return None
                                val_str = str(val).strip()
                                if val_str in ['', 'nan', 'None']:
                                    return None
                                try:
                                    cleaned = val_str.replace(',', '')
                                    return float(cleaned)
                                except:
                                    return val_str
                            
                            # Extract additional information from pooling_ss
                            # This splits station names with parenthetical info or descriptive text
                            # Example: "Fatehgarh-III (Section-I)" -> pooling_ss="Fatehgarh-III", additional_info="Section-I"
                            clean_pooling_ss, additional_info = extract_additional_info_from_pooling_ss(pooling_ss_val)
                            
                            # Build the record - NUMERIC VALUES
                            num_cols = len(row)
                            record = {
                                'sl_no': final_sl_no,
                                'state': normalize_state_name(row.iloc[2]) if num_cols > 2 and pd.notna(row.iloc[2]) else None,
                                'region': current_region,
                                'pooling_ss': clean_pooling_ss if clean_pooling_ss else None,
                                'additional_information_of_pooling_ss': additional_info,  # New field
                                'timelines': current_timeline,
                                're_potential_mw': to_numeric(row.iloc[3]) if num_cols > 3 else None,  # Column 3: RE Potential (MW) [A]
                                'bess_mw': to_numeric(row.iloc[4]) if num_cols > 4 else None,  # Column 4: BESS (MW) [B]
                                'ss_evacuation_capacity_mw': to_numeric(row.iloc[5]) if num_cols > 5 else None,  # Column 5: S/s Evacuation Capacity (RE Potential - BESS [A-B])
                                'expected_cod_of_pooling_station': str(row.iloc[6]).strip() if num_cols > 6 and pd.notna(row.iloc[6]) and str(row.iloc[6]).strip() not in ['', 'nan'] else None,
                                'connectivity_granted_1_200kv_mw': to_numeric(row.iloc[7]) if num_cols > 7 else None,
                                'connectivity_granted_1_400kv_mw': to_numeric(row.iloc[8]) if num_cols > 8 else None,
                                'connectivity_granted_1_total_mw': to_numeric(row.iloc[9]) if num_cols > 9 else None,
                                'connectivity_granted_2_200kv_mw': to_numeric(row.iloc[10]) if num_cols > 10 else None,
                                'connectivity_granted_2_400kv_mw': to_numeric(row.iloc[11]) if num_cols > 11 else None,
                                'connectivity_granted_2_total_mw': to_numeric(row.iloc[12]) if num_cols > 12 else None,
                                'margin_for_connectivity_200kv_mw': to_numeric(row.iloc[13]) if num_cols > 13 else None,
                                'margin_for_connectivity_400kv_mw': to_numeric(row.iloc[14]) if num_cols > 14 else None,
                                'margin_for_connectivity_total_mw': to_numeric(row.iloc[15]) if num_cols > 15 else None,
                                'additional_margin_200kv_mw': to_numeric(row.iloc[16]) if num_cols > 16 else None,
                                'additional_margin_400kv_mw': to_numeric(row.iloc[17]) if num_cols > 17 else None,
                                'additional_margin_total_mw': to_numeric(row.iloc[18]) if num_cols > 18 else None,
                                'effectiveness_of_gna': str(row.iloc[19]).strip() if num_cols > 19 and pd.notna(row.iloc[19]) and str(row.iloc[19]).strip() not in ['', 'nan'] else None,
                                'remarks': None
                            }
                            margin_records.append(record)
                        
                        if margin_records:
                            extracted_data = pd.DataFrame(margin_records)
                            extracted_data = extracted_data.reindex(columns=MARGIN_FIELDS)
                            processed_tables.append(extracted_data)
                            print(f"      [*] Table {table_idx + 1}: Extracted {len(extracted_data)} rows using SN9 Margin mapping")
                        continue
                    
                    # Check if this is an SN9 continuation table (18-20 columns)
                    is_sn9_continuation = (18 <= len(table_df.columns) <= 20 and sheet_name == "Transformation Capacity")
                    
                    if is_sn9_continuation:
                        # Detect lattice vs stream mode for continuation table
                        is_continuation_lattice = (len(table_df.columns) == 20)
                        header_skip = 4 if is_continuation_lattice else 2
                        mode_str = "LATTICE" if is_continuation_lattice else "STREAM"
                        
                        print(f"      [*] Table {table_idx + 1}: SN9 continuation ({len(table_df.columns)} columns, {mode_str}), skipping {header_skip} header rows")
                        data_df = table_df.iloc[header_skip:].reset_index(drop=True)
                        
                        num_cols = len(data_df.columns)
                        
                        if is_continuation_lattice:
                            # LATTICE MODE: Separate columns
                            extracted_data = pd.DataFrame({
                                's_no': data_df.iloc[:, 0] if num_cols > 0 else None,
                                'region': data_df.iloc[:, 3] if num_cols > 3 else None,
                                'state': None,
                                'substation': data_df.iloc[:, 1] if num_cols > 1 else None,
                                'existing_mva': data_df.iloc[:, 5] if num_cols > 5 else None,  # Column 5: Existing
                                'under_implementation_mva': data_df.iloc[:, 6] if num_cols > 6 else None,  # Column 6: Under Implementation
                                'planned_mva': data_df.iloc[:, 4] if num_cols > 4 else None  # Column 4: Planned
                            })
                        else:
                            # STREAM MODE: Merge columns 4 & 5
                            col4 = data_df.iloc[:, 4] if num_cols > 4 else pd.Series([None] * len(data_df))
                            col5 = data_df.iloc[:, 5] if num_cols > 5 else pd.Series([None] * len(data_df))
                            
                            combined_capacity = []
                            for v4, v5 in zip(col4, col5):
                                parts = []
                                if pd.notna(v4) and str(v4).strip() and str(v4).strip() != 'nan':
                                    parts.append(str(v4).strip())
                                if pd.notna(v5) and str(v5).strip() and str(v5).strip() != 'nan':
                                    parts.append(str(v5).strip())
                                combined_capacity.append(' | '.join(parts) if parts else None)
                            
                            extracted_data = pd.DataFrame({
                                's_no': data_df.iloc[:, 0] if num_cols > 0 else None,
                                'region': data_df.iloc[:, 3] if num_cols > 3 else None,
                                'state': None,
                                'substation': data_df.iloc[:, 1] if num_cols > 1 else None,
                                'existing_mva': combined_capacity,  # Combined capacity from col 4 & 5
                                'under_implementation_mva': None,  # Cannot reliably separate in stream mode
                                'planned_mva': None  # Cannot reliably separate in stream mode
                            })
                        
                        extracted_data = extracted_data.dropna(how='all')
                        
                        # Remove header rows
                        header_keywords = ['sl. no', 'serial', 'name of substation', 'transformation capacity (mva)', 
                                          'planned', 'existing', 'under implementation', 'region', 'state']
                        for col in ['s_no', 'substation', 'existing_mva']:
                            if col in extracted_data.columns:
                                mask = extracted_data[col].astype(str).str.lower().isin(header_keywords)
                                extracted_data = extracted_data[~mask]
                        
                        # Forward-fill key fields for continuation rows (same logic as Table 1)
                        if not extracted_data.empty:
                            fill_columns = ['s_no', 'substation', 'region']
                            for col in fill_columns:
                                if col in extracted_data.columns:
                                    extracted_data[col] = extracted_data[col].replace('', None)
                                    extracted_data[col] = extracted_data[col].ffill()
                            
                            # FILTER OUT rows where all capacity columns are empty
                            def has_real_value(val):
                                """Check if value is not None, NaN, empty string, or 'nan' string"""
                                if pd.isna(val):
                                    return False
                                val_str = str(val).strip()
                                return val_str and val_str.lower() != 'nan' and val_str != ''
                            
                            capacity_cols = ['existing_mva', 'under_implementation_mva', 'planned_mva']
                            has_capacity_data = extracted_data[capacity_cols].apply(lambda row: any(has_real_value(v) for v in row), axis=1)
                            
                            extracted_data = extracted_data[has_capacity_data]
                        
                        if not extracted_data.empty:
                            processed_tables.append(extracted_data)
                            print(f"      [*] Table {table_idx + 1}: Extracted {len(extracted_data)} rows using SN9 mapping")
                        continue
                    
                    # Check if this is an SN1 11-column application data table
                    is_sn1_11col = (len(table_df.columns) == 11 and folder_name == "SN1" and sheet_name == "Data to be captured")
                    
                    if is_sn1_11col:
                        print(f"      [*] Table {table_idx + 1}: SN1 11-column application table detected")
                        
                        # Combine header rows 0-5
                        combined_headers = []
                        for col_idx in range(11):
                            parts = []
                            for row_idx in range(min(6, len(table_df))):
                                val = table_df.iloc[row_idx, col_idx]
                                if val and str(val).strip() and str(val).strip() not in ['nan', 'Minutes', 'of', 'Transmission', '34th', 'Consultation']:
                                    parts.append(str(val).strip())
                            combined = ' '.join(parts) if parts else f'Column_{col_idx}'
                            combined_headers.append(combined)
                        
                        # Normalize headers
                        normalized_headers = [normalize_header(h) for h in combined_headers]
                        
                        # Find data start row - skip narrative rows
                        # Start from row 6 and look for actual data
                        data_start_row = None
                        for row_idx in range(6, min(25, len(table_df))):
                            # Get values from first few columns
                            col_vals = [str(table_df.iloc[row_idx, c]).strip() for c in range(min(5, len(table_df.columns)))]
                            
                            # Check if this looks like a data row:
                            # - First column (sl_no) is a short number/empty
                            # - Second column (application_id) is not super long narrative
                            # - At least one of the first 5 columns has content
                            first_col = col_vals[0] if len(col_vals) > 0 else ""
                            second_col = col_vals[1] if len(col_vals) > 1 else ""
                            third_col = col_vals[2] if len(col_vals) > 2 else ""
                            
                            # Skip if second column has narrative keywords or is very long
                            is_narrative = (
                                'meeting' in second_col.lower() or
                                'it was' in second_col.lower() or
                                'transmission system' in second_col.lower() or
                                'applicant was asked' in second_col.lower() or
                                len(second_col) > 150
                            )
                            
                            # Data row should have: short first column OR content in col 2/3
                            has_content = any(len(v) > 0 and v != 'nan' for v in col_vals[:5])
                            looks_like_data = (
                                (len(first_col) <= 5 or first_col == '') and
                                len(second_col) < 150 and
                                (len(third_col) > 0 or len(second_col) > 0) and
                                not is_narrative and
                                has_content
                            )
                            
                            if looks_like_data:
                                data_start_row = row_idx
                                print(f"      [SN1] Data starts at row {data_start_row}")
                                break
                        
                        if data_start_row is None:
                            print(f"      [SN1] No data found in table (all narrative), skipping")
                            continue
                        
                        # Extract data
                        data_df = table_df.iloc[data_start_row:].reset_index(drop=True)
                        data_df.columns = normalized_headers
                        data_df = data_df.dropna(how='all')
                        
                        # Apply narrative filtering
                        if len(normalized_headers) > 0:
                            first_col = normalized_headers[0]
                            second_col = normalized_headers[1] if len(normalized_headers) > 1 else None
                            
                            if first_col in data_df.columns and second_col in data_df.columns:
                                narrative_keywords = ['it was informed', 'it was mentioned', 'it was also', 'accordingly',
                                                     'm/s', 'details of transmission', 'associated transmission system',
                                                     'applicant was asked', 'upon evolution', 'meeting']
                                mask = data_df.apply(
                                    lambda row: (
                                        len(str(row[first_col]).strip()) > 100 or
                                        len(str(row[second_col]).strip()) > 150 or
                                        any(kw in str(row[first_col]).lower()[:100] for kw in narrative_keywords) or
                                        any(kw in str(row[second_col]).lower()[:100] for kw in narrative_keywords)
                                    ),
                                    axis=1
                                )
                                filtered_count = mask.sum()
                                data_df = data_df[~mask]
                                if filtered_count > 0:
                                    print(f"      [SN1 Filter] Removed {filtered_count} narrative rows")
                        
                        # Skip table if too few data rows remain
                        if len(data_df) < 3:
                            print(f"      [SN1] Only {len(data_df)} data rows found, skipping table (likely all headers/narrative)")
                            continue
                        
                        if not data_df.empty:
                            # Reindex to canonical fields
                            data_df_reindexed = data_df.reindex(columns=canonical_fields)
                            processed_tables.append(data_df_reindexed)
                            print(f"      [+] Table {table_idx + 1}: Extracted {len(data_df)} rows using SN1 11-column mapping")
                        continue
                    
                    # Normal processing for non-SN9 tables
                    # Skip first 2 rows (likely continuation markers or page breaks)
                    data_df = table_df.iloc[2:].reset_index(drop=True) if len(table_df) > 2 else table_df
                    
                    # Check if column count matches Table 1
                    if len(data_df.columns) == len(first_table_headers):
                        # Same structure - use Table 1 headers directly
                        data_df.columns = first_table_headers
                        data_df = data_df.dropna(how='all')
                        
                        if not data_df.empty:
                            processed_tables.append(data_df)
                            print(f"      [*] Table {table_idx + 1}: {len(first_table_headers)} columns, {len(data_df)} rows (using Table 1 headers)")
                    else:
                        # Different structure - detect own headers and map to canonical fields
                        print(f"      [*] Table {table_idx + 1}: Different structure ({len(data_df.columns)} cols vs {len(first_table_headers)}), detecting own headers...")
                        
                        # Try to find header row in this table
                        table_header_row_idx = None
                        for idx in range(min(3, len(data_df))):
                            row_text = ' '.join(data_df.iloc[idx].astype(str).str.lower())
                            non_null_count = data_df.iloc[idx].notna().sum()
                            if non_null_count < 2:
                                continue
                            
                            # Count keyword matches
                            keyword_matches = sum([
                                any(kw in row_text for kw in ['sl. no', 'sl.no', 'serial', 's.no', 's no']),
                                any(kw in row_text for kw in ['application id', 'app id', 'applicant', 'developer', 'name']),
                                any(kw in row_text for kw in ['region', 'state', 'substation']),
                                any(kw in row_text for kw in ['capacity', 'quantum', 'mw', 'type']),
                                any(kw in row_text for kw in ['date', 'status', 'remarks'])
                            ])
                            
                            if keyword_matches >= 2:
                                table_header_row_idx = idx
                                break
                        
                        if table_header_row_idx is not None:
                            # Extract headers from this table
                            table_headers = data_df.iloc[table_header_row_idx].astype(str).tolist()
                            table_data = data_df.iloc[table_header_row_idx + 1:].reset_index(drop=True)
                            
                            # Normalize headers
                            normalized_headers = [normalize_header(h) for h in table_headers]
                            
                            # Handle duplicates
                            seen = {}
                            unique_headers = []
                            for header in normalized_headers:
                                if header in seen:
                                    seen[header] += 1
                                    unique_headers.append(f"{header}_{seen[header]}")
                                else:
                                    seen[header] = 0
                                    unique_headers.append(header)
                            
                            table_data.columns = unique_headers
                            table_data = table_data.dropna(how='all')
                            
                            # SN1-specific filtering: Remove narrative text rows
                            if folder_name == "SN1" and not table_data.empty:
                                # Check first column for narrative patterns
                                first_col = unique_headers[0] if len(unique_headers) > 0 else None
                                if first_col and first_col in table_data.columns:
                                    narrative_keywords = ['it was informed', 'it was mentioned', 'it was also', 'accordingly', 
                                                         'm/s', 'details of transmission', 'associated transmission system']
                                    mask = table_data[first_col].astype(str).apply(
                                        lambda x: len(str(x).strip()) > 100 or 
                                                 any(kw in str(x).lower()[:50] for kw in narrative_keywords)
                                    )
                                    filtered_count = mask.sum()
                                    table_data = table_data[~mask]
                                    if filtered_count > 0:
                                        print(f"          [SN1 Filter] Removed {filtered_count} narrative rows")
                            
                            if not table_data.empty:
                                # Map to canonical fields - keep only columns that match the sheet's canonical fields
                                matched_columns = [col for col in unique_headers if col in canonical_fields]
                                unmapped_columns = [col for col in unique_headers if col not in canonical_fields]
                                
                                # Require at least 3 canonical fields to include this table
                                if len(matched_columns) >= 3:
                                    # Reindex to canonical fields (missing columns will be NaN)
                                    table_data_reindexed = table_data.reindex(columns=canonical_fields)
                                    processed_tables.append(table_data_reindexed)
                                    print(f"      [+] Table {table_idx + 1}: Mapped {len(matched_columns)}/{len(unique_headers)} columns, {len(table_data)} rows")
                                    if unmapped_columns:
                                        print(f"          [INFO] Unmapped columns: {unmapped_columns[:5]}{'...' if len(unmapped_columns) > 5 else ''}")
                                else:
                                    print(f"      [~] Table {table_idx + 1}: Skipped - insufficient canonical fields ({len(matched_columns)} < 3)")
                        else:
                            print(f"      [~] Table {table_idx + 1}: Skipped - no header row detected")
            
            # Merge all processed tables into one DataFrame with unified columns
            # This prevents each table from having different column sets
            if processed_tables:
                import pandas as pd
                # Concatenate all tables - pandas will align columns automatically
                combined_df = pd.concat(processed_tables, ignore_index=True)
                
                # IMPORTANT: Reindex to canonical fields for this sheet
                # This ensures only mapped columns go to Excel
                print(f"      [*] Reindexing to canonical fields for sheet '{sheet_name}'")
                combined_df = combined_df.reindex(columns=canonical_fields)
                
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
            
            # Split LTA IDs from Application IDs (for Data to be captured sheet only)
            if sheet_name == "Data to be captured" and records:
                print(f"      [*] Checking for LTA IDs in Application ID field...")
                records = split_lta_from_application_id(records)
            
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
    Processes existing PDFs for all configured sheets from their respective sources.
    """
    print("=" * 70)
    print("="*70)
    print("=== TEST PIPELINE - SKIP SCRAPING/DOWNLOADING ===")
    print(f"=== Processing sheets: {', '.join(TEST_SHEETS)} ===")
    print("="*70)

    # Ensure template exists
    if not os.path.exists(TEMPLATE_EXCEL_FILE):
        print(f"[!] CRITICAL ERROR: Template file '{TEMPLATE_EXCEL_FILE}' not found. Cannot proceed.")
        return
    
    print(f"\n[*] Template file found: {TEMPLATE_EXCEL_FILE}")
    print(f"[*] Output will be saved to: {OUTPUT_EXCEL_FILE}")
    print(f"\n[*] Config has {len(SHEET_CONFIG)} sheets configured")
    print(f"[*] This test processes: {TEST_SHEETS}")
    
    # Process each sheet
    all_sheets_used_camelot = False  # Track extraction method across all sheets
    for TEST_SHEET_NAME in TEST_SHEETS:
        # Verify the sheet exists in config FIRST
        if TEST_SHEET_NAME not in SHEET_CONFIG:
            print(f"\n[!] ERROR: Sheet '{TEST_SHEET_NAME}' not found in SHEET_CONFIG")
            continue
        
        # Get sheet config
        sheet_config = SHEET_CONFIG[TEST_SHEET_NAME]
        
        # Get all sources for this sheet
        sheet_sources = sheet_config["sources"]
        
        # Find sources with PDFs (search recursively in subdirectories)
        sources_with_pdfs = []
        for source_id in sheet_sources:
            source_folder = os.path.join(BASE_DOWNLOAD_DIR, source_id)
            if os.path.exists(source_folder):
                # Collect all PDFs recursively
                all_pdfs = []
                for root, dirs, files in os.walk(source_folder):
                    for f in files:
                        if f.lower().endswith('.pdf'):
                            all_pdfs.append(os.path.join(root, f))
                
                if all_pdfs:
                    sources_with_pdfs.append((source_id, source_folder, all_pdfs))
        
        if not sources_with_pdfs:
            print(f"\n[!] WARNING: No PDFs found for sheet '{TEST_SHEET_NAME}'")
            print(f"    Expected sources: {sheet_sources}")
            continue

        # --- Process the Sheet ---
        print(f"\n{'='*70}")
        print(f"=== PROCESSING SHEET: '{TEST_SHEET_NAME}' ===")
        print(f"{'='*70}")
        
        prompt_for_sheet = sheet_config["prompt"]
        sheet_records = []
        used_camelot = False  # Track which extraction method was used for this sheet
        
        # Process all sources for this sheet
        for source_id, source_folder, pdf_paths in sources_with_pdfs:
            print(f"\n  [*] Processing source: {source_id}")
            
            # pdf_paths already contains full paths from os.walk
            
            # Limit to MAX_TEST_PDFS for faster testing (None = process all)
            if MAX_TEST_PDFS is not None:
                pdf_paths = pdf_paths[:MAX_TEST_PDFS]
                print(f"  [+] Found {len(pdf_paths)} PDF(s) to process (limited to {MAX_TEST_PDFS} for testing):")
            else:
                print(f"  [+] Found {len(pdf_paths)} PDF(s) to process (processing ALL):")
            for pdf_path in pdf_paths:
                print(f"      - {os.path.basename(pdf_path)}")

            # Process PDFs (sequential to avoid Windows issues)
            print(f"\n  [*] Starting sequential processing (MAX_WORKERS={MAX_WORKERS})...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = [executor.submit(process_pdf_file, p, prompt_for_sheet, TEST_SHEET_NAME) for p in pdf_paths]
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    # Check if result is a tuple (method, recs) or an empty DataFrame (skipped)
                    if isinstance(result, pd.DataFrame):
                        # Empty DataFrame means PDF was skipped, continue to next
                        continue
                    # Result is a tuple (method, recs)
                    if result:
                        method, recs = result
                        if method == 'camelot':
                            used_camelot = True
                            all_sheets_used_camelot = True
                        if recs:
                            sheet_records.extend(recs)

        print(f"\n  {'-'*60}")
        print(f"  [*] Total records collected for sheet '{TEST_SHEET_NAME}': {len(sheet_records)}")
        print(f"  {'-'*60}")
        
        # Apply state propagation for Margin sheet
        if TEST_SHEET_NAME == "Margin" and sheet_records:
            print(f"\n  [*] Applying state propagation from subcomplexes to parent complex rows...")
            sheet_records = propagate_state_to_parent_complex(sheet_records)
        
        # Apply substation cleaning, state lookup, and row splitting for Transformation Capacity sheet
        if TEST_SHEET_NAME == "Transformation Capacity" and sheet_records:
            print(f"\n  [*] Processing Transformation Capacity sheet...")
            print(f"      - Cleaning substation names (removing voltage levels, GIS/AIS, special chars)")
            print(f"      - Looking up states from Margin sheet and Data to be captured sheet")
            print(f"      - Extracting voltage levels and calculating MVA capacities")
            print(f"      - Splitting rows by voltage level")
            
            # Load Margin sheet data for state lookup
            margin_csv_path = "extraction_output/Margin_extracted_data.csv"
            margin_data = []
            
            if os.path.exists(margin_csv_path):
                try:
                    margin_df = pd.read_csv(margin_csv_path)
                    margin_data = margin_df.to_dict('records')
                    print(f"      [OK] Loaded {len(margin_data)} records from Margin sheet for state lookup")
                except Exception as e:
                    print(f"      [!] Could not load Margin data: {e}")
            else:
                print(f"      [!] Margin CSV not found at {margin_csv_path}")
            
            # Load Data to be captured sheet data for state lookup (fallback)
            data_to_be_captured_csv_path = "extraction_output/Data_to_be_captured_extracted_data.csv"
            data_to_be_captured_data = []
            
            if os.path.exists(data_to_be_captured_csv_path):
                try:
                    dtbc_df = pd.read_csv(data_to_be_captured_csv_path)
                    data_to_be_captured_data = dtbc_df.to_dict('records')
                    print(f"      [OK] Loaded {len(data_to_be_captured_data)} records from Data to be captured sheet for state lookup")
                except Exception as e:
                    print(f"      [!] Could not load Data to be captured data: {e}")
            else:
                print(f"      [!] Data to be captured CSV not found at {data_to_be_captured_csv_path}")
            
            if not margin_data and not data_to_be_captured_data:
                print(f"      [!] No data sources available for state lookup")
            
            # STEP 1: Clean substation names and lookup states (before row splitting)
            cleaned_count = 0
            state_from_margin_count = 0
            state_from_dtbc_count = 0
            
            for record in sheet_records:
                original_substation = record.get('substation', '')
                
                if original_substation:
                    # Clean the substation name
                    cleaned_substation = clean_substation_name(original_substation)
                    
                    if cleaned_substation != original_substation:
                        cleaned_count += 1
                        if cleaned_count <= 5:  # Show first 5 examples
                            print(f"      [Clean] '{original_substation}' → '{cleaned_substation}'")
                    
                    # Update the record with cleaned name
                    record['substation'] = cleaned_substation
                    
                    # First, try to look up state from Margin sheet
                    state = None
                    source = None
                    
                    if margin_data:
                        state = lookup_state_from_margin(cleaned_substation, margin_data)
                        if state:
                            source = 'Margin'
                            state_from_margin_count += 1
                    
                    # If not found in Margin, try Data to be captured sheet
                    if not state and data_to_be_captured_data:
                        state = lookup_state_from_data_to_be_captured(cleaned_substation, data_to_be_captured_data)
                        if state:
                            source = 'Data to be captured'
                            state_from_dtbc_count += 1
                    
                    # Update the record if state was found
                    if state:
                        record['state'] = state
                        if (state_from_margin_count + state_from_dtbc_count) <= 5:  # Show first 5 examples
                            print(f"      [State from {source}] '{cleaned_substation}' → {state}")
            
            print(f"      [Summary] Cleaned {cleaned_count} substation names")
            print(f"      [Summary] Found states for {state_from_margin_count} substations from Margin sheet")
            print(f"      [Summary] Found states for {state_from_dtbc_count} substations from Data to be captured sheet")
            print(f"      [Summary] Total states filled: {state_from_margin_count + state_from_dtbc_count}")
            
            # STEP 2: Split rows by voltage level and calculate MVA
            print(f"\n      [*] Splitting rows by voltage level and calculating MVA capacities...")
            original_count = len(sheet_records)
            transformed_records = []
            
            for record in sheet_records:
                # DEBUG: Print Bhuj-II data before transformation
                if 'Bhuj-II' in str(record.get('substation', '')):
                    print(f"\n      [DEBUG Bhuj-II BEFORE transformation]:")
                    print(f"        Substation: {record.get('substation')}")
                    print(f"        Existing: {record.get('existing_mva')}")
                    print(f"        Under Impl: {record.get('under_implementation_mva')}")
                    print(f"        Planned: {record.get('planned_mva')}")
                
                # Split this row into multiple rows (one per voltage level)
                split_rows = split_transformation_capacity_row(record)
                
                # DEBUG: Print Bhuj-II data after transformation
                for split_row in split_rows:
                    if 'Bhuj-II' in str(split_row.get('substation', '')):
                        print(f"\n      [DEBUG Bhuj-II AFTER transformation]:")
                        print(f"        Substation: {split_row.get('substation')}")
                        print(f"        Voltage: {split_row.get('voltage_level_kv')} kV")
                        print(f"        Existing: {split_row.get('existing_mva')}")
                        print(f"        Under Impl: {split_row.get('under_implementation_mva')}")
                        print(f"        Planned: {split_row.get('planned_mva')}")
                
                transformed_records.extend(split_rows)
            
            # Replace sheet_records with the transformed records
            sheet_records = transformed_records
            new_count = len(sheet_records)
            
            print(f"      [Summary] Original rows: {original_count}")
            print(f"      [Summary] After splitting: {new_count} rows ({new_count - original_count} new rows created)")
            
            # Show first 3 examples of transformed data
            print(f"\n      [*] First 3 transformed rows (example):")
            for i, rec in enumerate(sheet_records[:3], 1):
                voltage = rec.get('voltage_level_kv', 'N/A')
                existing = rec.get('existing_mva', 'N/A')
                under_impl = rec.get('under_implementation_mva', 'N/A')
                planned = rec.get('planned_mva', 'N/A')
                print(f"      {i}. {rec.get('substation', 'N/A'):30s} | Voltage: {voltage} kV | Existing: {existing} | Under Impl: {under_impl} | Planned: {planned}")
        
        # Apply post-processing cleaning for Non RE proposed RE Integration sheet
        if TEST_SHEET_NAME == "Non RE proposed RE Integration" and sheet_records:
            print(f"\n  [*] Post-processing Non RE proposed RE Integration sheet...")
            print(f"      - Cleaning station names (removing voltage levels, GIS/AIS, special chars)")
            print(f"      - Normalizing regional hub names to states")
            
            cleaned_count = 0
            state_normalized_count = 0
            
            for record in sheet_records:
                # Clean station name
                original_station = record.get('name_of_station', '')
                if original_station:
                    cleaned_station = clean_substation_name(original_station)
                    if cleaned_station != original_station:
                        cleaned_count += 1
                        if cleaned_count <= 5:  # Show first 5 examples
                            print(f"      [Clean] '{original_station}' → '{cleaned_station}'")
                    record['name_of_station'] = cleaned_station
                
                # Normalize state (convert regional hubs to actual states)
                original_state = record.get('state', '')
                if original_state:
                    normalized_state = normalize_regional_hub_to_state(original_state)
                    if normalized_state != original_state:
                        state_normalized_count += 1
                        if state_normalized_count <= 3:  # Show first 3 examples
                            print(f"      [State] '{original_state}' → '{normalized_state}'")
                    record['state'] = normalize_state_name(normalized_state)
            
            print(f"      [Summary] Cleaned {cleaned_count} station names")
            print(f"      [Summary] Normalized {state_normalized_count} state names")
        
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
                print(f"      Columns: {list(df.columns)[:10]}...")
                print(f"\n  [*] CSV Preview (first 3 rows):")
                print(df.head(3).to_string())
            except Exception as e:
                print(f"  [!] Error saving to CSV: {e}")
        
        # Write to Excel
        if sheet_records:
            print(f"\n  [*] Writing {len(sheet_records)} records to Excel sheet '{TEST_SHEET_NAME}'...")
            try:
                write_to_excel(sheet_records, TEMPLATE_EXCEL_FILE, OUTPUT_EXCEL_FILE, TEST_SHEET_NAME, clear_existing=True)
                print(f"  [OK] Successfully wrote data to '{TEST_SHEET_NAME}' in Excel")
            except Exception as e:
                print(f"  [!] Error writing to Excel: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"  [~] No records extracted for sheet '{TEST_SHEET_NAME}'. Check extraction logs above.")

    print(f"\n{'='*70}")
    print("=== TEST PIPELINE EXECUTION FINISHED ===")
    print(f"{'='*70}")
    print(f"\n[Output Files]")
    print(f"  - Excel: {OUTPUT_EXCEL_FILE}")
    print(f"  - CSVs in: extraction_output/")
    print(f"\n[Test Summary]")
    print(f"  - Sheets processed: {TEST_SHEETS}")
    print(f"  - Extraction method: {'Camelot (direct table extraction)' if all_sheets_used_camelot else 'LLM (text-based)'}")
    print(f"\n>> Review the CSV files first to validate data, then check the Excel output.")
    print(f"\n[Next steps]")
    print(f"  1. Open CSVs in Excel to verify all data is captured")
    print(f"  2. Check Excel output matches template format for each sheet")
    print(f"  3. If data looks good, update main.py with the same logic")


if __name__ == '__main__':
    run_test_pipeline()
