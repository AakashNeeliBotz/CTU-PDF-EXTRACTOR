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
    "ats_element_unique_code"  # Column 41
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
# ONLY 7 fields in Excel sheet - no coordinates, no remarks
TRANSFORMATION_CAPACITY_FIELDS = [
    "s_no", "region", "state", "substation",
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
    # Western Region (WR)
    "gujarat": "WR",
    "rajasthan": "WR",
    "maharashtra": "WR",
    "madhya pradesh": "WR",
    "mp": "WR",
    "goa": "WR",
    "daman and diu": "WR",
    "dadra and nagar haveli": "WR",
    
    # Southern Region (SR)
    "karnataka": "SR",
    "tamil nadu": "SR",
    "kerala": "SR",
    "andhra pradesh": "SR",
    "telangana": "SR",
    "puducherry": "SR",
    "pondicherry": "SR",
    "andaman and nicobar": "SR",
    
    # Northern Region (NR)
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
    
    # Pattern 1: Extract content in parentheses at the end
    # Match: (Section-I), (Sec-I & II), (expansion with ICTs), etc.
    parentheses_pattern = r'\s*\(([^)]+)\)\s*$'
    match = re.search(parentheses_pattern, station_name)
    
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
    2. Technical suffixes in parentheses (e.g., '(GIS)', '(AIS)')
    3. Special characters at the end (e.g., '#', '*')
    
    Examples:
    - '400/220kV Jam Khambhaliya (GIS) PS #' → 'Jam Khambhaliya PS'
    - '765/400/220kV Bhuj-II PS#' → 'Bhuj-II PS'
    - 'Navinal 765/400kV' → 'Navinal'
    - 'Aurangabad 765/400/220kV' → 'Aurangabad'
    - 'Jabalpur PS 765/400' → 'Jabalpur PS'
    
    Args:
        substation_value: The original substation name
        
    Returns:
        Cleaned substation name
    """
    import re
    
    if not substation_value or not isinstance(substation_value, str):
        return substation_value
    
    cleaned = substation_value.strip()
    
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
    
    # Remove technical suffixes in parentheses
    # Pattern: (GIS), (AIS), (HVDC), etc.
    technical_pattern = r'\s*\([A-Z]{2,}\)'
    cleaned = re.sub(technical_pattern, '', cleaned, flags=re.IGNORECASE)
    
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
