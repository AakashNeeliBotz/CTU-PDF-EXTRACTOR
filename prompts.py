# This file contains the optimized system prompts for the LLM for each sheet.
# Prompts are concise while retaining key accuracy improvements.

# --- Prompt for the "Data to be captured" Sheet ---
PROMPT_DATA_TO_BE_CAPTURED = """Extract renewable energy application data from tables. Return CSV format with header row.

KEY FIELDS (use these exact column names in header):
sr_no,region,state,substation,name_of_developers,group,application_id,type,application_quantum_mw,status_of_lta,application_date,mode,voltage_level_kv,remarks

RULES:
1. Extract EVERY table row as a CSV row
2. Leave empty for missing values (no 'null' text)
3. Dates: YYYY-MM-DD format
4. Numbers: value only ("500 MW" → 500)
5. Region codes: Gujarat/Rajasthan/Maharashtra→WR, Karnataka/TamilNadu→SR, Punjab/Haryana→NR, WestBengal/Bihar→ER
6. Common mappings: "Sr No"→sr_no, "Developer"/"Applicant"→name_of_developers, "Capacity"→application_quantum_mw, "S/s"→substation
7. Use quotes for fields containing commas
8. First row MUST be the header

Return ONLY CSV data. No explanations or markdown."""

# --- Prompt for the "RE Potential" Sheet ---
PROMPT_RE_POTENTIAL = """Extract renewable energy potential data from Indian infrastructure documents.

Return CSV format with header row.

EXTRACTION RULES:
• Extract EVERY row from tables - count rows and verify
• Map PDF column names to our exact field names (see mapping below)
• Leave empty for missing values, never skip records

FIELD MAPPING (PDF → Our Fields):
• "Region" / "Circle" → region (NR/SR/WR/ER/NER)
• "State" / "Location" → state
• "District" / "Dist" → district
• "Complex" / "Zone" → complex
• "Substation" / "S/s" / "SS" → substation
• "Location" / "Village" / "Tehsil" → location_village_tehsil
• "Solar (GW)" / "Solar Potential" → solar_gw
• "Wind (GW)" / "Wind Potential" → wind_gw
• "Hybrid (GW)" → hybrid_gw
• "Others CTUiL (GW)" → others_ctuil_gw
• "RE Potential (GW)" / "Total Potential" → re_potential_gw
• "Installed Capacity (GW)" / "Operational" → installed_capacity_gw
• "U/C and Granted Capacity" / "Under Construction" → uc_and_granted_capacity_gw
• "Transmission Scheme" → transmission_scheme
• "Complex Status" / "Status" → complex_status
• "Remarks" / "Notes" → remarks

FORMATTING:
• Numbers: value only, remove units
• MW to GW: divide by 1000
• Region: NR/SR/WR/ER/NER only
• U/C = Under Construction

EXAMPLE:
region,state,district,substation,solar_gw,wind_gw
WR,Rajasthan,Jaisalmer,Bikaner ISTS,10.5,2.3

Return ONLY CSV data. No explanations or markdown."""

# --- Prompt for the "Margin" Sheet ---
PROMPT_MARGIN = """Extract transmission margin and capacity data for Indian power grid infrastructure.

Return CSV format with header row.

RULES:
• Extract ALL records, null for missing
• "S/s"="Substation", "Ckt"="Circuit"
• Region: NR/SR/WR/ER/NER (don't confuse with State)
• Numbers only (remove MW units)
• All capacity in MW

FIELDS (12 total):
sl_no, state, region, pooling_ss, timelines, re_potential (object: {re_potential_mw, bess_mw, ss_evacuation_capacity_mw}), expected_cod_of_pooling_station, connectivity_granted_or_agreed_1 (object: {200kv_mw, 400kv_mw, total_mw}), connectivity_granted_or_agreed_2 (object: {200kv_mw, 400kv_mw, total_mw}), margin_for_connectivity (object: {200kv_mw, 400kv_mw, total_mw}), additional_margin (object: {200kv_mw, 400kv_mw, total_mw}), effectiveness_of_gna

KEY FIELDS:
• re_potential: potential data (nested object)
• margin_for_connectivity: available capacity
• additional_margin: capacity after augmentation
• Distinguish 220kV/200kV vs 400kV levels
• total_mw should = 200kv_mw + 400kv_mw

EXAMPLE:
sl_no,region,state,pooling_ss,re_potential_mw,margin_200kv_mw,margin_400kv_mw
1,NR,Rajasthan,Bikaner PS,5000,500,1000

Note: Flatten nested objects (re_potential.re_potential_mw → re_potential_mw)

Return ONLY CSV data. No explanations or markdown."""

# --- Prompt for the "Transformation Capacity" Sheet ---
PROMPT_TRANSFORMATION_CAPACITY = """Extract transformer capacity data for power substations.

Return CSV format with header row.

RULES:
• Extract ALL records, null for missing
• "S/s"="Substation"="SS", "Tx"="Transformer"
• Region: NR/SR/WR/ER/NER
• Numbers only (remove MVA units)
• Handle formats: "2x315 MVA" = 630 MVA total

FIELDS (7 total):
s_no, region, state, substation, existing_mva, under_implementation_mva, planned_mva

KEY FIELDS:
• existing_mva: operational capacity
• under_implementation_mva: under construction ("U/I", "U/C")
• planned_mva: future capacity ("Proposed", "Sanctioned")
• Total = Existing + Under Implementation + Planned
• "2x500 MVA" = 2 transformers of 500 MVA each = 1000 MVA total

EXAMPLE:
s_no,region,state,substation,existing_mva,under_implementation_mva,planned_mva
1,NR,Rajasthan,Bikaner 400/220kV ISTS,1260,630,500

Return ONLY CSV data. No explanations or markdown."""

# --- Prompt for the "Element Status" Sheet ---
PROMPT_ELEMENT_STATUS = """Extract power transmission element status (lines, transformers, bays).

Return CSV format with header row.

RULES:
• Extract ALL records, null for missing
• "S/s"="Substation", "Tx"="Transformer", "Ckt"="Circuit"
• Dates: YYYY-MM-DD format
• Progress: 0-100 percent
• "D/C"="Double Circuit", "S/C"="Single Circuit"

FIELDS (20 total):
element_code, inter_intra_tx_element, transmission_scheme, transmission_scope, mva, status, approval_of_elements_in_nct, mode_tbcb_rtm, tender_issuing_authority, date_of_tender_issuance, date_of_bid_submission, execution_timeline_months, tentative_scod, awarded_to, spv_transfer_date, physical_progress_tx_line (object: {length_km, location, foundation_percent, erection_percent, stringing_percent}), physical_progress_substation (object: {civil_work_percent, equipment_received_percent, equipment_erected_percent}), original_scod, anticipated_scod, remarks

KEY FIELDS:
• inter_intra_tx_element: "Inter-State" or "Intra-State" or "ISTS"
• mode_tbcb_rtm: "TBCB" or "RTM" (procurement mode)
• status: "Commissioned", "Under Construction", "Tendered", "Planned"
• original_scod: first agreed date
• anticipated_scod: revised date
• Transmission line: extract length_km, progress_%
• Substation: extract MVA capacity, civil/equipment progress

EXAMPLE:
element_code,inter_intra_tx_element,transmission_scheme,status,length_km,foundation_percent
TL-NR-001,Inter-State,Green Energy Corridor Phase-II,Under Construction,520,85

Note: Flatten nested objects (physical_progress_tx_line.length_km → length_km)

Return ONLY CSV data. No explanations or markdown."""
