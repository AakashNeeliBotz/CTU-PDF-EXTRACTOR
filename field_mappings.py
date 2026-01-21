"""
Field name mappings for PDF column headers to canonical field names.
Maps various PDF column header variations to standardized field names.
"""

# Canonical field names for each sheet
DATA_TO_BE_CAPTURED_FIELDS = [
    "sr_no", "region", "state", "substation", "coordinates",
    "name_of_developers", "group", 
    "gna_st_ii_application_id",  # Column 9
    "lta_application_id",  # Column 10 - NEW
    "application_id_enhancement_5_2_or_revision",  # Column 11
    "cmets_gna_approved",  # Column 12 - separated from LTA
    "cmets_lta_approved",  # Column 13 - NEW (was combined with GNA)
    "cmets_gna_meeting_date",  # Column 14 - separated from LTA
    "cmets_lta_meeting_date",  # Column 15 - NEW (was combined with GNA)
    "type",  # Column 16
    "application_quantum_mw",  # Column 17
    "granted_quantum_gna_lta_mw",  # Column 18 - NEW
    # Installed/Breakup Capacity (columns 19-21)
    "installed_breakup_solar_mw",  # Column 19
    "installed_breakup_wind_mw",  # Column 20
    "installed_breakup_hybrid_mw",  # Column 21
    # Battery (columns 22-24)
    "battery_mwh",  # Column 22
    "battery_injection_mw",  # Column 23
    "battery_drawl_mw",  # Column 24
    # PSP (columns 25-27)
    "psp_mwh",  # Column 25
    "psp_injection_mw",  # Column 26
    "psp_drawl_mw",  # Column 27
    # Commissioned (columns 28-29)
    "commissioned_tgna",  # Column 28
    "commissioned_gna",  # Column 29
    # Rest of the fields
    "application_date",  # Column 30
    "mode",  # Column 31
    "applied_start_of_connectivity",  # Column 32
    "gna_operationalization",  # Column 33
    "gna_operationalization_yes_no",  # Column 34
    "date_for_additional_capacity",  # Column 35
    "nature_of_applicant",  # Column 36
    "status_of_application",  # Column 37 - NEW
    "voltage_level_kv",  # Column 38
    "bay_no",  # Column 39
    "cts_element_unique_code",  # Column 40
    "ats_element_unique_code",  # Column 41
    "dtl_element_unique_code"  # Column 42
]

# Margin sheet fields (flattened from nested structures)
MARGIN_FIELDS = [
    "sl_no", "state", "region", "pooling_ss", "additional_information_of_pooling_ss", "timelines",
    "re_potential_mw", "bess_mw", "ss_evacuation_capacity_mw",
    "expected_cod_of_pooling_station",
    "connectivity_granted_1_200kv_mw", "connectivity_granted_1_400kv_mw", "connectivity_granted_1_total_mw",
    "connectivity_granted_2_200kv_mw", "connectivity_granted_2_400kv_mw", "connectivity_granted_2_total_mw",
    "margin_for_connectivity_200kv_mw", "margin_for_connectivity_400kv_mw", "margin_for_connectivity_total_mw",
    "additional_margin_200kv_mw", "additional_margin_400kv_mw", "additional_margin_total_mw",
    "effectiveness_of_gna", "remarks"
]

# Transformation Capacity sheet fields
# Note: For SN9 PDFs, columns 4-6 are under "Transformation Capacity (MVA)" header:
#   - Column 4: Existing
#   - Column 5: Under Implementation  
#   - Column 6: Planned
# Updated to include voltage_level_kv and renamed capacity columns
TRANSFORMATION_CAPACITY_FIELDS = [
    "s_no", "region", "state", "substation", "voltage_level_kv",
    "existing_mva", "under_implementation_mva", "planned_mva"
]

# Non RE proposed RE Integration sheet fields
# From SN9 Non RE subfolder: "Connectivity margins at existing ISTS (non RE) substations for future RE integration"
NON_RE_FIELDS = [
    "state", "name_of_station", "capacity_mva", "capacity_allocated_mw",
    "margin_existing_220kv", "margin_existing_400kv",
    "line_bays_220kv", "line_bays_400kv",
    "margin_with_ict_220kv", "margin_with_ict_400kv",
    "line_bays_with_ict_220kv", "line_bays_with_ict_400kv",
    "no_of_transformers_required", "remarks"
]

# Element Status sheet fields (from SN1 PDFs)
# Maps to columns in Element Status sheet
ELEMENT_STATUS_FIELDS = [
    "element_code",  # Column 2 - Unique code (CTS-001, DTL-001, ATS-001)
    "inter_intra_tx_element",  # Column 3 - Element description
    "transmission_scheme",  # Column 4
    "transmission_scope",  # Column 5 - ATS/DTL/CTS
    "mva",  # Column 6
    "status",  # Column 7
    "approval_nct",  # Column 8
    "mode_tbcb_rtm",  # Column 9
    "tender_issuing_authority",  # Column 10
    "date_tender_issuance",  # Column 11
    "date_bid_submission",  # Column 12
    "execution_timeline",  # Column 13
    "tentative_scod",  # Column 14
    "awarded_to",  # Column 15 - Developer name
    "spv_transfer_date",  # Column 16
    "physical_progress_length",  # Column 17
    "physical_progress_location",  # Column 18
    "physical_progress_foundation"  # Column 19
]

# Mapping from PDF column headers (variations) to canonical field names
# Keys are lowercase, stripped versions of PDF headers
HEADER_MAPPINGS = {
    # Serial Number variations
    "serial no": "sr_no",
    "sr no": "sr_no",
    "s.no": "sr_no",
    "sno": "sr_no",
    "id": "sr_no",
    "sl no": "sr_no",
    "s no": "sr_no",
    
    # Region
    "region": "region",
    "regional": "region",
    "circle": "region",
    
    # State
    "state": "state",
    "location state": "state",
    
    # Substation variations
    "substation": "substation",
    "s/s": "substation",
    "ss": "substation",
    "sub-station": "substation",
    "sub station": "substation",
    "pooling station": "substation",
    "pooling ss": "substation",
    
    # Coordinates
    "coordinates": "coordinates",
    "geo coordinates": "coordinates",
    "lat/long": "coordinates",
    "latitude/longitude": "coordinates",
    
    # Developer variations
    "name of developers": "name_of_developers",
    "name of developer": "name_of_developers",
    "developer": "name_of_developers",
    "developers": "name_of_developers",
    "company": "name_of_developers",
    "applicant": "name_of_developers",
    "name of applicant": "name_of_developers",
    "developer name": "name_of_developers",
    
    # Group
    "group": "group",
    "developer group": "group",
    "parent company": "group",
    
    # Application ID variations - now maps to GNA/ST-II Application ID
    "application id": "gna_st_ii_application_id",
    "app id": "gna_st_ii_application_id",
    "reference no": "gna_st_ii_application_id",
    "application no": "gna_st_ii_application_id",
    "ref no": "gna_st_ii_application_id",
    "gna application id": "gna_st_ii_application_id",
    "st-ii application id": "gna_st_ii_application_id",
    "st ii application id": "gna_st_ii_application_id",
    "gna/st ii application id": "gna_st_ii_application_id",
    
    # LTA Application ID (specific)
    "lta application id": "lta_application_id",
    "lta id": "lta_application_id",
    
    # SN1-specific mappings
    "applicant": "name_of_developers",
    "project location": "state",
    "submission date": "application_date",
    "criterion for applying": "mode",
    "start date of connectivity (as per application)": "applied_start_of_connectivity",
    "start date of connectivity as per application": "applied_start_of_connectivity",
    "connectivity location (as per application)": "substation",
    "connectivity location as per application": "substation",
    "nature of applicant": "nature_of_applicant",
    "connectivity quantum (mw)": "application_quantum_mw",
    "connectivity quantum": "application_quantum_mw",
    
    # Application ID Enhancement
    "application id (enhancement)": "application_id_enhancement_5_2_or_revision",
    "revision": "application_id_enhancement_5_2_or_revision",
    "modified id": "application_id_enhancement_5_2_or_revision",
    
    # CMETS/LTA/GNA Approved
    "cmets/lta/gna approved": "cmets_lta_gna_approved",
    "approval": "cmets_lta_gna_approved",
    "approved capacity": "cmets_lta_gna_approved",
    
    # CMETS/LTA/GNA Meeting Date
    "cmets/lta/gna meeting date": "cmets_lta_gna_meeting_date",
    "meeting date": "cmets_lta_gna_meeting_date",
    "approval date": "cmets_lta_gna_meeting_date",
    
    # Type/Technology
    "type": "type",
    "technology": "type",
    "category": "type",
    "project type": "type",
    "type of project": "type",  # Added
    "type of nproject": "type",  # Handle newline case
    
    # Application Quantum (MW)
    "application quantum (mw)": "application_quantum_mw",
    "application quantum": "application_quantum_mw",
    "capacity": "application_quantum_mw",
    "applied capacity": "application_quantum_mw",
    "quantum mw": "application_quantum_mw",
    "capacity mw": "application_quantum_mw",
    "capacity (mw)": "application_quantum_mw",
    "installed capacity (mw)": "application_quantum_mw",  # Added
    "installed ncapacity n(mw)": "application_quantum_mw",  # Handle newline case
    "present connectivity /deemed gna": "application_quantum_mw",  # Added - seems to be capacity
    "present nconnectivity n/deemed gna": "application_quantum_mw",  # Handle newline
    
    # Substation variations (extended)
    "substation": "substation",
    "s/s": "substation",
    "ss": "substation",
    "sub-station": "substation",
    "sub station": "substation",
    "pooling station": "substation",
    "pooling ss": "substation",
    "substation at which generation connected/ connectivity granted": "substation",  # Added
    "substation at nwhich ngeneration nconnected/ nconnectivity ngranted": "substation",  # Newline case
    
    # State variations
    "state": "state",
    "location state": "state",
    "state (connectivity station)": "state",  # Added
    "state n(connectivity nstation)": "state",  # Newline case
    
    # Expected date
    "expected date": "expected_date_of_connectivity",
    "expected date of connectivity/ gna to be made effective": "expected_date_of_connectivity",  # Added
    "expected date of nconnectivity/ gna to nbe made effective": "expected_date_of_connectivity",  # Newline,
    
    # Status of LTA
    "status of lta": "status_of_lta",
    "lta status": "status_of_lta",
    "status": "status_of_lta",
    
    # Application Date
    "application date": "application_date",
    "date of application": "application_date",
    "submission date": "application_date",
    
    # Mode
    "mode": "mode",
    "connectivity mode": "mode",
    
    # Voltage Level
    "voltage level (kv)": "voltage_level_kv",
    "voltage level": "voltage_level_kv",
    "voltage": "voltage_level_kv",
    "kv": "voltage_level_kv",
    
    # Bay Number
    "bay no": "bay_no",
    "bay number": "bay_no",
    "bay": "bay_no",
    
    # Remarks
    "remarks": "remarks",
    "comments": "remarks",
    "notes": "remarks",
    
    # === SN9-specific mappings (Bay Allocation / Margin / Transformation Capacity) ===
    
    # Substation variations (SN9)
    "name of substation": "substation",
    "substation coordinates": "coordinates",
    "pooling ss": "pooling_ss",
    "pooling s/s": "pooling_ss",
    "sl no": "sl_no",
    "s no": "s_no",
    
    # Transformation Capacity (MVA) - direct mappings
    "transformation capacity (mva)": "transformation_capacity",
    "transformation capacity": "transformation_capacity",
    "existing": "existing_mva",
    "under implementation": "under_implementation_mva",
    "planned": "planned_mva",
    
    # Margin and Connectivity fields
    "re capacity granted": "re_capacity_granted",
    "re capacity granted (stage-ii connectivity)": "re_capacity_granted",
    "re capacity granted\n (stage-ii connectivity)": "re_capacity_granted",
    "stage-ii quantum (mw)": "stage_ii_quantum_mw",
    "stage ii quantum (mw)": "stage_ii_quantum_mw",
    "stage-ii \nquantum \n(mw)": "stage_ii_quantum_mw",
    "quantum (mw)": "quantum_mw",
    "name of entity": "name_of_entity",
    "bay no": "bay_no",
    "bay-wise margins available (mw)": "bay_margins_mw",
    "bay-wise margins \navailable (mw)": "bay_margins_mw",
    "margins available (mw)": "bay_margins_mw",
    "space provision for future additional line bays (no.) for injection": "future_line_bays",
    "space provision for future \nadditional line bays (no.) for \ninjection": "future_line_bays",
    "timelines": "timelines",
    
    # COD and Potential
    "expected cod of pooling station": "expected_cod_of_pooling_station",
    "re potential (mw)": "re_potential_mw",
    "re potential": "re_potential_mw",
    "bess (mw)": "bess_mw",
    "bess": "bess_mw",
    "s/s evacuation capacity": "ss_evacuation_capacity_mw",
    "evacuation capacity": "ss_evacuation_capacity_mw",
    
    # Connectivity granted variations
    "connectivity granted/ agreed": "connectivity_granted",
    "connectivity granted": "connectivity_granted",
    "total (mw)": "total_mw",
    
    # Margin variations
    "margin for connectivity": "margin_for_connectivity",
    "additional margin for connectivity requiring ict augmentation / additional tr. system": "additional_margin",
    "additional margin": "additional_margin",
    "effectiveness of gna for capacity mentioned under margin for connectivity": "effectiveness_of_gna",
    "effectiveness of gna": "effectiveness_of_gna",
}

# State to Region mapping
STATE_TO_REGION = {
    # Northern Region (NR) - Rajasthan moved here per user requirement
    "rajasthan": "NR",
    "punjab": "NR",
    "haryana": "NR",
    "himachal pradesh": "NR",
    "jammu and kashmir": "NR",
    "j&k": "NR",
    "delhi": "NR",
    "uttarakhand": "NR",
    "uttar pradesh": "NR",
    "up": "NR",
    "chandigarh": "NR",
    "ladakh": "NR",
    
    # Western Region (WR)
    "gujarat": "WR",
    "maharashtra": "WR",
    "madhya pradesh": "WR",
    "mp": "WR",
    "goa": "WR",
    "daman and diu": "WR",
    "dadra and nagar haveli": "WR",
    "chhattisgarh": "WR",
    
    # Southern Region (SR)
    "karnataka": "SR",
    "tamil nadu": "SR",
    "kerala": "SR",
    "andhra pradesh": "SR",
    "telangana": "SR",
    "puducherry": "SR",
    "pondicherry": "SR",
    "andaman and nicobar": "SR",
    "lakshadweep": "SR",
    
    # Eastern Region (ER)
    "west bengal": "ER",
    "bihar": "ER",
    "odisha": "ER",
    "jharkhand": "ER",
    "sikkim": "ER",
    
    # North Eastern Region (NER)
    "assam": "NER",
    "manipur": "NER",
    "meghalaya": "NER",
    "mizoram": "NER",
    "nagaland": "NER",
    "tripura": "NER",
    "arunachal pradesh": "NER",
}


def normalize_header(header: str) -> str:
    """
    Normalize a PDF column header to canonical field name.
    
    Args:
        header: Raw column header from PDF
        
    Returns:
        Canonical field name or original header if no mapping found
    """
    if not header:
        return ""
    
    # Clean and normalize
    normalized = str(header).lower().strip()
    normalized = normalized.replace("_", " ")
    normalized = normalized.replace("-", " ")
    normalized = normalized.replace(".", "")  # Remove periods (e.g., "Sl. No" -> "sl no")
    normalized = normalized.replace("\n", " ")  # Replace newlines with spaces
    
    # Remove extra whitespace
    normalized = " ".join(normalized.split())
    
    # First try exact match in mapping
    if normalized in HEADER_MAPPINGS:
        return HEADER_MAPPINGS[normalized]
    
    # SN1 special case: Headers that end with known keywords (multi-row headers)
    # Check if the header ENDS with a known pattern
    if normalized.endswith('submission date'):
        return 'application_date'
    if normalized.endswith('criterion for applying'):
        return 'mode'
    if normalized.endswith('nature of applicant'):
        return 'nature_of_applicant'
    if normalized.endswith('connectivity quantum (mw)') or normalized.endswith('connectivity quantum'):
        return 'application_quantum_mw'
    if normalized.endswith('start date of connectivity (as per application)'):
        return 'applied_start_of_connectivity'
    if normalized.endswith('connectivity location (as per application)'):
        return 'substation'
    if normalized.endswith('application id'):
        return 'gna_st_ii_application_id'
    if normalized.endswith('applicant') and 'nature' not in normalized:
        return 'name_of_developers'
    if normalized.endswith('project location'):
        return 'state'
    
    # If no match found, return original header
    return header


def infer_region_from_state(state: str) -> str:
    """
    Infer region code from state name.
    
    Args:
        state: State name
        
    Returns:
        Region code (NR/SR/WR/ER/NER) or empty string if not found
    """
    if not state:
        return ""
    
    state_normalized = str(state).lower().strip()
    return STATE_TO_REGION.get(state_normalized, "")


def build_schema_alignment_prompt(sheet_name: str, expected_fields: list, input_row_count: int) -> str:
    """
    Build a strict schema-alignment prompt for LLM to format table data.
    
    Args:
        sheet_name: Name of the target sheet
        expected_fields: List of canonical field names in exact order
        input_row_count: Number of data rows in input (excluding header)
        
    Returns:
        Schema-alignment prompt string
    """
    header_csv = ",".join(expected_fields)
    
    prompt = f"""Format the following table data to match this EXACT schema.

RETURN REQUIREMENTS:
1. Return ONLY CSV format
2. First row MUST be this exact header: {header_csv}
3. Output MUST have exactly {input_row_count} data rows (excluding header)
4. Use these exact column names in order: {header_csv}

FORMATTING RULES:
- Dates: YYYY-MM-DD format only
- Numbers: numeric value only, remove units ("500 MW" → 500)
- Empty values: leave blank (no "null" or "N/A" text)
- Fields with commas: wrap in quotes
- Region: must be NR/SR/WR/ER/NER only
- Remove extra spaces and newlines within cells

CRITICAL:
- Do NOT skip any rows
- Do NOT add extra rows
- Do NOT change the order of columns
- Do NOT include explanations or markdown
- Return ONLY the CSV data

Input table data:
"""
    return prompt


def split_lta_from_application_id(records: list) -> list:
    """
    Post-process records to intelligently split LTA IDs from application ID fields.
    
    Logic:
    1. If value contains "LTA" anywhere, extract the LTA ID portion
    2. If value has BOTH GNA/ST-II ID and LTA ID, split them:
       - LTA part → lta_application_id
       - Remaining part → gna_st_ii_application_id
    3. If only LTA is present, put in lta_application_id only
    
    Examples:
    - "LTA:1200003120" → lta_application_id: "1200003120"
    - "2200000286 (LTA:1200003120)" → gna_st_ii_application_id: "2200000286", lta_application_id: "1200003120"
    - "LTA: 1200003120 (88.35MW)" → lta_application_id: "1200003120"
    
    Args:
        records: List of record dictionaries
        
    Returns:
        Updated list of records with LTA IDs properly separated
    """
    import re
    
    for record in records:
        # Check if gna_st_ii_application_id field exists and has value
        gna_id = record.get('gna_st_ii_application_id', '')
        
        if gna_id and isinstance(gna_id, str):
            # Search for LTA ID pattern anywhere in the string
            # Pattern matches: LTA:1234567890 or LTA: 1234567890 or LTA 1234567890
            lta_match = re.search(r'LTA[:\s]*([\d]+)', str(gna_id), re.IGNORECASE)
            
            if lta_match:
                # Extract the LTA ID (numeric part only)
                lta_id = lta_match.group(1).strip()
                
                # Extract the non-LTA part (GNA/ST-II ID if present)
                # Remove the entire LTA portion and any surrounding brackets/parentheses
                remaining = re.sub(r'[\(\[]?\s*LTA[:\s]*[\d]+[^\)\]]*[\)\]]?', '', gna_id, flags=re.IGNORECASE)
                # Clean up extra whitespace and special characters
                remaining = re.sub(r'\s+', ' ', remaining).strip()
                remaining = remaining.strip('(),[] ')
                
                # Check if remaining part looks like a valid application ID (contains digits)
                # If it's just text (like company name) or capacity info, treat as LTA-only
                has_digits = bool(re.search(r'\d', remaining))
                
                # Set the LTA ID
                record['lta_application_id'] = lta_id
                
                # Set the remaining part as GNA/ST-II ID only if it looks like an ID (has digits)
                if remaining and has_digits and remaining.lower() not in ['lta', 'n/a', 'na', '-']:
                    record['gna_st_ii_application_id'] = remaining
                    print(f"      [LTA Split] '{gna_id}' → GNA: '{remaining}' + LTA: '{lta_id}'")
                else:
                    record['gna_st_ii_application_id'] = None
                    print(f"      [LTA Split] '{gna_id}' → LTA only: '{lta_id}'")
    
    return records


def extract_additional_info_from_pooling_ss(pooling_ss_value: str) -> tuple:
    """
    Extract additional information from pooling S/s station name.
    
    Rules:
    1. Extract content in parentheses (e.g., '(Section-I)' → 'Section-I')
    2. Extract descriptive text after station name (e.g., 'Section linked to...')
    3. Remove parentheses from extracted text
    4. Keep station names with Roman numerals (I, II, III, IV), 'Complex', or '/' as-is
    
    Examples:
    - 'Fatehgarh-III (Section-I)' → ('Fatehgarh-III', 'Section-I')
    - 'Pavagada (expansion with ICTs)' → ('Pavagada', 'expansion with ICTs')
    - 'Khvada III PS (Sec-I & II)' → ('Khvada III PS', 'Sec-I & II')
    - 'Bhadla-III Section linked to Bhadla HVDC station & system' → ('Bhadla-III', 'Section linked to Bhadla HVDC station & system')
    - 'Fatehgarh-Barmer Complex' → ('Fatehgarh-Barmer Complex', None)
    - 'Bhadla-II' → ('Bhadla-II', None)
    - 'Jam Khambhaliya-II / Kalyanpur' → ('Jam Khambhaliya-II / Kalyanpur', None)
    
    Args:
        pooling_ss_value: The original pooling S/s value
        
    Returns:
        Tuple of (cleaned_station_name, additional_info)
    """
    import re
    
    if not pooling_ss_value or not isinstance(pooling_ss_value, str):
        return (pooling_ss_value, None)
    
    original = pooling_ss_value.strip()
    station_name = original
    additional_info = None
    
    # Pattern 1: Extract content in COMPLETE parentheses at the end
    # Match: (Section-I), (Sec-I & II), (expansion with ICTs), etc.
    parentheses_pattern = r'\s*\(([^)]+)\)\s*$'
    match = re.search(parentheses_pattern, station_name)
    
    # Pattern 1b: Also handle INCOMPLETE parentheses (missing closing paren)
    # Common in PDF extraction where text is split across cells
    # Match: (Section-II, (Sec-I, etc.
    if not match:
        incomplete_paren_pattern = r'\s*\(([^)]+)\s*$'
        match = re.search(incomplete_paren_pattern, station_name)
    
    if match:
        # Extract the content inside parentheses
        content = match.group(1).strip()
        
        # Check if it's NOT just a location reference (keep those in station name)
        # We want to extract: Section-I, Sec-I, expansion, etc.
        # We DON'T want to extract if it's part of the core name
        if content:
            additional_info = content
            # Remove the parenthetical part from station name
            station_name = station_name[:match.start()].strip()
    
    # Pattern 2: Extract descriptive text after station name
    # Look for keywords that indicate additional information
    # Examples: "Section linked to", "expansion", "with", etc.
    if not additional_info:
        # Keywords that indicate start of additional info
        info_keywords = [
            r'\s+Section\s+linked\s+to',
            r'\s+section\s+linked\s+to',
            r'\s+linked\s+to',
            r'\s+expansion\s+',
            r'\s+with\s+expansion',
            r'\s+including\s+',
        ]
        
        for keyword in info_keywords:
            match = re.search(keyword, station_name, re.IGNORECASE)
            if match:
                # Split at the keyword
                split_pos = match.start()
                additional_info = station_name[split_pos:].strip()
                station_name = station_name[:split_pos].strip()
                break
    
    # Clean up: Remove trailing/leading special characters from station name
    station_name = station_name.strip('- \t\n')
    
    # If additional_info is empty or None, keep it as None
    if additional_info and not additional_info.strip():
        additional_info = None
    
    return (station_name, additional_info)


def clean_substation_name(substation_value: str) -> str:
    """
    Clean substation name by removing voltage levels, technical suffixes, and special characters.
    
    Removes:
    1. Voltage levels at the beginning OR end (e.g., '400/220kV', '765/400/220kV', '765/400')
    2. Technical suffixes: GIS, AIS, PS, P.S., S/s, S/S (with or without parentheses/brackets)
    3. Patterns in parentheses: (GIS), (AIS), (existing S/s), (Proposed), etc.
    4. Patterns in square brackets: [GIS], [AIS], etc.
    5. GPS coordinates (e.g., 10°46'22"N 76°45'36"E)
    6. Special characters at the end (e.g., '#', '*')
    
    Examples:
    - '400/220kV Jam Khambhaliya (GIS) PS #' → 'Jam Khambhaliya'
    - '765/400/220kV Bhuj-II PS#' → 'Bhuj-II'
    - 'Tuticorin-II GIS' → 'Tuticorin-II'
    - 'Banaskantha PS [GIS]' → 'Banaskantha'
    - 'Khandwa S/s (existing S/s)' → 'Khandwa'
    - 'Palakkad S/s 10°46'22"N 76°45'36"E' → 'Palakkad'
    - 'Navinal 765/400kV' → 'Navinal'
    
    Args:
        substation_value: The original substation name
        
    Returns:
        Cleaned substation name
    """
    import re
    
    if not substation_value or not isinstance(substation_value, str):
        return substation_value
    
    cleaned = substation_value.strip()
    
    # Remove GPS coordinates (e.g., 10°46'22"N 76°45'36"E or variations)
    # Pattern: digits + degree symbol + digits + quote/apostrophe + digits + double-quote + N/S + space + similar for E/W
    coord_pattern = r'\d+°\d+[\'′]\d+[\"″]?[NS]?\s*\d*°?\d*[\'′]?\d*[\"″]?[EW]?'
    cleaned = re.sub(coord_pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Remove voltage levels at the BEGINNING
    # Pattern: one or more voltage numbers separated by / followed by kV or KV
    # Examples: 400/220kV, 765/400/220kV, 220kV, 400kV
    voltage_pattern_start = r'^\d+(?:/\d+)*\s*k[Vv]\s*'
    cleaned = re.sub(voltage_pattern_start, '', cleaned)
    
    # Remove voltage levels at the END (with or without kV suffix)
    # Patterns: 
    #   - "765/400kV" at end
    #   - "765/400/220kV" at end
    #   - "765/400" at end (without kV)
    # Match: space + digits + optional(/digits) + optional(kV) at end
    voltage_pattern_end = r'\s+\d+(?:/\d+)*(?:\s*k[Vv])?\s*$'
    cleaned = re.sub(voltage_pattern_end, '', cleaned)
    
    # Remove patterns in square brackets: [GIS], [AIS], etc.
    bracket_pattern = r'\s*\[[^\]]+\]'
    cleaned = re.sub(bracket_pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Remove patterns in parentheses: (GIS), (AIS), (existing S/s), (Proposed), (expansion), etc.
    paren_pattern = r'\s*\([^)]*\)'
    cleaned = re.sub(paren_pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Remove standalone technical suffixes at the end (without parentheses)
    # GIS, AIS at end (with optional dash and version like GIS-II)
    cleaned = re.sub(r'\s+(?:GIS|AIS)(?:\s*-?\s*[IVX]+)?\s*$', '', cleaned, flags=re.IGNORECASE)
    
    # Remove PS, P.S., S/s, S/S from the name
    # Pattern 1: PS followed by version (PS-II, PS-III) - keep the version, remove PS
    cleaned = re.sub(r'\s+(?:PS|P\.S\.)\s*(-\s*[IVX\d]+)', r'\1', cleaned, flags=re.IGNORECASE)
    # Pattern 2: PS at the end alone
    cleaned = re.sub(r'\s*(?:PS|P\.S\.|S/[sS]|S/S)\s*$', '', cleaned, flags=re.IGNORECASE)
    # Pattern 3: PS followed by space and more text (PS Complex, etc)
    cleaned = re.sub(r'\s+(?:PS|P\.S\.)\s+', ' ', cleaned, flags=re.IGNORECASE)
    
    # Remove special characters at the end (#, *, etc.)
    cleaned = cleaned.rstrip('#*~+ ')
    
    # Clean up extra whitespace
    cleaned = ' '.join(cleaned.split())
    
    return cleaned.strip()


def lookup_state_from_margin(substation_name: str, margin_data: list) -> str:
    """
    Look up state from Margin sheet data by matching substation name with pooling_ss.
    
    Uses fuzzy matching to handle variations:
    - Exact match first
    - Partial match (contains or is contained)
    - Core name matching (strips suffixes like S/s, PS, roman numerals, etc.)
    - Case-insensitive matching
    
    Args:
        substation_name: Cleaned substation name from Transformation Capacity
        margin_data: List of Margin sheet records (dicts with 'pooling_ss' and 'state' keys)
        
    Returns:
        State name if found, None otherwise
    """
    import re
    
    if not substation_name or not margin_data:
        return None
    
    def extract_core_name(name):
        """Extract core station name by removing common suffixes and patterns"""
        if not name:
            return ""
        
        core = name.lower().strip()
        
        # Remove voltage levels first (if any remain)
        core = re.sub(r'^\d+(?:/\d+)*\s*k[Vv]\s*', '', core)
        
        # Remove technical suffixes in square brackets or parentheses
        core = re.sub(r'\s*\[[^\]]+\]', '', core)  # [GIS], [AIS], etc.
        core = re.sub(r'\s*\([^)]*(?:existing|gis|ais|hvdc)[^)]*\)', '', core, flags=re.IGNORECASE)
        
        # Remove common suffixes
        for suffix in [' s/s', ' ps', ' complex', ' station', ' substation', ' ss']:
            if core.endswith(suffix):
                core = core[:-len(suffix)].strip()
        
        # Remove roman numerals and version numbers at the end
        # Pattern: -II, -III, -IV, -V, -VI, etc. or just II, III, IV
        core = re.sub(r'[-\s]+(i{1,3}|iv|vi{0,3}|ix|x)\s*$', '', core, flags=re.IGNORECASE)
        
        # Remove single letter suffixes like -A, -B, -C
        core = re.sub(r'[-\s]+[a-z]\s*$', '', core, flags=re.IGNORECASE)
        
        # Remove trailing special characters and numbers
        core = re.sub(r'[-\s#*~+]+$', '', core)
        
        # Clean up extra whitespace
        core = ' '.join(core.split())
        
        return core.strip()
    
    # Normalize the search term
    search_term = substation_name.strip().lower()
    search_core = extract_core_name(search_term)
    
    # First pass: Try exact match
    for record in margin_data:
        pooling_ss = record.get('pooling_ss', '')
        if pooling_ss and isinstance(pooling_ss, str):
            if pooling_ss.strip().lower() == search_term:
                state = record.get('state')
                if state:
                    return state
    
    # Second pass: Try core name exact match
    # This handles cases like "Kurnool S/s" matching "Kurnool-V"
    best_match_state = None
    best_match_score = 0
    
    for record in margin_data:
        pooling_ss = record.get('pooling_ss', '')
        if pooling_ss and isinstance(pooling_ss, str):
            pooling_core = extract_core_name(pooling_ss)
            
            # Exact core name match (highest priority)
            if search_core and pooling_core and search_core == pooling_core:
                state = record.get('state')
                if state:
                    return state  # Return immediately for exact core match
    
    # Third pass: Try partial match on core names
    # Match if one core is contained in the other
    for record in margin_data:
        pooling_ss = record.get('pooling_ss', '')
        if pooling_ss and isinstance(pooling_ss, str):
            pooling_ss_lower = pooling_ss.strip().lower()
            pooling_core = extract_core_name(pooling_ss)
            
            # Check if cores are similar (one contains the other)
            if search_core and pooling_core:
                if search_core in pooling_core or pooling_core in search_core:
                    state = record.get('state')
                    if state:
                        # Calculate match score (prefer longer matches)
                        match_score = min(len(search_core), len(pooling_core))
                        if match_score > best_match_score:
                            best_match_state = state
                            best_match_score = match_score
    
    if best_match_state:
        return best_match_state
    
    # Fourth pass: Try matching on original terms (fallback)
    # Check if search_term is in pooling_ss or vice versa
    for record in margin_data:
        pooling_ss = record.get('pooling_ss', '')
        if pooling_ss and isinstance(pooling_ss, str):
            pooling_ss_lower = pooling_ss.strip().lower()
            
            if search_term in pooling_ss_lower or pooling_ss_lower in search_term:
                state = record.get('state')
                if state:
                    match_score = min(len(search_term), len(pooling_ss_lower))
                    if match_score > best_match_score:
                        best_match_state = state
                        best_match_score = match_score
    
    # No match found
    return best_match_state


def lookup_state_from_data_to_be_captured(substation_name: str, dtbc_data: list) -> str:
    """
    Look up state from 'Data to be captured' sheet data by matching substation name.
    
    Uses the same fuzzy matching logic as lookup_state_from_margin:
    - Exact match first
    - Partial match (contains or is contained)
    - Core name matching (strips suffixes like S/s, PS, roman numerals, etc.)
    - Case-insensitive matching
    
    Args:
        substation_name: Cleaned substation name from Transformation Capacity
        dtbc_data: List of Data to be captured sheet records (dicts with 'substation' and 'state' keys)
        
    Returns:
        State name if found, None otherwise
    """
    import re
    
    if not substation_name or not dtbc_data:
        return None
    
    def extract_core_name(name):
        """Extract core station name by removing common suffixes and patterns"""
        if not name:
            return ""
        
        core = name.lower().strip()
        
        # Remove voltage levels first (if any remain)
        core = re.sub(r'^\d+(?:/\d+)*\s*k[Vv]\s*', '', core)
        
        # Remove technical suffixes in square brackets or parentheses
        core = re.sub(r'\s*\[[^\]]+\]', '', core)  # [GIS], [AIS], etc.
        core = re.sub(r'\s*\([^)]*(?:existing|gis|ais|hvdc)[^)]*\)', '', core, flags=re.IGNORECASE)
        
        # Remove common suffixes
        for suffix in [' s/s', ' ps', ' complex', ' station', ' substation', ' ss']:
            if core.endswith(suffix):
                core = core[:-len(suffix)].strip()
        
        # Remove roman numerals and version numbers at the end
        core = re.sub(r'[-\s]+(i{1,3}|iv|vi{0,3}|ix|x)\s*$', '', core, flags=re.IGNORECASE)
        
        # Remove single letter suffixes like -A, -B, -C
        core = re.sub(r'[-\s]+[a-z]\s*$', '', core, flags=re.IGNORECASE)
        
        # Remove trailing special characters and numbers
        core = re.sub(r'[-\s#*~+]+$', '', core)
        
        # Clean up extra whitespace
        core = ' '.join(core.split())
        
        return core.strip()
    
    # Normalize the search term
    search_term = substation_name.strip().lower()
    search_core = extract_core_name(search_term)
    
    # First pass: Try exact match
    for record in dtbc_data:
        dtbc_substation = record.get('substation', '')
        if dtbc_substation and isinstance(dtbc_substation, str):
            if dtbc_substation.strip().lower() == search_term:
                state = record.get('state')
                if state:
                    return state
    
    # Second pass: Try core name exact match
    best_match_state = None
    best_match_score = 0
    
    for record in dtbc_data:
        dtbc_substation = record.get('substation', '')
        if dtbc_substation and isinstance(dtbc_substation, str):
            dtbc_core = extract_core_name(dtbc_substation)
            
            # Exact core name match (highest priority)
            if search_core and dtbc_core and search_core == dtbc_core:
                state = record.get('state')
                if state:
                    return state  # Return immediately for exact core match
    
    # Third pass: Try partial match on core names
    for record in dtbc_data:
        dtbc_substation = record.get('substation', '')
        if dtbc_substation and isinstance(dtbc_substation, str):
            dtbc_substation_lower = dtbc_substation.strip().lower()
            dtbc_core = extract_core_name(dtbc_substation)
            
            # Check if cores are similar (one contains the other)
            if search_core and dtbc_core:
                if search_core in dtbc_core or dtbc_core in search_core:
                    state = record.get('state')
                    if state:
                        match_score = min(len(search_core), len(dtbc_core))
                        if match_score > best_match_score:
                            best_match_state = state
                            best_match_score = match_score
    
    if best_match_state:
        return best_match_state
    
    # Fourth pass: Try matching on original terms (fallback)
    for record in dtbc_data:
        dtbc_substation = record.get('substation', '')
        if dtbc_substation and isinstance(dtbc_substation, str):
            dtbc_substation_lower = dtbc_substation.strip().lower()
            
            if search_term in dtbc_substation_lower or dtbc_substation_lower in search_term:
                state = record.get('state')
                if state:
                    match_score = min(len(search_term), len(dtbc_substation_lower))
                    if match_score > best_match_score:
                        best_match_state = state
                        best_match_score = match_score
    
    # No match found
    return best_match_state


def normalize_regional_hub_to_state(state_value: str) -> str:
    """
    Normalize regional hub/station names to their actual state names.
    
    Some PDFs use regional hub names instead of state names:
    - 'Paradeep' → 'Odisha'
    - 'Neemarana' → 'Rajasthan'
    - 'Patna' → 'Bihar'
    
    Args:
        state_value: State or regional hub name
        
    Returns:
        Actual state name
    """
    if not state_value or not isinstance(state_value, str):
        return state_value
    
    # Mapping of regional hubs to their actual states
    REGIONAL_HUB_TO_STATE = {
        'paradeep': 'Odisha',
        'neemarana': 'Rajasthan',
        'patna': 'Bihar',
        'raipur': 'Chhattisgarh',
        'gaya': 'Bihar',
        'dhanbad': 'Jharkhand',
        'jamshedpur': 'Jharkhand',
        'ranchi': 'Jharkhand',
        'mundra': 'Gujarat',
        'surat': 'Gujarat',
        'vadodara': 'Gujarat',
        'nagpur': 'Maharashtra',
        'pune': 'Maharashtra',
        'aurangabad': 'Maharashtra',
        'indore': 'Madhya Pradesh',
        'bhopal': 'Madhya Pradesh',
        'jabalpur': 'Madhya Pradesh',
    }
    
    state_lower = state_value.strip().lower()
    
    # Check if it's a regional hub
    if state_lower in REGIONAL_HUB_TO_STATE:
        return REGIONAL_HUB_TO_STATE[state_lower]
    
    # Otherwise return the original value
    return state_value


def extract_voltage_level(text: str) -> int:
    """
    Extract the voltage level from a voltage string.
    Returns the LAST (rightmost) number before 'kV'.
    
    Examples:
    - '400/220kV' → 220
    - '765/400kV' → 400
    - '400/230 kV' → 230
    - '220kV' → 220
    
    Args:
        text: String containing voltage information
        
    Returns:
        Voltage level as integer, or None if not found
    """
    import re
    
    if not text or not isinstance(text, str):
        return None
    
    # Pattern to find all numbers followed by optional space and kV/KV (case insensitive)
    # This will capture: 765/400kV, 400/220 kV, 400/220 KV, etc.
    pattern = r'(\d+)\s*[Kk][Vv]'
    matches = re.findall(pattern, text)
    
    if matches:
        # Return the LAST match (rightmost voltage level)
        return int(matches[-1])
    
    return None


def replace_multiplication_patterns(text: str) -> str:
    """
    Replace multiplication patterns (NxMMM) with their calculated products in text.
    Preserves all surrounding context.
    
    Examples:
    - '(3x1500)' → '(4500)'
    - '(1x1500)' → '(1500)'
    - 'Sec-II ICTs: Jun-26 (3x1500) & 2026-27 (1x1500)' → 'Sec-II ICTs: Jun-26 (4500) & 2026-27 (1500)'
    
    Args:
        text: String that may contain multiplication patterns
        
    Returns:
        String with multiplication patterns replaced by their products
    """
    import re
    
    if not text or not isinstance(text, str):
        return text
    
    # Pattern to find multiplication formulas: NxMMM or N×MMM
    # Examples: 3x1500, 2X315, 1×500
    # Captures the entire match so we can replace it
    pattern = r'(\d+)\s*[xX×]\s*(\d+(?:\.\d+)?)'
    
    def replace_match(match):
        count = float(match.group(1))
        capacity = float(match.group(2))
        result = count * capacity
        # Return as integer if it's a whole number
        if result == int(result):
            return str(int(result))
        return str(result)
    
    return re.sub(pattern, replace_match, text)


def calculate_mva_capacity(text: str) -> float:
    """
    Calculate MVA capacity from formula strings.
    
    Handles:
    - Simple multiplication: '4x500MVA' → 2000
    - Addition: '2x315MVA + 1x500MVA' → 1130
    - Multiple terms: '2x315 + 3x200 + 1x500' → 630 + 600 + 500 = 1730
    
    Args:
        text: String containing MVA formula (e.g., '4x500MVA', '2x315+1x500MVA')
        
    Returns:
        Calculated MVA capacity as float, or None if no valid formula found
    """
    import re
    
    if not text or not isinstance(text, str):
        return None
    
    # Pattern to find multiplication formulas: NxMMM or N×MMM
    # Examples: 4x500, 2X315, 3×200
    pattern = r'(\d+)\s*[xX×]\s*(\d+(?:\.\d+)?)'
    
    matches = re.findall(pattern, text)
    
    if not matches:
        return None
    
    # Calculate sum of all multiplication terms
    total = 0.0
    for count, capacity in matches:
        total += float(count) * float(capacity)
    
    return total if total > 0 else None


def parse_capacity_segment(segment: str) -> dict:
    """
    Parse a single capacity segment to extract voltage level and MVA capacity.
    
    A segment is one part separated by semicolon, containing:
    - MVA capacity formula (e.g., '4x500MVA', '2x315+1x500MVA')
    - Voltage level (e.g., '400/220kV', '765/400kV')
    
    Examples:
    - '4x500MVA, 400/220kV' → {'voltage_kv': 220, 'mva': 2000}
    - '2x315MVA + 1x500MVA, 400/220kV' → {'voltage_kv': 220, 'mva': 1130}
    
    Args:
        segment: String segment containing MVA formula and voltage
        
    Returns:
        Dict with 'voltage_kv' and 'mva' keys, or None if parsing fails
    """
    if not segment or not isinstance(segment, str):
        return None
    
    segment = segment.strip()
    if not segment:
        return None
    
    # Extract voltage level
    voltage_kv = extract_voltage_level(segment)
    
    # Extract and calculate MVA capacity
    mva = calculate_mva_capacity(segment)
    
    # Only return if we found at least voltage or MVA
    if voltage_kv is not None or mva is not None:
        return {
            'voltage_kv': voltage_kv,
            'mva': mva
        }
    
    return None


def normalize_capacity_string(text: str) -> str:
    """
    Normalize capacity strings by inserting semicolons where voltage specifications
    are directly followed by capacity formulas (no space/separator) OR where multiple
    voltage specifications appear in the same string.
    
    This handles cases where PDF extraction concatenates segments like:
    - "2x1500MVA, 765/400kV2x500MVA, 400/220kV" (no space after kV)
    - "1x1500MVA, 765/400kV, 1x500MVA, 400/220kV" (comma instead of semicolon)
    - "2x1500MVA, 765/400kV 2x500MVA, 400/220kV" (single space separator)
    
    And converts them to:
    - "2x1500MVA, 765/400kV; 2x500MVA, 400/220kV"
    - "1x1500MVA, 765/400kV; 1x500MVA, 400/220kV"
    - "2x1500MVA, 765/400kV; 2x500MVA, 400/220kV"
    
    But preserves:
    - "400/220kV, 4X500MVA" (comma within same segment - voltage and formula together)
    
    Args:
        text: Raw capacity string from PDF
        
    Returns:
        Normalized string with semicolons inserted between segments
    """
    import re
    
    if not text or not isinstance(text, str):
        return text
    
    # STEP 1: Handle case where kV is directly followed by a digit (no space)
    # Pattern: "kV" or "KV" followed immediately by a digit (start of next formula)
    # Example: "765/400kV2x500MVA" -> "765/400kV; 2x500MVA"
    normalized = re.sub(r'([Kk][Vv])(\d)', r'\1; \2', text)
    
    # STEP 2: Handle case where kV is followed by comma/space and ANOTHER MVA formula
    # that has its OWN voltage specification (indicating a new segment)
    # Pattern: "kV" followed by ", " (with optional whitespace/newline) and then 
    # a digit followed by "x" (indicating NxMVA formula)
    # But we need to check if this new formula has its own voltage (contains kV later)
    # Example: "1x1500MVA, 765/400kV, 1x500MVA, 400/220kV" -> split at second occurrence
    # But NOT: "400/220kV, 4X500MVA" -> this is ONE segment (formula comes after voltage)
    
    # Strategy: Look for pattern "kV" + optional comma/whitespace + "NxMVA" + comma/space + voltage
    # This indicates the NxMVA starts a NEW segment
    # We need to check if there's another voltage spec (kV) after the formula
    
    # For now, use a simpler approach:
    # Only insert semicolon if kV is followed by comma/space AND the next part contains BOTH
    # a formula (NxMVA) AND another voltage (kV)
    
    # STEP 2a: Handle "kV, 1x500MVA, 400/220kV" - comma followed by formula with voltage
    # Look ahead to see if there's a voltage spec after the MVA formula
    # Pattern: kV followed by comma/space, then formula, then another kV
    normalized = re.sub(
        r'([Kk][Vv]),\s+(\d+[xX]\d+\s*MVA[^;,]*,\s*\d+)',
        r'\1; \2',
        normalized
    )
    
    # STEP 3: Handle case where kV is followed by ONE OR MORE spaces and then a digit
    # that starts a NEW segment (has its own voltage later)
    # This catches patterns like "765/400kV 2x500MVA" (space-separated segments)
    # Example: "2x1500MVA, 765/400kV 2x500MVA, 400/220kV" -> "2x1500MVA, 765/400kV; 2x500MVA, 400/220kV"
    # But NOT: "400/220kV 4X500MVA" if there's no voltage after MVA (same segment)
    
    # Only add semicolon if there's a space followed by a formula that has its own voltage
    # Pattern: kV + space + formula (NxMVA) that's followed by a voltage (contains kV)
    normalized = re.sub(
        r'([Kk][Vv])\s+(\d+[xX]\d+\s*MVA[^;]*\d+[Kk][Vv])',
        r'\1; \2',
        normalized
    )
    
    return normalized


def split_transformation_capacity_row(row: dict) -> list:
    """
    Split a Transformation Capacity row into multiple rows based on voltage levels.
    
    Process all three capacity columns:
    - existing_mva
    - under_implementation_mva
    - planned_mva
    
    Each semicolon-separated segment creates a new row.
    For example:
        "1x1500 MVA, 765/400 kV; 4X500 MVA, 400/220 KV"
        Should create 2 rows:
        - Row 1: voltage=400, mva=1500 (from first segment)
        - Row 2: voltage=220, mva=4000 (from second segment)
    
    Args:
        row: Dictionary containing transformation capacity data
        
    Returns:
        List of dictionaries (one per voltage level/segment)
    """
    # Collect segments from all three capacity columns
    output_rows = []
    
    # Process each capacity column
    for column_name in ['existing_mva', 'under_implementation_mva', 'planned_mva']:
        value = row.get(column_name, '')
        if value and isinstance(value, str) and value.strip():
            # STEP 1: Normalize the capacity string to handle concatenated segments
            # This converts "765/400kV2x500MVA" to "765/400kV; 2x500MVA"
            normalized_value = normalize_capacity_string(value)
            
            # STEP 2: Split by semicolon to get individual segments
            segments = [s.strip() for s in normalized_value.split(';') if s.strip()]
            
            for segment in segments:
                parsed = parse_capacity_segment(segment)
                if parsed and parsed.get('voltage_kv') is not None:
                    voltage_kv = parsed['voltage_kv']
                    mva = parsed['mva']
                    
                    # Check if we already have a row for this voltage in this column
                    # Find existing row with this voltage
                    existing_row = None
                    for out_row in output_rows:
                        if out_row.get('voltage_level_kv') == voltage_kv:
                            # Check if this column is already populated
                            if out_row.get(column_name) is None:
                                existing_row = out_row
                                break
                    
                    if existing_row:
                        # Add MVA to existing row
                        existing_row[column_name] = mva
                    else:
                        # Create new row for this voltage level
                        new_row = {
                            's_no': row.get('s_no'),
                            'region': row.get('region'),
                            'state': row.get('state'),
                            'substation': row.get('substation'),
                            'voltage_level_kv': voltage_kv,
                            'existing_mva': None,
                            'under_implementation_mva': None,
                            'planned_mva': None
                        }
                        new_row[column_name] = mva
                        output_rows.append(new_row)
    
    # If no rows were created, return a single row with None values
    if not output_rows:
        return [{
            's_no': row.get('s_no'),
            'region': row.get('region'),
            'state': row.get('state'),
            'substation': row.get('substation'),
            'voltage_level_kv': None,
            'existing_mva': None,
            'under_implementation_mva': None,
            'planned_mva': None
        }]
    
    # Sort rows by voltage (descending - higher voltage first)
    output_rows.sort(key=lambda x: x.get('voltage_level_kv') or 0, reverse=True)
    
    return output_rows


def clean_application_quantum(value: str) -> str:
    """
    Clean Application Quantum field to extract only the connectivity value.
    
    Handles cases like:
    "Connectivity:880\\nMax Injection: 800\\nMax Drawl:880" -> "880"
    
    Args:
        value: Raw value from PDF extraction
        
    Returns:
        Cleaned value (Connectivity quantum only)
    """
    import re
    
    if not value or not isinstance(value, str):
        return value
    
    original = value.strip()
    
    # Check for "Connectivity:" pattern (common in PSP applications)
    # Case insensitive match for "Connectivity:" followed by number
    match = re.search(r'Connectivity\s*[:]\s*([\d\.]+)', original, re.IGNORECASE)
    
    if match:
        # Return just the number found after Connectivity:
        return match.group(1).strip()
    
    # If no specific pattern found, return original value
    return original

