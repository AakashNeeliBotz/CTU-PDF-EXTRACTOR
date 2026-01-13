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
# LLM extraction removed - using Camelot/PyMuPDF table extraction only
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
    split_transformation_capacity_row,  # Add transformation capacity row splitter
    split_transformation_capacity_row,  # Add transformation capacity row splitter
    replace_multiplication_patterns  # Add multiplication pattern replacer for capacity calculations
)
from element_status_processor import ElementStatusProcessor  # Import the new processor
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


# =============================================================================
# SN1 EXTRACTION HELPER FUNCTIONS (Adapted from AkashNeeli's code)
# =============================================================================

# Rajasthan districts for state extraction
RAJASTHAN_DISTRICTS = [
    "Ajmer", "Alwar", "Banswara", "Baran", "Barmer", "Bharatpur", "Bhilwara",
    "Bikaner", "Bundi", "Chittorgarh", "Churu", "Dausa", "Dholpur", "Dungarpur",
    "Hanumangarh", "Jaipur", "Jaisalmer", "Jalore", "Jhalawar", "Jhunjhunu",
    "Jodhpur", "Karauli", "Kota", "Nagaur", "Pali", "Pratapgarh", "Rajsamand",
    "Sawai Madhopur", "Sikar", "Sirohi", "Sri Ganganagar", "Tonk", "Udaipur",
    "Balotra", "Beawar", "Kotputli-Behror", "Deeg", "Didwana-Kuchaman",
    "Khairthal-Tijara", "Phalodi", "Salumbar"
]

# Gujarat districts for state extraction
GUJARAT_DISTRICTS = [
    "Ahmedabad", "Amreli", "Anand", "Aravalli", "Banaskantha", "Bharuch", "Bhavnagar",
    "Botad", "Chhota Udaipur", "Dahod", "Dang", "Devbhoomi Dwarka", "Gandhinagar",
    "Gir Somnath", "Jamnagar", "Junagadh", "Kheda", "Kutch", "Mahisagar", "Mehsana",
    "Morbi", "Narmada", "Navsari", "Panchmahal", "Patan", "Porbandar", "Rajkot",
    "Sabarkantha", "Surat", "Surendranagar", "Tapi", "Vadodara", "Valsad"
]

# Header keywords for SN1 table detection
SN1_HEADER_KEYWORDS = ['sl', 'no', 'application', 'id', 'applicant', 'location', 'date',
                        'nature', 'quantum', 'connectivity', 'region', 'criterion', 'mode']


def normalize_roman_numerals(text):
    """
    Normalize Roman numerals in substation names to UPPERCASE.
    
    Examples:
    - 'Merta-Iii' → 'Merta-III'
    - 'Bhadla-Iv' → 'Bhadla-IV'
    - 'Ramgarh-Ii' → 'Ramgarh-II'
    - 'Fatehgarh-Vi' → 'Fatehgarh-VI'
    
    Args:
        text: String containing potential Roman numerals
        
    Returns:
        String with Roman numerals normalized to uppercase
    """
    import re
    
    if not text or not isinstance(text, str):
        return text
    
    def replace_roman(match):
        prefix = match.group(1)  # The hyphen/dash or space
        roman = match.group(2).upper()  # Convert to uppercase
        suffix = match.group(3) or ""  # Trailing part (space, end, etc.)
        return prefix + roman + suffix
    
    # Pattern: hyphen/dash/space followed by Roman numerals (mixed case)
    # Matches: -Iii, -IV, -ii, -Vi, etc. (case insensitive)
    # The Roman numeral must be at word boundary (end of string, followed by space, or non-letter)
    pattern = r'(-|–|\s)([IiVvXx]+)(\s|$|[^a-zA-Z])'
    
    return re.sub(pattern, replace_roman, text)


def fix_sn1_column_alignment(table_df):
    """
    Fix common column alignment issues in SN1 extracted tables.
    Handles cases where serial numbers get merged with application IDs.
    
    Args:
        table_df: pandas DataFrame from Camelot extraction
        
    Returns:
        pandas DataFrame with fixed alignment
    """
    df = table_df.copy()
    
    if df.shape[1] >= 2:
        for i in range(len(df)):
            first_col = str(df.iloc[i, 0]).strip() if not pd.isna(df.iloc[i, 0]) else ""
            second_col = str(df.iloc[i, 1]).strip() if not pd.isna(df.iloc[i, 1]) else ""
            
            # If first column is empty and second column contains "1. 2200000788" pattern
            if not first_col and "." in second_col:
                parts = second_col.split(".", 1)
                if len(parts) == 2 and parts[0].strip().isdigit():
                    df.iloc[i, 0] = parts[0].strip()
                    df.iloc[i, 1] = parts[1].strip()
            
            # If first column has merged serial number and data
            elif first_col and not second_col and "." in first_col:
                parts = first_col.split(".", 1)
                if len(parts) == 2 and parts[0].strip().isdigit():
                    df.iloc[i, 0] = parts[0].strip()
                    df.iloc[i, 1] = parts[1].strip()
    
    return df


def are_sn1_tables_related(df1, df2):
    """
    Check if two SN1 tables should be merged (continuation tables).
    Uses serial number continuity detection.
    
    Args:
        df1: First DataFrame
        df2: Second DataFrame
        
    Returns:
        bool: True if tables should be merged
    """
    try:
        # Check if tables have the same number of columns
        if df1.shape[1] != df2.shape[1]:
            return False
        
        if df1.shape[0] == 0 or df2.shape[0] == 0:
            return False
        
        # Find last serial number in df1
        last_serial = None
        for i in range(df1.shape[0] - 1, -1, -1):
            cell_value = str(df1.iloc[i, 0]).strip() if not pd.isna(df1.iloc[i, 0]) else ""
            # Remove period if present (e.g., "5." -> "5")
            cell_value = cell_value.rstrip('.')
            if cell_value.isdigit():
                last_serial = int(cell_value)
                break
        
        # Find first serial number in df2
        first_serial = None
        for i in range(min(5, df2.shape[0])):
            cell_value = str(df2.iloc[i, 0]).strip() if not pd.isna(df2.iloc[i, 0]) else ""
            cell_value = cell_value.rstrip('.')
            if cell_value.isdigit():
                first_serial = int(cell_value)
                break
        
        # Check if serial numbers are consecutive
        if last_serial is not None and first_serial is not None:
            if first_serial == last_serial + 1:
                return True
        
        return False
        
    except Exception as e:
        print(f"      [!] Error checking table relation: {e}")
        return False


def remove_sn1_repeated_headers(df):
    """
    Remove repeated header rows from a merged SN1 DataFrame.
    
    Args:
        df: pandas DataFrame
        
    Returns:
        DataFrame with repeated headers removed
    """
    if df.shape[0] <= 1:
        return df
    
    # Get the first row as reference header
    header_row = df.iloc[0].tolist()
    
    rows_to_drop = []
    for i in range(1, df.shape[0]):
        current_row = df.iloc[i].tolist()
        
        if len(current_row) == len(header_row):
            matching_cells = 0
            total_non_empty = 0
            
            for j in range(len(header_row)):
                header_cell = str(header_row[j]).strip()
                current_cell = str(current_row[j]).strip()
                
                if header_cell:
                    total_non_empty += 1
                    if header_cell == current_cell:
                        matching_cells += 1
            
            # If more than 80% match, it's a repeated header
            if total_non_empty > 0 and (matching_cells / total_non_empty) > 0.8:
                rows_to_drop.append(i)
    
    if rows_to_drop:
        df = df.drop(df.index[rows_to_drop]).reset_index(drop=True)
        print(f"      [SN1] Removed {len(rows_to_drop)} repeated header rows")
    
    return df


def merge_sn1_related_tables(table_dfs):
    """
    Merge related SN1 tables that are continuations of each other.
    
    Args:
        table_dfs: List of DataFrames from Camelot extraction
        
    Returns:
        List of merged DataFrames
    """
    if not table_dfs:
        return []
    
    merged_tables = []
    i = 0
    
    while i < len(table_dfs):
        current_df = table_dfs[i].copy()
        merged = False
        
        j = i + 1
        while j < len(table_dfs):
            if are_sn1_tables_related(current_df, table_dfs[j]):
                # Merge tables
                current_df = pd.concat([current_df, table_dfs[j]], ignore_index=True)
                current_df = remove_sn1_repeated_headers(current_df)
                merged = True
                j += 1
            else:
                break
        
        # Also remove repeated headers from standalone tables
        current_df = remove_sn1_repeated_headers(current_df)
        merged_tables.append(current_df)
        
        if merged:
            i = j
        else:
            i += 1
    
    print(f"      [SN1] Merged {len(table_dfs)} tables into {len(merged_tables)} logical tables")
    return merged_tables


def detect_sn1_header_row(df):
    """
    Detect which row contains the header in an SN1 table.
    
    Args:
        df: pandas DataFrame
        
    Returns:
        Tuple of (header_row_index, column_mapping dict)
    """
    column_mapping = {}
    header_row_idx = None
    
    for row_idx in range(min(10, len(df))):
        row = df.iloc[row_idx]
        row_values = [str(cell).strip().lower().replace('\n', ' ') if not pd.isna(cell) else "" for cell in row]
        
        # Count how many header keywords are found
        header_matches = sum(1 for cell in row_values[:10] 
                           if any(keyword in cell for keyword in SN1_HEADER_KEYWORDS))
        
        if header_matches >= 2:
            header_row_idx = row_idx
            
            # Create column mapping
            for j, cell in enumerate(row_values):
                cell_clean = cell.lower()
                if ('sl' in cell_clean and 'no' in cell_clean) or 'serial' in cell_clean:
                    column_mapping['serial'] = j
                elif 'application' in cell_clean and 'id' in cell_clean:
                    column_mapping['app_id'] = j
                elif 'project' in cell_clean and 'location' in cell_clean:
                    column_mapping['location'] = j
                elif 'submission' in cell_clean and 'date' in cell_clean:
                    column_mapping['submission_date'] = j
                elif 'region' in cell_clean and 'date' not in cell_clean and 'gnare' not in cell_clean:
                    column_mapping['region'] = j
                elif 'nature' in cell_clean and 'applicant' in cell_clean:
                    column_mapping['nature_applicant'] = j
                elif 'quantum' in cell_clean and 'mw' in cell_clean:
                    column_mapping['quantum'] = j
                elif ('start' in cell_clean and 'date' in cell_clean) or ('start' in cell_clean and 'connectivity' in cell_clean):
                    column_mapping['start_date'] = j
                elif 'applicant' in cell_clean and 'nature' not in cell_clean:
                    column_mapping['applicant'] = j
                elif 'criterion' in cell_clean or 'mode' in cell_clean:
                    column_mapping['criterion'] = j
                elif 'connectivity' in cell_clean and 'location' in cell_clean:
                    column_mapping['connectivity_location'] = j
            
            break
    
    return header_row_idx, column_mapping


def extract_state_from_location(location_text):
    """
    Extract state name from project location text.
    Handles district-to-state mapping for Rajasthan and Gujarat.
    
    Args:
        location_text: Raw location string from PDF
        
    Returns:
        State name or the original location if no state detected
    """
    if not location_text or pd.isna(location_text):
        return ""
    
    location_str = str(location_text).strip()
    
    # Check for direct state mention
    location_lower = location_str.lower()
    if 'rajasthan' in location_lower:
        return 'Rajasthan'
    if 'gujarat' in location_lower:
        return 'Gujarat'
    if 'maharashtra' in location_lower:
        return 'Maharashtra'
    if 'karnataka' in location_lower:
        return 'Karnataka'
    if 'tamil nadu' in location_lower:
        return 'Tamil Nadu'
    if 'andhra pradesh' in location_lower:
        return 'Andhra Pradesh'
    if 'telangana' in location_lower:
        return 'Telangana'
    if 'madhya pradesh' in location_lower:
        return 'Madhya Pradesh'
    
    # Check for Rajasthan districts
    for district in RAJASTHAN_DISTRICTS:
        if district.lower() in location_lower:
            return 'Rajasthan'
    
    # Check for Gujarat districts
    for district in GUJARAT_DISTRICTS:
        if district.lower() in location_lower:
            return 'Gujarat'
    
    # If comma-separated, take last part (might be state)
    if ',' in location_str:
        last_part = location_str.split(',')[-1].strip()
        # Check if it's a known state
        normalized = normalize_state_name(last_part)
        if normalized and normalized != last_part:
            return normalized
        return last_part
    
    return location_str


def detect_status_for_developer(df, current_row_idx, developer_name):
    """
    Detect status (Withdrawn/Granted/Revoked) for a specific developer.
    Only matches status if it's associated with the same developer.
    
    Args:
        df: pandas DataFrame
        current_row_idx: Current data row index
        developer_name: Name of the developer to match
        
    Returns:
        Status string or empty string if not found
    """
    if not developer_name:
        return ""
    
    developer_lower = developer_name.lower().strip()
    # Extract key words from developer name for matching (first 2-3 significant words)
    dev_words = [w for w in developer_lower.split() if len(w) > 3][:3]
    
    status_keywords = {
        'withdrawn': 'Withdrawn',
        'closed': 'Withdrawn',
        'granted': 'Granted',
        'agreed': 'Granted',
        'revoked': 'Revoked'
    }
    
    # Look ahead up to 7 rows, but stop if we hit another serial number
    for j in range(1, min(8, len(df) - current_row_idx)):
        next_row = df.iloc[current_row_idx + j]
        
        # Check if we've hit the next record (new serial number)
        first_cell = str(next_row.iloc[0]).strip() if not pd.isna(next_row.iloc[0]) else ""
        first_cell_clean = first_cell.rstrip('.')
        if first_cell_clean.isdigit():
            # We've reached the next record, stop looking
            break
        
        # Combine all cells in the row for checking
        row_text = ' '.join([str(cell).lower() if not pd.isna(cell) else "" for cell in next_row])
        
        # Check if developer name (or key words) appears in this row
        developer_mentioned = any(word in row_text for word in dev_words) if dev_words else True
        
        # If developer is mentioned (or no developer name to check), look for status
        if developer_mentioned:
            for keyword, status in status_keywords.items():
                if keyword in row_text:
                    return status
    
    return ""


def process_sn1_quantum_value(quantum_str):
    """
    Process quantum value to separate application quantum from granted quantum.
    E.g., "300 (reduced to 250)" -> ("300", "(reduced to 250)")
    
    Args:
        quantum_str: Raw quantum string
        
    Returns:
        Tuple of (application_quantum, granted_quantum)
    """
    import re
    
    if not quantum_str or pd.isna(quantum_str):
        return "", ""
    
    quantum_str = str(quantum_str).strip()
    
    # Normalize whitespace
    normalized = re.sub(r'\s+', ' ', quantum_str)
    
    # Pattern to match "NUMBER (text)" format
    match = re.search(r'^([.\d]+(?:\s*[.\d]+)*)\s*\(([^)]+)\).*$', normalized)
    if match:
        app_quantum = match.group(1).strip()
        granted_quantum = "(" + match.group(2).strip() + ")"
        return app_quantum, granted_quantum
    
    # No parentheses, return original as application quantum
    return quantum_str, ""


def extract_sn1_substation_from_text(pdf_text, developer_name):
    """
    Extract confirmed substation for a developer from PDF narrative text.
    Only extracts substation when there's confirmation (agreed, granted, approved).
    
    IMPORTANT: Uses STRICT developer matching to prevent cross-contamination.
    Captures full substation names including parenthetical text like "Sirohi(HVDC) PS".
    
    Args:
        pdf_text: Raw text from PDF (all pages or relevant sections)
        developer_name: Name of developer to match
        
    Returns:
        Substation name if confirmed, empty string otherwise
    """
    import re
    
    if not pdf_text or not developer_name:
        return ""
    
    # Normalize developer name - extract key words for STRICT matching
    dev_lower = developer_name.lower().strip()
    # Remove common prefixes
    dev_lower = re.sub(r'^m/s\.?\s*', '', dev_lower)
    dev_lower = re.sub(r'^(messrs|shri|sri|smt)\.?\s*', '', dev_lower)
    
    # Get key words (ignore common words)
    stop_words = {'and', 'the', 'pvt', 'ltd', 'private', 'limited', 'india', 'llp', 
                  'energy', 'power', 'solar', 'wind', 'renewable', 'renewables', 'green',
                  'company', 'corporation', 'enterprises', 'industries', 'group', 'holdings'}
    dev_words = [w for w in dev_lower.split() if len(w) > 2 and w not in stop_words]
    
    if len(dev_words) < 1:
        # Fallback: use any word > 3 chars (but not common words)
        dev_words = [w for w in dev_lower.split() if len(w) > 3 and w not in stop_words][:2]
    
    if len(dev_words) < 1:
        return ""
    
    # The FIRST TWO distinctive words are crucial for matching
    # E.g., 'acme solar' vs 'acme sunny' - must match BOTH words
    first_key_word = dev_words[0] if dev_words else ""
    second_key_word = dev_words[1] if len(dev_words) > 1 else ""
    
    # Check pre-computed cache first (much faster)
    cache_key = '_sn1_substation_cache'
    if hasattr(extract_sn1_substation_from_text, cache_key):
        cache = getattr(extract_sn1_substation_from_text, cache_key)
        # Try to find developer in cache with VERY STRICT matching
        for cached_dev, cached_substation in cache.items():
            cached_lower = cached_dev.lower()
            # STRICT: First key word must be present
            if first_key_word and first_key_word in cached_lower:
                # If we have a second key word, it MUST also be present
                if second_key_word:
                    if second_key_word in cached_lower:
                        return cached_substation
                    # else: don't match - second word is different
                else:
                    # Only one key word - match if present
                    return cached_substation
        return ""
    
    # First time - build the cache by scanning text ONCE
    cache = {}
    withdrawn_developers = set()  # Track developers who withdrew their applications
    
    # Normalize text for searching
    text_lower = pdf_text.lower()
    text_normalized = re.sub(r'\s+', ' ', text_lower)  # Normalize whitespace
    
    # STEP 1: First detect WITHDRAWN applications - these should NOT get substations
    # Pattern: "M/s [Developer] has withdrawn" or "M/s [Developer] ... withdrawn their application"
    withdrawn_patterns = [
        r'm/s\.?\s*([^,]+?)\s+(?:has\s+)?withdrawn',
        r'm/s\.?\s*([^,]+?)\s+[^.]*?withdrawn\s+(?:their|the)\s+application',
        r'withdrawn[^.]*?(?:by\s+)?m/s\.?\s*([^,]+)',
    ]
    
    for pattern in withdrawn_patterns:
        for match in re.finditer(pattern, text_normalized, re.IGNORECASE):
            withdrawn_dev = match.group(1).strip().lower()
            if withdrawn_dev and len(withdrawn_dev) > 3:
                withdrawn_developers.add(withdrawn_dev)
    
    # STEP 2: ENHANCED patterns that capture:
    # 1. Parenthetical suffixes like (HVDC), (PG), etc.
    # 2. Full substation suffix (PS, S/S, etc.)
    # Substation pattern: Name + optional(parenthetical) + suffix
    # Examples: Sirohi(HVDC) PS, Ramgarh-II PS, Bhadla-IV S/S
    substation_pattern = r'([A-Za-z][A-Za-z0-9\-]+(?:[\-][IVXivx]+)?(?:\s*\([A-Za-z0-9]+\))?)\s*(ps|p\.s\.|s/s|substation|pooling\s*station)'
    
    # Trigger words that indicate a confirmed/proposed grant
    # Captures: agreed to grant, proposed to grant, decided to grant, granted, approved
    grant_triggers = r'(?:agreed|proposed|decided)\s+to\s+grant|granted|approved'
    
    # Multiple patterns to catch different sentence structures
    confirmed_patterns = [
        # Pattern 1: "[trigger] X MW connectivity to M/s [Developer] at [kV] [Substation] PS"
        # Example: "agreed to grant 150 MW connectivity to M/s Adani at Bhadla-IV PS"
        r'(?:' + grant_triggers + r')\s+[\d,]+\s*mw\s+connectivity[^.]*?(?:to\s+)?m/s\.?\s*([^,]+?)\s+at\s+(?:\d+(?:/\d+)?\s*k[vV]\s+)?' + substation_pattern,
        
        # Pattern 2: "[trigger] connectivity of X MW to M/s [Developer] at [kV] [Substation] PS"
        # Example: "proposed to grant connectivity of 150 MW to M/s Adani at 400 kV Bhadla-IV PS"
        r'(?:' + grant_triggers + r')\s+connectivity\s+of\s+[\d,]+\s*mw[^.]*?(?:to\s+)?m/s\.?\s*([^,]+?)\s+at\s+(?:\d+(?:/\d+)?\s*k[vV]\s+)?' + substation_pattern,
        
        # Pattern 3: "[trigger] X MW [anything] to M/s [Developer] at [Substation]"
        # Example: "agreed to grant 350 MW connectivity to M/s Amplus Centaur at Sirohi(HVDC) PS"
        r'(?:' + grant_triggers + r')\s+[\d,]+\s*mw[^.]*?(?:to\s+)?m/s\.?\s*([^,]+?)\s+at\s+(?:\d+(?:/\d+)?\s*k[vV]\s+)?' + substation_pattern,
        
        # Pattern 4: "connectivity to M/s [Developer] at [kV] [Substation] PS" (simpler, when grant is nearby)
        r'connectivity[^.]*?to\s+m/s\.?\s*([^,]+?)\s+at\s+(?:\d+\s*k[vV]\s+)?' + substation_pattern,
        
        # Pattern 5: "grant [anything] to M/s [Developer] [anything] at [Substation]"
        # Catches more flexible sentence structures
        r'grant[^.]*?to\s+m/s\.?\s*([^,]+?)[^.]*?\s+at\s+(?:\d+(?:/\d+)?\s*k[vV]\s+)?' + substation_pattern,
        
        # Pattern 6: REVERSED ORDER - "M/s [Developer] was [earlier] granted connectivity [of X MW] at [of] [Substation]"
        # Example: "M/s Adani Renewable Energy Holding Four Limited was earlier granted connectivity of 765 MW at of Bhadla-IV PS"
        # Note: handles typo "at of" in PDF
        r'm/s\.?\s*([^,\(]+?)(?:\s*\([^)]+\))?\s+was\s+(?:earlier\s+)?(?:granted|approved)\s+connectivity[^.]*?\s+at\s+(?:of\s+)?(?:\d+\s*k[vV]\s+)?' + substation_pattern,
        
        # Pattern 7: REVERSED ORDER simpler - "M/s [Developer] [anything] granted [anything] at [Substation]"
        r'm/s\.?\s*([^,\(]+?)(?:\s*\([^)]+\))?[^.]*?(?:granted|approved)[^.]*?\s+at\s+(?:of\s+)?(?:\d+\s*k[vV]\s+)?' + substation_pattern,
    ]
    
    for pattern in confirmed_patterns:
        for match in re.finditer(pattern, text_normalized, re.IGNORECASE):
            developer = match.group(1).strip()
            substation_name = match.group(2).strip().rstrip('-')
            substation_suffix = match.group(3).strip().upper()  # PS, S/S, etc.
            
            if developer and substation_name and len(substation_name) > 2:
                # Check if this developer has withdrawn - if so, skip
                dev_lower = developer.lower()
                is_withdrawn = any(wd in dev_lower or dev_lower in wd for wd in withdrawn_developers)
                if is_withdrawn:
                    continue  # Skip - this developer withdrew
                
                # Build full substation name with suffix
                # Normalize suffix: s/s -> S/S, ps -> PS
                if substation_suffix.lower() in ['ps', 'p.s.']:
                    substation_suffix = 'PS'
                elif substation_suffix.lower() == 's/s':
                    substation_suffix = 'S/S'
                elif 'substation' in substation_suffix.lower():
                    substation_suffix = 'Substation'
                elif 'pooling' in substation_suffix.lower():
                    substation_suffix = 'Pooling Station'
                
                # Apply Roman numeral normalization and build full name
                full_substation = normalize_roman_numerals(substation_name.title()) + " " + substation_suffix
                cache[developer] = full_substation
    
    # Store cache for future calls
    setattr(extract_sn1_substation_from_text, cache_key, cache)
    
    # Now look up this developer with VERY STRICT matching
    for cached_dev, cached_substation in cache.items():
        cached_lower = cached_dev.lower()
        # STRICT: First key word must be present
        if first_key_word and first_key_word in cached_lower:
            # If we have a second key word, it MUST also be present
            if second_key_word:
                if second_key_word in cached_lower:
                    return cached_substation
                # else: don't match - second word is different
            else:
                return cached_substation
    
    return ""


def extract_agreed_substation_from_dtl(pdf_text, developer_name):
    """
    Extract the agreed substation from the DTL section (B. Transmission System under applicant scope).
    
    For developers who are GRANTED connectivity, the actually agreed substation often differs
    from the applied substation (shown in the table column). The agreed substation appears in
    the DTL section in patterns like:
    "M/s Developer Name Solar Power Project – Bikaner-V PS 220 kV"
    
    Args:
        pdf_text: Raw PDF text
        developer_name: Name of the developer
        
    Returns:
        Agreed substation name if found, empty string otherwise
    """
    import re
    
    if not pdf_text or not developer_name:
        return ""
    
    # Normalize developer name for matching
    dev_lower = developer_name.lower().strip()
    dev_lower = re.sub(r'^m/s\.?\s*', '', dev_lower)
    dev_lower = re.sub(r'\s*\(erstwhile[^)]*\)', '', dev_lower)
    
    # Get key words for matching
    stop_words = {'and', 'the', 'pvt', 'ltd', 'private', 'limited', 'india', 'llp', 
                  'energy', 'power', 'solar', 'wind', 'renewable', 'renewables', 'green',
                  'project', 'projects', 'holding', 'holdings', 'company', 'corporation'}
    dev_words = [w for w in dev_lower.split() if len(w) > 2 and w not in stop_words][:3]
    
    if not dev_words:
        return ""
    
    text_normalized = re.sub(r'\s+', ' ', pdf_text.lower())
    
    # Find the DTL section (B. Transmission System under applicant scope) for this developer
    # Pattern: Look for developer name followed by "Project" and then substation pattern
    # Example: "M/s Juniper Green Energy Private Limited Solar Power Project – Bikaner-V PS 220 kV"
    
    # Build pattern to find developer + project + substation
    dev_pattern = r'm/s\.?\s+[^–\-]*?' + re.escape(dev_words[0])
    if len(dev_words) > 1:
        dev_pattern += r'[^–\-]*?' + re.escape(dev_words[1])
    
    # Pattern to capture substation after developer name and project mention
    # Substation patterns: "Bikaner-V PS", "Barmer-III PS", "Bhadla-IV PS", etc.
    substation_pattern = dev_pattern + r'[^–\-]*?(?:project\s*[–\-]\s*|project\s+at\s+)?([a-z]+[\-\s]*[ivxlcdm\d]+\s*(?:ps|p\.s\.|pooling\s*station|substation|s/s))'
    
    match = re.search(substation_pattern, text_normalized, re.IGNORECASE)
    if match:
        substation = match.group(1).strip()
        # Clean up and normalize
        substation = re.sub(r'\s+', ' ', substation)
        substation = substation.upper()
        # Format consistently: "Bikaner-V PS"
        substation = re.sub(r'(\w+)\s*[\-\s]\s*([IVXLCDM\d]+)\s*(PS|P\.S\.|POOLING STATION|SUBSTATION|S/S)', 
                           r'\1-\2 \3', substation)
        return substation
    
    # Fallback: Look for "agreed to grant ... connectivity ... at ... PS" pattern  
    # Example: "Accordingly, it was agreed to grant 400 MW connectivity to M/s Juniper Green Energy Private Limited at 220 kV Bikaner-V PS"
    agreed_pattern = r'agreed\s+to\s+grant[^.]*?' + re.escape(dev_words[0]) + r'[^.]*?at\s+(?:\d+\s*kv\s+)?([a-z]+[\-\s]*[ivxlcdm\d]+\s*(?:ps|p\.s\.|pooling\s*station))'
    
    match = re.search(agreed_pattern, text_normalized, re.IGNORECASE)
    if match:
        substation = match.group(1).strip()
        substation = re.sub(r'\s+', ' ', substation)
        substation = substation.upper()
        substation = re.sub(r'(\w+)\s*[\-\s]\s*([IVXLCDM\d]+)\s*(PS|P\.S\.|POOLING STATION)', 
                           r'\1-\2 \3', substation)
        return substation
    
    return ""




def extract_agreed_substation_from_dtl(pdf_text, developer_name):
    """
    Extract the agreed substation for a developer from the DTL section of PDF text.
    
    This function finds the developer's specific section in the PDF and extracts the 
    substation mentioned in the "Transmission System under applicant scope" (DTL) section,
    which represents the AGREED substation (vs the APPLIED substation from the table).
    
    Args:
        pdf_text: Raw PDF text
        developer_name: Name of developer
        
    Returns:
        String containing the agreed substation name, or None if not found
    """
    import re
    
    if not pdf_text or not developer_name:
        return None
    
    # Normalize developer name for matching - be more strict
    dev_lower = developer_name.lower().strip()
    dev_lower = re.sub(r'^m/s\.?\s*', '', dev_lower)
    # Remove common suffixes and prefixes
    dev_lower = re.sub(r'\s*\(erstwhile[^)]*\)', '', dev_lower)  # Remove (erstwhile...) clauses
    
    # Get key words for matching - require at least 2 unique words for better accuracy
    stop_words = {'and', 'the', 'pvt', 'ltd', 'private', 'limited', 'india', 'llp', 
                  'energy', 'power', 'solar', 'wind', 'renewable', 'renewables', 'green',
                  'project', 'projects', 'holding', 'holdings', 'company', 'corporation'}
    dev_words = [w for w in dev_lower.split() if len(w) > 2 and w not in stop_words]
    
    # Ensure we have at least 2 unique identifying words
    if len(dev_words) < 2:
        # Try to use the first 2 words regardless of length
        dev_words = [w for w in dev_lower.split() if w not in stop_words][:2]
    
    if not dev_words:
        return None
    
    text_lower = pdf_text.lower()
    text_normalized = re.sub(r'\s+', ' ', text_lower)
    
    # Find sections for this developer - STRICT matching requiring multiple words
    # Look for patterns like "M/s Developer Name ... Details of Transmission"
    
    section_start = -1
    section_end = -1
    
    # Build a pattern that requires BOTH first two key words to appear in order
    if len(dev_words) >= 2:
        # Stricter pattern: both words must appear with some flexibility
        section_pattern = rf'm/s\.?\s+[^.]*{re.escape(dev_words[0])}[^.]*{re.escape(dev_words[1])}[^.]*?details\s+of\s+transmission'
    else:
        section_pattern = rf'm/s\.?\s+[^.]*{re.escape(dev_words[0])}[^.]*?details\s+of\s+transmission'
    
    for match in re.finditer(section_pattern, text_normalized, re.IGNORECASE):
        section_start = match.start()
        # Find end of section (next "M/s" developer declaration or page break)
        next_section = re.search(r'm/s\.?\s+\w+.*?details\s+of\s+transmission|page\s+\d+\s+of\s+\d+', 
                                  text_normalized[match.end():match.end() + 5000], re.IGNORECASE)
        if next_section:
            section_end = match.end() + next_section.start()
        else:
            section_end = match.end() + 3000
        break
    
    if section_start == -1:
        # Fallback: Look for "Details of Transmission system" followed by the developer name
        # This pattern finds developer-specific sections more accurately
        details_pattern = r'details\s+of\s+transmission\s+system\s+for\s+connectivity\s+under\s+gna'
        
        for match in re.finditer(details_pattern, text_normalized):
            # Check if this developer's name appears shortly before/after this section header
            context_before = text_normalized[max(0, match.start()-400):match.start()]
            context_after = text_normalized[match.end():match.end()+200]
            
            # Count how many key words match in the context
            words_found = sum(1 for w in dev_words[:3] if w in context_before or w in context_after)
            
            # Require at least 2 matching words for a valid match
            if words_found >= min(2, len(dev_words)):
                section_start = match.start()
                # Find end of section
                next_section = re.search(r'details\s+of\s+transmission|page\s+\d+\s+of\s+\d+', 
                                          text_normalized[match.end()+100:match.end() + 5000])
                if next_section:
                    section_end = match.end() + 100 + next_section.start()
                else:
                    section_end = match.end() + 3000
                break
    
    if section_start == -1:
        return None
    
    section_text = text_normalized[section_start:section_end]
    
    # Extract DTL (Transmission System under applicant scope) to find agreed substation
    dtl_pattern = r'transmission\s+system\s+under\s+applicant\s+scope\s*[:\-]?\s*(?:\([^)]*\)\s*)?(.+?)(?=c\.|transmission\s+system\s+for\s+connectivity|$)'
    dtl_match = re.search(dtl_pattern, section_text, re.IGNORECASE | re.DOTALL)
    if dtl_match:
        dtl_text = dtl_match.group(1).strip()
        
        # --- Extract Agreed Substation from DTL text ---
        # Look for pattern: "... Project – [Substation Name] ..."
        # OR "... Project at [Substation Name] ..."
        substation_pattern = r'(?:project\s*[–\-\u2013]\s*|project\s+at\s+)([a-z]+[\-\s]*[ivxlcdm\d]+\s*(?:ps|p\.s\.|pooling\s*station|substation|s/s))'
        sub_match = re.search(substation_pattern, dtl_text, re.IGNORECASE)
        if sub_match:
            return sub_match.group(1).strip()
    
    return None


def extract_sn1_records_from_table(df, column_mapping, header_row_idx, canonical_fields, pdf_text=""):
    """
    Extract records from an SN1 table using the detected column mapping.
    
    Args:
        df: pandas DataFrame
        column_mapping: Dictionary mapping field names to column indices
        header_row_idx: Index of the header row
        canonical_fields: List of expected field names
        pdf_text: Raw text from PDF for substation extraction (optional)
        
    Returns:
        List of record dictionaries
    """
    records = []
    
    # Start from row after header
    start_row = header_row_idx + 1 if header_row_idx is not None else 0
    
    for i in range(start_row, len(df)):
        row = df.iloc[i]
        
        # Check if this is a data row (starts with serial number)
        first_cell = str(row.iloc[0]).strip() if not pd.isna(row.iloc[0]) else ""
        first_cell_clean = first_cell.rstrip('.')
        
        if not first_cell_clean.isdigit():
            continue  # Skip non-data rows
        
        record = {field: "" for field in canonical_fields}
        
        # Extract serial number
        sr_no = first_cell_clean
        record['sr_no'] = sr_no
        
        # Extract Application ID
        app_id = ""
        app_id_col = column_mapping.get('app_id')
        if app_id_col is not None and len(row) > app_id_col and not pd.isna(row.iloc[app_id_col]):
            app_id = str(row.iloc[app_id_col]).strip()
        elif len(row) > 1 and not pd.isna(row.iloc[1]):
            app_id = str(row.iloc[1]).strip()
        
        # Route to GNA or LTA based on whether it's numeric
        app_id_clean = app_id.replace('.', '', 1).replace(' ', '')
        if app_id_clean.isdigit():
            record['gna_st_ii_application_id'] = app_id
            record['lta_application_id'] = ""
        else:
            record['lta_application_id'] = app_id
            record['gna_st_ii_application_id'] = ""
        
        # Extract Project Location / Region
        location = ""
        location_col = column_mapping.get('location') or column_mapping.get('region')
        if location_col is not None and len(row) > location_col and not pd.isna(row.iloc[location_col]):
            location = str(row.iloc[location_col]).strip()
        elif len(row) > 3 and not pd.isna(row.iloc[3]):
            location = str(row.iloc[3]).strip()
        
        # Extract state from location and map to region code
        state = extract_state_from_location(location)
        record['state'] = state
        # Map state to region code (NR, WR, SR, ER, NER)
        record['region'] = infer_region_from_state(state)
        
        # Extract Applicant / Name of Developers
        applicant = ""
        applicant_col = column_mapping.get('applicant')
        if applicant_col is not None and len(row) > applicant_col and not pd.isna(row.iloc[applicant_col]):
            applicant = str(row.iloc[applicant_col]).strip()
        elif len(row) > 2 and not pd.isna(row.iloc[2]):
            applicant = str(row.iloc[2]).strip()
        record['name_of_developers'] = applicant
        
        # Extract Submission Date
        submission_date = ""
        date_col = column_mapping.get('submission_date')
        if date_col is not None and len(row) > date_col and not pd.isna(row.iloc[date_col]):
            submission_date = str(row.iloc[date_col]).strip()
        elif len(row) > 4 and not pd.isna(row.iloc[4]):
            submission_date = str(row.iloc[4]).strip()
        record['application_date'] = submission_date
        
        # Extract Nature of Applicant
        nature = ""
        nature_col = column_mapping.get('nature_applicant')
        if nature_col is not None and len(row) > nature_col and not pd.isna(row.iloc[nature_col]):
            nature = str(row.iloc[nature_col]).strip()
        elif len(row) > 5 and not pd.isna(row.iloc[5]):
            nature = str(row.iloc[5]).strip()
        record['nature_of_applicant'] = nature
        
        # Extract Quantum (MW)
        quantum = ""
        quantum_col = column_mapping.get('quantum')
        if quantum_col is not None and len(row) > quantum_col and not pd.isna(row.iloc[quantum_col]):
            quantum = str(row.iloc[quantum_col]).strip()
        elif len(row) > 7 and not pd.isna(row.iloc[7]):
            quantum = str(row.iloc[7]).strip()
        
        app_quantum, granted_quantum = process_sn1_quantum_value(quantum)
        record['application_quantum_mw'] = app_quantum
        record['granted_quantum_gna_lta_mw'] = granted_quantum
        
        # Extract Start Date of Connectivity
        start_date = ""
        start_date_col = column_mapping.get('start_date')
        if start_date_col is not None and len(row) > start_date_col and not pd.isna(row.iloc[start_date_col]):
            start_date = str(row.iloc[start_date_col]).strip()
        elif len(row) > 8 and not pd.isna(row.iloc[8]):
            start_date = str(row.iloc[8]).strip()
        record['applied_start_of_connectivity'] = start_date
        
        # Extract Criterion/Mode
        criterion = ""
        criterion_col = column_mapping.get('criterion')
        if criterion_col is not None and len(row) > criterion_col and not pd.isna(row.iloc[criterion_col]):
            criterion = str(row.iloc[criterion_col]).strip()
        else:
            # Fallback: check columns 6-7 for criterion keywords
            for col_idx in range(6, min(8, len(row))):
                if not pd.isna(row.iloc[col_idx]):
                    cell_value = str(row.iloc[col_idx]).strip()
                    if any(kw in cell_value.lower() for kw in ['land', 'route', 'bg']):
                        criterion = cell_value
                        break
        record['mode'] = criterion
        
        # Detect Status (with developer name verification)
        status = detect_status_for_developer(df, i, applicant)
        record['status_of_application'] = status
        
        # Extract Substation - PRIORITY order:
        # 1. For GRANTED developers: Check DTL section for agreed substation
        # 2. Table column "Connectivity location (As per Application)" 
        # 3. Fallback: Text extraction from narrative
        substation = ""
        applied_substation = ""  # Track what was in the table
        
        # Step 1: Get substation from table column (this is the APPLIED substation)
        conn_loc_col = column_mapping.get('connectivity_location')
        if conn_loc_col is not None and len(row) > conn_loc_col and not pd.isna(row.iloc[conn_loc_col]):
            table_substation = str(row.iloc[conn_loc_col]).strip()
            # Check if it looks like a valid substation format (contains PS, S/S, etc.)
            substation_indicators = ['ps', 'p.s.', 's/s', 'substation', 'pooling', 'power']
            if any(ind in table_substation.lower() for ind in substation_indicators):
                # Valid substation from table - use it (apply Roman numeral normalization)
                applied_substation = normalize_roman_numerals(table_substation)
                substation = applied_substation
        
        # Step 2: Check DTL section for the AGREED substation
        # We check even if status is empty, as DTL presence implies active application
        if (status == 'Granted' or not status) and pdf_text and applicant:
            agreed_sub = extract_agreed_substation_from_dtl(pdf_text, applicant)
            if agreed_sub:
                # Found agreed substation in DTL - use this instead of applied
                substation = normalize_roman_numerals(agreed_sub)
        
        # Step 3: Fallback to text extraction if we still don't have a substation
        if not substation and pdf_text and applicant:
            substation = extract_sn1_substation_from_text(pdf_text, applicant)
        
        if substation:
            record['substation'] = substation
        
        records.append(record)
    
    return records


# --- Test Configuration ---
BASE_DOWNLOAD_DIR = "downloaded_pdfs"
TEMPLATE_EXCEL_FILE = "Connectivity Application Data.xlsx"
OUTPUT_EXCEL_FILE = "Connectivity_Application_Data_TEST_ALL_SHEETS35.xlsx"
MAX_WORKERS = 1  # Set to 1 to avoid pypdfium2 threading issues on Windows

# Test Settings: Process multiple sheets from different sources
TEST_SHEETS = ["Data to be captured", "Margin", "Transformation Capacity", "Non RE proposed RE Integration", "Element Status"]  # All sheets to test
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


def process_pdf_file(pdf_path, sheet_name):
    """Extract data from PDF using Camelot table extraction."""
    try:
        print(f"\n    - Processing file: {os.path.basename(pdf_path)}")
        
        # -------------------------------------------------------------------------
        # SPECIAL HANDLING FOR ELEMENT STATUS SHEET
        # -------------------------------------------------------------------------
        if sheet_name == "Element Status":
             print(f"      [!] Using specialized Element Status Processor for {os.path.basename(pdf_path)}")
             try:
                 # Helper to access output file path - it's global
                 output_file = OUTPUT_EXCEL_FILE 
                 
                 # Ensure output file exists (copy from template if needed)
                 if not os.path.exists(output_file):
                     import shutil
                     template_file = TEMPLATE_EXCEL_FILE
                     if os.path.exists(template_file):
                         shutil.copy2(template_file, output_file)
                         print(f"      [OK] Created output file from template: {output_file}")
                     else:
                         print(f"      [!] Error: Template file {template_file} not found!")
                 
                 processor = ElementStatusProcessor()
                 processor.process_and_write(pdf_path, output_file)
                 print(f"      [OK] Element Status processing completed for {os.path.basename(pdf_path)}")
                 # Return empty DataFrame so main loop skips standard processing/writing
                 return pd.DataFrame()
             except Exception as e:
                 print(f"      [!] Element Status specialized processing failed: {e}")
                 import traceback
                 traceback.print_exc()
                 return pd.DataFrame()

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
        
        # =============================================================================
        # SN1-SPECIFIC EXTRACTION (CMETS Meeting Minutes PDFs)
        # =============================================================================
        if folder_name == "SN1" and sheet_name == "Data to be captured":
            print(f"      [SN1] Detected SN1 PDF for 'Data to be captured' sheet")
            print(f"      [SN1] Using specialized extraction (pages 11-end, table merging)")
            
            try:
                import camelot
                import fitz  # PyMuPDF for text extraction
                
                # Clear substation cache for this new PDF
                if hasattr(extract_sn1_substation_from_text, '_sn1_substation_cache'):
                    delattr(extract_sn1_substation_from_text, '_sn1_substation_cache')
                
                # Extract raw text from PDF for substation matching
                pdf_text = ""
                try:
                    doc = fitz.open(pdf_path)
                    for page in doc:
                        pdf_text += page.get_text()
                    doc.close()
                    print(f"      [SN1] Extracted {len(pdf_text)} characters of raw text for substation matching")
                except Exception as text_err:
                    print(f"      [SN1] Warning: Could not extract text for substation matching: {text_err}")
                
                # Extract tables from pages 11 onwards (where data tables are located)
                tables = camelot.read_pdf(pdf_path, pages='11-end', line_scale=40, suppress_stdout=True)
                print(f"      [SN1] Camelot extracted {len(tables)} raw table(s) from pages 11-end")
                
                if not tables or len(tables) == 0:
                    print(f"      [SN1] No tables found, returning empty result")
                    return pd.DataFrame()
                
                # Convert to DataFrames and fix column alignment
                table_dfs = []
                for t in tables:
                    fixed_df = fix_sn1_column_alignment(t.df)
                    table_dfs.append(fixed_df)
                
                # Merge related tables (continuation tables)
                merged_tables = merge_sn1_related_tables(table_dfs)
                
                # Extract records from all merged tables
                all_records = []
                for table_idx, table_df in enumerate(merged_tables):
                    # Detect header row and column mapping
                    header_row_idx, column_mapping = detect_sn1_header_row(table_df)
                    
                    if header_row_idx is None:
                        print(f"      [SN1] Table {table_idx + 1}: No header detected, skipping")
                        continue
                    
                    print(f"      [SN1] Table {table_idx + 1}: Header at row {header_row_idx}, columns mapped: {list(column_mapping.keys())}")
                    
                    # Extract records using the column mapping (with PDF text for substation extraction)
                    records = extract_sn1_records_from_table(
                        table_df, column_mapping, header_row_idx, canonical_fields, pdf_text
                    )
                    
                    print(f"      [SN1] Table {table_idx + 1}: Extracted {len(records)} record(s)")
                    all_records.extend(records)
                
                print(f"      [SN1] Total records extracted: {len(all_records)}")
                
                if all_records:
                    return ('camelot', all_records)
                else:
                    return pd.DataFrame()
                
            except Exception as e:
                print(f"      [SN1] Extraction error: {e}")
                import traceback
                traceback.print_exc()
                return pd.DataFrame()
        
        # Extract using 3-tier approach (returns text AND tables)
        # For SN9 Transformation Capacity and Margin PDFs, try lattice flavor first for clean column separation
        if sheet_name == "Transformation Capacity" or sheet_name == "Margin" or sheet_name == "Non RE proposed RE Integration":
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
                        
                        # Apply standardization to remove GIS, PS, S/s, coordinates etc.
                        if clean_pooling_ss:
                            clean_pooling_ss = clean_substation_name(clean_pooling_ss)
                        
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
                            
                            # Apply standardization to remove GIS, PS, S/s, coordinates etc.
                            if clean_pooling_ss:
                                clean_pooling_ss = clean_substation_name(clean_pooling_ss)
                            
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
            # Skip SN4 for "Data to be captured" sheet - SN4 extraction will be added later
            # Note: SN1 extraction is now integrated
            if source_id == "SN4" and TEST_SHEET_NAME == "Data to be captured":
                print(f"      [SKIP] Skipping {source_id} for '{TEST_SHEET_NAME}' sheet (extraction not yet integrated)")
                continue
            
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
        
        
        # LLM prompts removed - using Camelot table extraction only
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
                futures = [executor.submit(process_pdf_file, p, TEST_SHEET_NAME) for p in pdf_paths]
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
            
            # Post-processing: Clean all pooling_ss values
            print(f"\n  [*] Post-processing Margin sheet: Cleaning pooling_ss values...")
            cleaned_count = 0
            for record in sheet_records:
                original_pooling_ss = record.get('pooling_ss', '')
                if original_pooling_ss:
                    cleaned_pooling_ss = clean_substation_name(original_pooling_ss)
                    if cleaned_pooling_ss != original_pooling_ss:
                        cleaned_count += 1
                        if cleaned_count <= 5:  # Show first 5 examples
                            print(f"      [Clean] '{original_pooling_ss}' → '{cleaned_pooling_ss}'")
                    record['pooling_ss'] = cleaned_pooling_ss
            print(f"      [Summary] Cleaned {cleaned_count} pooling_ss names")
            
            # Post-processing: Calculate multiplication patterns in expected_cod_of_pooling_station
            print(f"\n  [*] Post-processing Margin sheet: Calculating capacity patterns in Expected CoD...")
            cod_calc_count = 0
            for record in sheet_records:
                original_cod = record.get('expected_cod_of_pooling_station', '')
                if original_cod:
                    calculated_cod = replace_multiplication_patterns(original_cod)
                    if calculated_cod != original_cod:
                        cod_calc_count += 1
                        if cod_calc_count <= 5:  # Show first 5 examples
                            print(f"      [Calc] '{original_cod}' → '{calculated_cod}'")
                    record['expected_cod_of_pooling_station'] = calculated_cod
            print(f"      [Summary] Calculated {cod_calc_count} multiplication patterns in Expected CoD")
        
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
            
            # FINAL CLEANUP: Apply clean_substation_name to ALL records after splitting
            # This ensures any values that may have bypassed earlier cleaning are caught
            print(f"\n      [*] Final pass: Cleaning all substation names...")
            final_cleaned_count = 0
            for record in sheet_records:
                original = record.get('substation', '')
                if original:
                    cleaned = clean_substation_name(original)
                    if cleaned != original:
                        final_cleaned_count += 1
                        if final_cleaned_count <= 5:
                            print(f"          [Clean] '{original}' → '{cleaned}'")
                    record['substation'] = cleaned
            print(f"      [Summary] Final cleanup: {final_cleaned_count} substation names cleaned")
            
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
    print(f"  - Extraction method: Camelot (direct table extraction)")
    print(f"\n>> Review the CSV files first to validate data, then check the Excel output.")
    print(f"\n[Next steps]")
    print(f"  1. Open CSVs in Excel to verify all data is captured")
    print(f"  2. Check Excel output matches template format for each sheet")
    print(f"  3. If data looks good, update main.py with the same logic")


if __name__ == '__main__':
    run_test_pipeline()
