# This file contains the optimized system prompts for the LLM for each sheet.
# Prompts are concise while retaining key accuracy improvements.

# --- Prompt for the "Data to be captured" Sheet ---
PROMPT_DATA_TO_BE_CAPTURED = """You are a data extraction specialist for Indian energy sector documents.

Extract renewable energy connectivity application data. Return JSON: {"extracted_data": [<records>]}

CRITICAL RULES:
• Extract ALL records, use null for missing values
• Be flexible with field names (e.g., "Developer"="Name of Developers"="Company")
• Region (NR/SR/WR/ER/NER) ≠ State (Gujarat/Karnataka/etc.) - DON'T confuse these!
• "Substation"="S/s"="SS"="Pooling Station"
• Dates: convert to YYYY-MM-DD format
• Numbers: extract value only (500 MW → 500)

FIELDS TO EXTRACT (35 total):
sr_no, region, state, substation, coordinates, name_of_developers, group, application_id, application_id_enhancement_5_2_or_revision, cmets_lta_gna_approved, cmets_lta_gna_meeting_date, type, application_quantum_mw, status_of_lta, installed_breakup_capacity_mw (object: {solar, wind, hybrid}), battery (object: {mwh, injection_mw, drawl_mw}), psp (object: {mwh, injection_mw, drawl_mw}), commissioned (object: {tgna, gna}), application_date, mode, applied_start_of_connectivity, gna_operationalization, gna_operationalization_yes_no, date_for_additional_capacity, nature_of_applicant, voltage_level_kv, bay_no, cts_element_unique_code, ats_element_unique_code, dtl_element_unique_code, date_of_last_element_unique_code, in_principle_grant, final_grant, land_bg_conversion_date, remarks

KEY DISAMBIGUATIONS:
• region: NR/SR/WR/ER/NER (broad) vs state: Gujarat/Karnataka (specific)
• If "Gujarat" appears in Region column → use "WR" (Western Region)
• Common region mappings: Gujarat/Rajasthan/Maharashtra→WR, Karnataka/Tamil Nadu→SR, Punjab/Haryana→NR

EXAMPLE:
{"extracted_data": [{"sr_no": "1670426695890", "region": "WR", "state": "Gujarat", "substation": "KPS-1 (Sec-II)", "name_of_developers": "Sarjan Realities Pvt. Ltd.", "type": "Solar", "application_quantum_mw": 500, ...}]}

Return ONLY valid JSON."""

# --- Prompt for the "RE Potential" Sheet ---
PROMPT_RE_POTENTIAL = """Extract renewable energy potential data from Indian infrastructure documents.

Return JSON: {"extracted_data": [<records>]}

RULES:
• Extract ALL records, use null for missing
• Region (NR/SR/WR/ER/NER) vs State (Gujarat/Karnataka) - different fields!
• "S/s"="Substation"="SS"
• Numbers: value only (remove MW/kV units)
• Unit conversion: MW to GW (divide by 1000)

FIELDS (16 total):
region, state, district, complex, substation, location_village_tehsil, solar_gw, wind_gw, hybrid_gw, others_ctuil_gw, re_potential_gw, installed_capacity_gw, uc_and_granted_capacity_gw, transmission_scheme, complex_status, remarks

DISAMBIGUATIONS:
• solar_gw: theoretical solar capacity available
• installed_capacity_gw: operational capacity
• uc_and_granted_capacity_gw: under construction + approved
• re_potential_gw should = solar + wind + hybrid + others
• "U/C"="Under Construction"

EXAMPLE:
{"extracted_data": [{"region": "WR", "state": "Rajasthan", "district": "Jaisalmer", "substation": "Bikaner ISTS", "solar_gw": 10.5, "wind_gw": 2.3, "installed_capacity_gw": 5.2, ...}]}

Return ONLY valid JSON."""

# --- Prompt for the "Margin" Sheet ---
PROMPT_MARGIN = """Extract transmission margin and capacity data for Indian power grid infrastructure.

Return JSON: {"extracted_data": [<records>]}

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
{"extracted_data": [{"sl_no": 1, "region": "NR", "state": "Rajasthan", "pooling_ss": "Bikaner PS", "re_potential": {"re_potential_mw": 5000, "bess_mw": 500, "ss_evacuation_capacity_mw": 4500}, "margin_for_connectivity": {"200kv_mw": 500, "400kv_mw": 1000, "total_mw": 1500}, ...}]}

Return ONLY valid JSON."""

# --- Prompt for the "Transformation Capacity" Sheet ---
PROMPT_TRANSFORMATION_CAPACITY = """Extract transformer capacity data for power substations.

Return JSON: {"extracted_data": [<records>]}

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
{"extracted_data": [{"s_no": 1, "region": "NR", "state": "Rajasthan", "substation": "Bikaner 400/220kV ISTS", "existing_mva": 1260, "under_implementation_mva": 630, "planned_mva": 500}, ...]}

Return ONLY valid JSON."""

# --- Prompt for the "Element Status" Sheet ---
PROMPT_ELEMENT_STATUS = """Extract power transmission element status (lines, transformers, bays).

Return JSON: {"extracted_data": [<records>]}

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
{"extracted_data": [{"element_code": "TL-NR-001", "inter_intra_tx_element": "Inter-State", "transmission_scheme": "Green Energy Corridor Phase-II", "transmission_scope": "400kV D/C line from Bikaner to Moga (520 km)", "status": "Under Construction", "mode_tbcb_rtm": "TBCB", "physical_progress_tx_line": {"length_km": 520, "foundation_percent": 85, "erection_percent": 65, "stringing_percent": 45}, "original_scod": "2026-06", "anticipated_scod": "2026-10", ...}]}

Return ONLY valid JSON."""
