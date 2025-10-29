"""
Field name mappings for PDF column headers to canonical field names.
Maps various PDF column header variations to standardized field names.
"""

# Canonical field names for each sheet
DATA_TO_BE_CAPTURED_FIELDS = [
    "sr_no", "region", "state", "substation", "coordinates",
    "name_of_developers", "group", "application_id",
    "application_id_enhancement_5_2_or_revision",
    "cmets_lta_gna_approved", "cmets_lta_gna_meeting_date",
    "type", "application_quantum_mw", "status_of_lta",
    "installed_breakup_capacity_mw", "battery", "psp", "commissioned",
    "application_date", "mode", "applied_start_of_connectivity",
    "gna_operationalization", "gna_operationalization_yes_no",
    "date_for_additional_capacity", "nature_of_applicant",
    "voltage_level_kv", "bay_no", "cts_element_unique_code",
    "ats_element_unique_code", "dtl_element_unique_code",
    "date_of_last_element_unique_code", "in_principle_grant",
    "final_grant", "land_bg_conversion_date", "remarks"
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
    
    # Application ID variations
    "application id": "application_id",
    "app id": "application_id",
    "reference no": "application_id",
    "application no": "application_id",
    "ref no": "application_id",
    
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
    
    # Look up in mapping
    return HEADER_MAPPINGS.get(normalized, header)


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
