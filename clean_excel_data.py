"""
Excel Data Cleaning Script for "Data to be captured" sheet
Tasks:
1. Fix Serial Number Column - sequential starting from 1
2. Fill Region and State Columns based on substation/known data
3. Clean "Name of Developers" Column - extract IDs to GNA/ST II Application ID
4. Fix GNA/ST II and LTA Application ID Columns
5. Shift CMETS Columns (M→L, O→N when L or N is empty)
"""

import openpyxl
import re
from copy import copy

# File path
FILE_PATH = r'c:\Users\Sree Charan\Desktop\fold2\CTU-PDF-EXTRACTOR\Connectivity_Application_Data_TEST_ALL_SHEETS38 (2).xlsx'
OUTPUT_PATH = r'c:\Users\Sree Charan\Desktop\fold2\CTU-PDF-EXTRACTOR\Connectivity_Application_Data_TEST_ALL_SHEETS38 (2).xlsx'

# Region/State mapping based on substations/states
STATE_REGION_MAP = {
    'Rajasthan': 'NR',
    'Gujarat': 'WR',
    'Maharashtra': 'WR',
    'Madhya Pradesh': 'WR',
    'Tamil Nadu': 'SR',
    'Karnataka': 'SR',
    'Andhra Pradesh': 'SR',
    'Telangana': 'SR',
    'Kerala': 'SR',
    'Punjab': 'NR',
    'Haryana': 'NR',
    'Uttar Pradesh': 'NR',
    'Uttarakhand': 'NR',
    'Himachal Pradesh': 'NR',
    'Jammu and Kashmir': 'NR',
    'Delhi': 'NR',
    'Chandigarh': 'NR',
    'Bihar': 'ER',
    'Jharkhand': 'ER',
    'Odisha': 'ER',
    'West Bengal': 'ER',
    'Sikkim': 'ER',
    'Assam': 'NER',
    'Meghalaya': 'NER',
    'Tripura': 'NER',
    'Manipur': 'NER',
    'Mizoram': 'NER',
    'Nagaland': 'NER',
    'Arunachal Pradesh': 'NER',
    'Chhattisgarh': 'WR',
    'Goa': 'WR',
}

# Substation to State mapping (commonly known substations)
SUBSTATION_STATE_MAP = {
    'bhadla': 'Rajasthan',
    'barmer': 'Rajasthan',
    'bikaner': 'Rajasthan',
    'fatehgarh': 'Rajasthan',
    'ramgarh': 'Rajasthan',
    'jodhpur': 'Rajasthan',
    'jaisalmer': 'Rajasthan',
    'ajmer': 'Rajasthan',
    'chamakri': 'Rajasthan',  # Assuming Rajasthan based on context
    'khavda': 'Gujarat',
    'mundra': 'Gujarat',
    'bhuj': 'Gujarat',
    'rajkot': 'Gujarat',
    'vadodara': 'Gujarat',
    'solapur': 'Maharashtra',
    'pune': 'Maharashtra',
    'nagpur': 'Maharashtra',
    'nashik': 'Maharashtra',
    'raipur': 'Chhattisgarh',
    'korba': 'Chhattisgarh',
    'bilaspur': 'Chhattisgarh',
    'bhopal': 'Madhya Pradesh',
    'indore': 'Madhya Pradesh',
    'jabalpur': 'Madhya Pradesh',
    'sholapur': 'Maharashtra',
    'bidri': 'Karnataka',
    'kolar': 'Karnataka',
    'bellary': 'Karnataka',
    'tumkur': 'Karnataka',
    'raichur': 'Karnataka',
    'tuticorin': 'Tamil Nadu',
    'kayathar': 'Tamil Nadu',
    'tirunelveli': 'Tamil Nadu',
    'kurnool': 'Andhra Pradesh',
    'anantapur': 'Andhra Pradesh',
    'kadapa': 'Andhra Pradesh',
}

def get_state_from_substation(substation):
    """Try to identify state from substation name"""
    if not substation:
        return None
    substation_lower = substation.lower()
    for key, state in SUBSTATION_STATE_MAP.items():
        if key in substation_lower:
            return state
    return None

def get_region_from_state(state):
    """Get region based on state"""
    if not state:
        return None
    return STATE_REGION_MAP.get(state)

def extract_id_and_name(text):
    """
    Extract numeric ID and developer name from mixed values
    Examples:
    - "2200000740  Ambuja Cements Limited" -> ("2200000740", "Ambuja Cements Limited")
    - "2200000564 \n \n(Enhancement)" -> ("2200000564", "(Enhancement)")
    """
    if not text:
        return None, None
    
    text = str(text).strip()
    
    # Pattern to match: numeric ID (10 digits typically) followed by optional text
    pattern = r'^(\d{10})\s*(.*)$'
    match = re.match(pattern, text, re.DOTALL)
    
    if match:
        app_id = match.group(1).strip()
        remaining = match.group(2).strip().replace('\n', ' ').replace('\r', ' ')
        remaining = ' '.join(remaining.split())  # Normalize whitespace
        return app_id, remaining if remaining else None
    
    return None, text

def clean_text(text):
    """Clean text by normalizing whitespace and newlines"""
    if not text:
        return text
    text = str(text).replace('\n', ' ').replace('\r', ' ')
    return ' '.join(text.split())

def process_excel():
    print("Loading workbook...")
    wb = openpyxl.load_workbook(FILE_PATH)
    ws = wb['Data to be captured']
    
    header_row = 2  # Headers are in row 2
    data_start_row = 3
    
    # Column indices (1-indexed)
    COL_SR_NO = 2        # B - Sr.no.
    COL_REGION = 3       # C - Region
    COL_STATE = 4        # D - State
    COL_SUBSTATION = 5   # E - Substation
    COL_DEVELOPER = 7    # G - Name of Developers
    COL_GNA_ID = 9       # I - GNA/ST II Application ID
    COL_LTA_ID = 10      # J - LTA Application ID
    COL_L = 12           # L - CMETS GNA Approved
    COL_M = 13           # M - CMETS LTA Approved
    COL_N = 14           # N - CMETS GNA Meeting Date
    COL_O = 15           # O - CMETS LTA Meeting Date
    
    # Find the last row with data
    max_row = ws.max_row
    last_data_row = max_row
    
    # Track changes
    changes = {
        'serial_fixed': 0,
        'region_filled': 0,
        'state_filled': 0,
        'developer_cleaned': 0,
        'id_moved': 0,
        'cmets_shifted': 0
    }
    
    print(f"Processing rows from {data_start_row} to {last_data_row}...")
    
    # First pass: Collect state mappings from existing data for forward-fill
    state_region_cache = {}  # substation -> (state, region)
    
    # Forward-pass to learn state/region associations
    for row in range(data_start_row, last_data_row + 1):
        substation = ws.cell(row=row, column=COL_SUBSTATION).value
        state = ws.cell(row=row, column=COL_STATE).value
        region = ws.cell(row=row, column=COL_REGION).value
        
        if substation and state and region:
            substation_clean = clean_text(substation).lower()
            if substation_clean not in state_region_cache:
                state_region_cache[substation_clean] = (state, region)
    
    print(f"Learned {len(state_region_cache)} substation-state-region mappings from existing data")
    
    # Main processing pass
    serial_number = 1
    prev_state = None
    prev_region = None
    
    for row in range(data_start_row, last_data_row + 1):
        # Skip completely empty rows (check if at least Sr.no or Developer or GNA_ID has data)
        sr_val = ws.cell(row=row, column=COL_SR_NO).value
        dev_val = ws.cell(row=row, column=COL_DEVELOPER).value
        gna_val = ws.cell(row=row, column=COL_GNA_ID).value
        lta_val = ws.cell(row=row, column=COL_LTA_ID).value
        
        # Check if this is a data row (has serial number or developer or ID)
        is_data_row = sr_val is not None or dev_val is not None or gna_val is not None or lta_val is not None
        
        if not is_data_row:
            continue
        
        # ========== TASK 1: Fix Serial Number ==========
        ws.cell(row=row, column=COL_SR_NO).value = serial_number
        if sr_val != serial_number:
            changes['serial_fixed'] += 1
        serial_number += 1
        
        # ========== TASK 3 & 4: Clean Developer and Fix IDs ==========
        developer = ws.cell(row=row, column=COL_DEVELOPER).value
        gna_id = ws.cell(row=row, column=COL_GNA_ID).value
        lta_id = ws.cell(row=row, column=COL_LTA_ID).value
        
        # Process Developer column for mixed ID+Name
        if developer:
            extracted_id, extracted_name = extract_id_and_name(developer)
            if extracted_id:
                # Move ID to GNA/ST II Application ID if empty
                if not gna_id:
                    ws.cell(row=row, column=COL_GNA_ID).value = extracted_id
                    changes['id_moved'] += 1
                # Keep only the name in Developer column
                if extracted_name:
                    ws.cell(row=row, column=COL_DEVELOPER).value = extracted_name
                    changes['developer_cleaned'] += 1
                else:
                    ws.cell(row=row, column=COL_DEVELOPER).value = None
                    changes['developer_cleaned'] += 1
        
        # Process LTA Application ID column for mixed values
        if lta_id:
            lta_str = str(lta_id).strip()
            extracted_id, extracted_name = extract_id_and_name(lta_str)
            
            if extracted_id:
                # This ID should be in GNA/ST II Application ID
                current_gna = ws.cell(row=row, column=COL_GNA_ID).value
                if not current_gna:
                    ws.cell(row=row, column=COL_GNA_ID).value = extracted_id
                    changes['id_moved'] += 1
                
                # If there's a name part (like "ACC Limited"), put it in Developer if empty
                if extracted_name and extracted_name not in ['(Enhancement)', 'Enhancement']:
                    current_dev = ws.cell(row=row, column=COL_DEVELOPER).value
                    if not current_dev or current_dev.strip() == '':
                        ws.cell(row=row, column=COL_DEVELOPER).value = extracted_name
                    elif extracted_name not in current_dev:
                        # Append if different
                        ws.cell(row=row, column=COL_DEVELOPER).value = f"{clean_text(current_dev)} / {extracted_name}"
                
                # Keep Enhancement notation in LTA column or clear it
                if extracted_name and 'Enhancement' in extracted_name:
                    ws.cell(row=row, column=COL_LTA_ID).value = extracted_name
                else:
                    ws.cell(row=row, column=COL_LTA_ID).value = None
        
        # ========== TASK 5: Shift CMETS Columns ==========
        col_l_val = ws.cell(row=row, column=COL_L).value
        col_m_val = ws.cell(row=row, column=COL_M).value
        col_n_val = ws.cell(row=row, column=COL_N).value
        col_o_val = ws.cell(row=row, column=COL_O).value
        
        # Shift M to L if L is empty and M has value
        if not col_l_val and col_m_val:
            ws.cell(row=row, column=COL_L).value = col_m_val
            ws.cell(row=row, column=COL_M).value = None
            changes['cmets_shifted'] += 1
        
        # Shift O to N if N is empty and O has value
        if not col_n_val and col_o_val:
            ws.cell(row=row, column=COL_N).value = col_o_val
            ws.cell(row=row, column=COL_O).value = None
            changes['cmets_shifted'] += 1
        
        # ========== TASK 2: Fill Region and State ==========
        substation = ws.cell(row=row, column=COL_SUBSTATION).value
        state = ws.cell(row=row, column=COL_STATE).value
        region = ws.cell(row=row, column=COL_REGION).value
        
        # Try to fill state from substation if empty
        if not state:
            # First try from learned cache
            if substation:
                substation_clean = clean_text(substation).lower()
                if substation_clean in state_region_cache:
                    state = state_region_cache[substation_clean][0]
                    ws.cell(row=row, column=COL_STATE).value = state
                    changes['state_filled'] += 1
                else:
                    # Try from substation mapping
                    inferred_state = get_state_from_substation(substation)
                    if inferred_state:
                        state = inferred_state
                        ws.cell(row=row, column=COL_STATE).value = state
                        changes['state_filled'] += 1
            
            # If still no state, use previous row's state
            if not state and prev_state:
                ws.cell(row=row, column=COL_STATE).value = prev_state
                state = prev_state
                changes['state_filled'] += 1
        
        # Fill region based on state if empty
        if not region:
            if state:
                inferred_region = get_region_from_state(state)
                if inferred_region:
                    ws.cell(row=row, column=COL_REGION).value = inferred_region
                    region = inferred_region
                    changes['region_filled'] += 1
            elif prev_region:
                ws.cell(row=row, column=COL_REGION).value = prev_region
                region = prev_region
                changes['region_filled'] += 1
        
        # Update previous values for forward-fill
        if state:
            prev_state = state
        if region:
            prev_region = region
    
    print("\n========== CHANGES SUMMARY ==========")
    print(f"Serial numbers fixed: {changes['serial_fixed']}")
    print(f"Regions filled: {changes['region_filled']}")
    print(f"States filled: {changes['state_filled']}")
    print(f"Developer names cleaned: {changes['developer_cleaned']}")
    print(f"IDs moved to correct columns: {changes['id_moved']}")
    print(f"CMETS columns shifted: {changes['cmets_shifted']}")
    print(f"Total serial numbers assigned: {serial_number - 1}")
    
    print(f"\nSaving workbook to {OUTPUT_PATH}...")
    wb.save(OUTPUT_PATH)
    print("Done!")
    
    return changes

if __name__ == "__main__":
    process_excel()
