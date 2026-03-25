from __future__ import annotations

import os
import re
from datetime import datetime

import camelot
import fitz

from cmets_extractor.config import (
    CMETS_34TH_MEETING_DATE,
    CMETS_34TH_MEETING_NUMBER,
    PDF_PATH_34TH,
)
from cmets_extractor.domain.common.dates import parse_date
from cmets_extractor.domain.common.ids import is_lta_application_id, remove_leading_zeros
from cmets_extractor.domain.common.numbers import parse_numeric_value
from cmets_extractor.domain.common.text import clean_text
from cmets_extractor.domain.data_capture_common import (
    clean_substation_value,
    extract_34th_gna_date_from_text,
    extract_34th_substation_from_text,
    extract_34th_voltage_from_text,
    parse_34th_nature_and_type,
    parse_34th_quantum,
    parse_project_location,
    strip_ps_suffix,
)
from cmets_extractor.domain.element_status_runtime import (
    apply_cmets_element_codes_to_record,
    get_annexure_elements_lookup,
)
from cmets_extractor.domain.hybrid_context import extract_34th_status_from_text
from cmets_extractor.run_context import ExtractionRunContext, build_run_context


def _resolve_context(run_context: ExtractionRunContext | None) -> ExtractionRunContext:
    return run_context if run_context is not None else build_run_context()


def build_34th_page_text_map():
    """Load the 34th PDF text page-by-page for collapsed-row recovery."""
    page_text_map = {}
    doc = fitz.open(PDF_PATH_34TH)
    for idx, page in enumerate(doc):
        page_text_map[idx + 1] = page.get_text()
    doc.close()
    return page_text_map


def extract_34th_row_segment_from_page_text(app_id, page_text):
    """Extract one collapsed connectivity row segment from one page."""
    if not page_text:
        return None

    normalized = re.sub(r"\s+", " ", page_text)
    app_match = re.search(r"\b" + re.escape(str(app_id)) + r"\b", normalized)
    if not app_match:
        return None

    start = app_match.start()
    tail = normalized[app_match.end():]
    next_row = re.search(r"\b\d+\.\s*22\d{8}\b", tail)
    if next_row:
        end = app_match.end() + next_row.start()
    else:
        end = min(len(normalized), app_match.end() + 2200)

    return normalized[start:end].strip()


def extract_34th_row_segment_from_full_text(app_id, full_text):
    """Extract one collapsed connectivity row segment from the full 34th text."""
    if not full_text:
        return None

    normalized = re.sub(r"\s+", " ", full_text)
    app_match = re.search(r"\b" + re.escape(str(app_id)) + r"\b", normalized)
    if not app_match:
        return None

    start = app_match.start()
    tail = normalized[app_match.end():]
    next_row = re.search(r"\b\d+\.\s*22\d{8}\b", tail)
    if next_row:
        end = app_match.end() + next_row.start()
    else:
        end = min(len(normalized), app_match.end() + 2600)

    return normalized[start:end].strip()


def split_34th_applicant_and_location(body_text):
    """Split one collapsed-row body into applicant and location text."""
    body = " ".join(str(body_text).split()).strip()
    if not body:
        return None, None

    distt_match = re.search(r"\bdistt\.,", body, re.IGNORECASE)
    if distt_match:
        before = body[:distt_match.start()].strip()
        after = body[distt_match.end():].strip()
        parts = before.split()
        if len(parts) >= 2:
            district = parts[-1]
            applicant = " ".join(parts[:-1]).strip()
            location = f"{district} distt.," + (f" {after}" if after else "")
            if applicant:
                return applicant, location.strip()

    loc_match = re.search(
        r"([A-Za-z]+(?:\s+[A-Za-z]+){0,2}\s+distt\.,(?:\s*[A-Za-z]+(?:\s+[A-Za-z]+){0,2})?)\s*$",
        body,
        re.IGNORECASE,
    )
    if loc_match:
        location = loc_match.group(1).strip()
        applicant = body[:loc_match.start()].strip()
        if applicant:
            return applicant, location
        return None, location

    return body, None


def build_connectivity_record_from_page_text(
    app_id,
    page_num,
    page_text_map,
    full_text=None,
    *,
    run_context: ExtractionRunContext | None = None,
):
    """Build one 34th connectivity record from collapsed page text."""
    context = _resolve_context(run_context)
    page_text = page_text_map.get(page_num)
    segment = extract_34th_row_segment_from_full_text(app_id, full_text)
    if not segment:
        segment = extract_34th_row_segment_from_page_text(app_id, page_text)
    if not segment:
        return None

    row_match = re.search(
        r"\b" + re.escape(str(app_id)) + r"\b\s+(.+?)\s+"
        r"(\d{2}\.\d{2}\.\d{4})\s+"
        r"Generator\s*\(([^)]+)\)\s+"
        r"Land\s+BG\s+Route\s+"
        r"(\d+(?:\.\d+)?)\s+"
        r"(\d{2}\.\d{2}\.\d{4})\s+"
        r"([A-Za-z0-9\-\(\)\s]+?PS)\s+"
        r"(?:NA|\uf0b7|It\s+was|Applicant|Accordingly)",
        segment,
        re.IGNORECASE,
    )
    if not row_match:
        return None

    body_text = row_match.group(1)
    submission_date = row_match.group(2)
    energy_type = row_match.group(3).strip()
    quantum_val = parse_numeric_value(row_match.group(4))
    applied_start_date = row_match.group(5)
    substation_raw = row_match.group(6).strip()

    applicant_name, location_text = split_34th_applicant_and_location(body_text)

    record = {}
    if is_lta_application_id(app_id):
        record["lta_application_id"] = remove_leading_zeros(app_id)
        record["gna_st_ii_application_id"] = None
        record["cmets_lta_approved"] = CMETS_34TH_MEETING_NUMBER
        record["cmets_lta_meeting_date"] = CMETS_34TH_MEETING_DATE
    else:
        record["gna_st_ii_application_id"] = remove_leading_zeros(app_id)
        record["lta_application_id"] = None
        record["cmets_gna_approved"] = CMETS_34TH_MEETING_NUMBER
        record["cmets_gna_meeting_date"] = CMETS_34TH_MEETING_DATE

    record["name_of_developers"] = applicant_name
    state, region = parse_project_location(location_text, substation_raw)
    record["state"] = state
    record["region"] = region
    record["application_date"] = submission_date
    record["nature_of_applicant"] = "Generator"
    record["type"] = energy_type
    record["mode_criteria"] = "Land BG Route"
    record["application_quantum_mw"] = quantum_val
    record["applied_start_date"] = applied_start_date
    record["substation"] = clean_substation_value(substation_raw, segment, applicant_name)

    status = extract_34th_status_from_text(segment)
    record["status_of_application"] = status

    voltage, text_substation = extract_34th_voltage_from_text(segment)
    if not voltage and substation_raw:
        loc_kv = re.search(r"(\d+)\s*kV", str(substation_raw), re.IGNORECASE)
        if loc_kv:
            voltage = int(loc_kv.group(1))
    if not voltage and segment:
        generic_kv = re.search(r"(\d+)\s*kV", segment, re.IGNORECASE)
        if generic_kv:
            voltage = int(generic_kv.group(1))

    if status == "Withdrawn":
        voltage = None

    record["voltage_level_kv"] = voltage
    if status == "Granted" and text_substation:
        record["substation"] = text_substation

    if status == "Granted" and quantum_val is not None:
        record["granted_quantum_mw"] = quantum_val

    if energy_type == "Solar" and quantum_val is not None:
        record["installed_breakup_solar_mw"] = quantum_val
    elif energy_type == "Wind" and quantum_val is not None:
        record["installed_breakup_wind_mw"] = quantum_val
    elif energy_type == "BESS" and quantum_val is not None:
        record["battery_injection_mw"] = quantum_val

    gna_date = extract_34th_gna_date_from_text(segment)
    if not gna_date and status == "Granted" and segment:
        all_dates = re.findall(r"(\d{2}[\.\-]\d{2}[\.\-]\d{4})", segment)
        if all_dates:
            parsed_dates = [(parse_date(date_text), date_text) for date_text in all_dates if parse_date(date_text)]
            if parsed_dates:
                parsed_dates.sort(key=lambda item: item[0], reverse=True)
                gna_date = parsed_dates[0][1]
    if gna_date:
        record["gna_operationalization_date"] = gna_date
        parsed_gna = parse_date(gna_date)
        if parsed_gna:
            today = datetime.now()
            record["gna_operationalization_yes_no"] = "Yes" if parsed_gna <= today else "No"

    apply_cmets_element_codes_to_record(
        record,
        segment,
        context,
        annexure_lookup=get_annexure_elements_lookup(PDF_PATH_34TH, context),
    )

    return record


def _build_transition_record(row, delib_text, *, run_context: ExtractionRunContext | None = None):
    """Build one transition-table record from a data row and its deliberation text."""
    context = _resolve_context(run_context)
    record = {}
    record["name_of_developers"] = clean_text(row.iloc[1])

    app_id_raw = clean_text(row.iloc[2])
    if app_id_raw:
        id_match = re.search(r"(\d{7,})", str(app_id_raw).replace(" ", ""))
        if id_match:
            raw_id = id_match.group(1)
            if is_lta_application_id(raw_id):
                record["lta_application_id"] = remove_leading_zeros(raw_id)
                record["gna_st_ii_application_id"] = None
                record["cmets_lta_approved"] = CMETS_34TH_MEETING_NUMBER
                record["cmets_lta_meeting_date"] = CMETS_34TH_MEETING_DATE
            else:
                record["gna_st_ii_application_id"] = remove_leading_zeros(raw_id)
                record["lta_application_id"] = None
                record["cmets_gna_approved"] = CMETS_34TH_MEETING_NUMBER
                record["cmets_gna_meeting_date"] = CMETS_34TH_MEETING_DATE

    record["substation"] = strip_ps_suffix(clean_text(row.iloc[3]))

    mw_text = clean_text(row.iloc[4])
    app_quantum = None
    if mw_text:
        mw_match = re.search(r"(\d+)", mw_text)
        if mw_match:
            app_quantum = int(mw_match.group(1))
            record["application_quantum_mw"] = app_quantum

    record["applied_start_date"] = clean_text(row.iloc[7])
    gna_date_raw = clean_text(row.iloc[8])
    record["gna_operationalization_date"] = gna_date_raw
    if gna_date_raw:
        parsed_gna = parse_date(gna_date_raw)
        if parsed_gna:
            today = datetime.now()
            record["gna_operationalization_yes_no"] = "Yes" if parsed_gna <= today else "No"

    substation = record.get("substation", "")
    _, region = parse_project_location("Rajasthan", substation)
    record["state"] = "Rajasthan"
    record["region"] = region

    status = extract_34th_status_from_text(delib_text)
    record["status_of_application"] = status
    if status:
        print(
            f"    App {record.get('gna_st_ii_application_id') or record.get('lta_application_id')}: "
            f"Status = {status}"
        )

    voltage, text_substation = extract_34th_voltage_from_text(delib_text)
    if status == "Withdrawn":
        voltage = None
    record["voltage_level_kv"] = voltage
    if voltage:
        print(
            f"    App {record.get('gna_st_ii_application_id') or record.get('lta_application_id')}: "
            f"Voltage = {voltage} kV"
        )
    if status == "Granted" and text_substation:
        record["substation"] = text_substation

    if status == "Granted" and app_quantum:
        record["granted_quantum_mw"] = app_quantum

    apply_cmets_element_codes_to_record(
        record,
        delib_text,
        context,
        annexure_lookup=get_annexure_elements_lookup(PDF_PATH_34TH, context),
    )

    return record


def process_34th_transition_tables(*, run_context: ExtractionRunContext | None = None):
    """Extract the 34th transition tables from pages 7-10."""
    context = _resolve_context(run_context)
    print("\n" + "=" * 60)
    print("34th CMETS - Processing TRANSITION Tables (Pages 7-10)")
    print("=" * 60)

    tables = camelot.read_pdf(PDF_PATH_34TH, pages="7-10", flavor="lattice")
    print(f"  Found {len(tables)} tables on pages 7-10")

    ten_col_tables = [table for table in tables if table.df.shape[1] == 10]
    print(f"  Filtered to {len(ten_col_tables)} 10-column tables")

    records = []
    data_row = None
    delib_text = ""

    for table_idx, table in enumerate(ten_col_tables):
        df = table.df
        print(f"\n  Table {table_idx + 1}: {df.shape[0]}r x {df.shape[1]}c")

        for idx in range(1, len(df)):
            row = df.iloc[idx]
            sl_no = str(row.iloc[0]).strip()
            sl_no_clean = re.sub(r"\s+", " ", sl_no).strip()
            if re.search(r"Sl\.?\s*No\.?", sl_no_clean, re.IGNORECASE) and not re.match(r"^\d+\.?$", sl_no_clean):
                continue

            if re.match(r"^\d+\.?$", sl_no):
                if data_row is not None:
                    rec = _build_transition_record(data_row, delib_text, run_context=context)
                    if rec:
                        records.append(rec)

                data_row = row
                delib_text = ""
            else:
                row_text = " ".join([str(cell) for cell in row.values if str(cell).strip()])
                if row_text.strip():
                    delib_text += " " + row_text

    if data_row is not None:
        rec = _build_transition_record(data_row, delib_text, run_context=context)
        if rec:
            records.append(rec)

    print(f"\n  TRANSITION: Extracted {len(records)} records")
    return records


def _build_connectivity_record(data_row_dict, delib_text, *, run_context: ExtractionRunContext | None = None):
    """Build one connectivity-table record from a data row and its deliberation text."""
    context = _resolve_context(run_context)
    row = data_row_dict["_row"]
    app_id = data_row_dict["_app_id"]
    record = {}

    if is_lta_application_id(app_id):
        record["lta_application_id"] = remove_leading_zeros(app_id)
        record["gna_st_ii_application_id"] = None
        record["cmets_lta_approved"] = CMETS_34TH_MEETING_NUMBER
        record["cmets_lta_meeting_date"] = CMETS_34TH_MEETING_DATE
    else:
        record["gna_st_ii_application_id"] = remove_leading_zeros(app_id)
        record["lta_application_id"] = None
        record["cmets_gna_approved"] = CMETS_34TH_MEETING_NUMBER
        record["cmets_gna_meeting_date"] = CMETS_34TH_MEETING_DATE

    record["name_of_developers"] = clean_text(row.iloc[2])
    location_text = clean_text(row.iloc[3])
    substation_raw = clean_text(row.iloc[9])
    state, region = parse_project_location(location_text, substation_raw)
    record["state"] = state
    record["region"] = region
    record["application_date"] = clean_text(row.iloc[4])

    nature_raw = clean_text(row.iloc[5])
    nature, energy_type = parse_34th_nature_and_type(nature_raw)
    record["nature_of_applicant"] = nature
    if energy_type:
        record["type"] = energy_type

    record["mode_criteria"] = clean_text(row.iloc[6])

    quantum_raw = clean_text(row.iloc[7])
    app_quantum, granted_quantum = parse_34th_quantum(quantum_raw)
    record["application_quantum_mw"] = app_quantum
    if granted_quantum is not None:
        record["granted_quantum_mw"] = granted_quantum

    record["applied_start_date"] = clean_text(row.iloc[8])
    applicant_name = record.get("name_of_developers", "")
    record["substation"] = clean_substation_value(substation_raw, delib_text, applicant_name)

    status = extract_34th_status_from_text(delib_text)
    record["status_of_application"] = status
    print(f"    App {app_id}: Status = {status}")

    voltage, text_substation = extract_34th_voltage_from_text(delib_text)
    if not voltage and substation_raw:
        loc_kv = re.search(r"(\d+)\s*kV", str(substation_raw), re.IGNORECASE)
        if loc_kv:
            voltage = int(loc_kv.group(1))
    if not voltage and delib_text:
        generic_kv = re.search(r"(\d+)\s*kV", delib_text, re.IGNORECASE)
        if generic_kv:
            voltage = int(generic_kv.group(1))

    if status == "Withdrawn":
        voltage = None
    record["voltage_level_kv"] = voltage
    if voltage:
        print(f"    App {app_id}: Voltage = {voltage} kV")

    if status == "Granted" and text_substation:
        record["substation"] = text_substation
        print(f"    App {app_id}: Substation overridden from text: {text_substation}")

    if status == "Granted" and app_quantum and granted_quantum is None:
        record["granted_quantum_mw"] = app_quantum

    if energy_type and app_quantum:
        if energy_type == "Solar":
            record["installed_breakup_solar_mw"] = app_quantum
        elif energy_type == "Wind":
            record["installed_breakup_wind_mw"] = app_quantum
        elif energy_type == "BESS":
            record["battery_injection_mw"] = app_quantum

    gna_date = extract_34th_gna_date_from_text(delib_text)
    if not gna_date and status == "Granted" and delib_text:
        date_pattern = r"(\d{2}[\.\-]\d{2}[\.\-]\d{4})"
        all_dates = re.findall(date_pattern, delib_text)
        if all_dates:
            parsed_dates = [(parse_date(date_text), date_text) for date_text in all_dates if parse_date(date_text)]
            if parsed_dates:
                parsed_dates.sort(key=lambda item: item[0], reverse=True)
                gna_date = parsed_dates[0][1]
    if gna_date:
        record["gna_operationalization_date"] = gna_date
        parsed_gna = parse_date(gna_date)
        if parsed_gna:
            today = datetime.now()
            record["gna_operationalization_yes_no"] = "Yes" if parsed_gna <= today else "No"
        print(f"    App {app_id}: GNA Date = {gna_date}")

    apply_cmets_element_codes_to_record(
        record,
        delib_text,
        context,
        annexure_lookup=get_annexure_elements_lookup(PDF_PATH_34TH, context),
    )

    return record


def process_34th_connectivity_tables(*, run_context: ExtractionRunContext | None = None):
    """Extract the 34th connectivity tables from pages 11-30."""
    context = _resolve_context(run_context)
    print("\n" + "=" * 60)
    print("34th CMETS - Processing CONNECTIVITY Tables (Pages 11-30)")
    print("=" * 60)

    tables = camelot.read_pdf(PDF_PATH_34TH, pages="11-30", flavor="lattice")
    print(f"  Found {len(tables)} tables on pages 11-30")

    eleven_col_tables = [table for table in tables if table.df.shape[1] == 11]
    print(f"  Filtered to {len(eleven_col_tables)} 11-column tables")

    records = []
    seen_app_ids = set()
    page_text_map = build_34th_page_text_map()
    full_connectivity_text = "\n".join(page_text_map.get(page_num, "") for page_num in range(11, 31))
    data_row = None
    delib_text = ""

    for table_idx, table in enumerate(eleven_col_tables):
        df = table.df
        print(f"\n  Table {table_idx + 1}: {df.shape[0]}r x {df.shape[1]}c, Page {table.page}")

        for idx in range(0, len(df)):
            row = df.iloc[idx]
            cell0 = str(row.iloc[0]).strip()
            cell1 = str(row.iloc[1]).strip()
            cell0_clean = re.sub(r"\s+", " ", cell0).strip()
            if re.search(r"Sl\.?\s*No\.?", cell0_clean, re.IGNORECASE) and not re.match(r"^\d+\.?$", cell0_clean):
                continue

            is_data_row = False
            app_id_found = None
            if re.match(r"^\d+\.?$", cell0):
                is_data_row = True
                id_match = re.search(r"(22\d{8})", cell1.replace(" ", ""))
                if id_match:
                    app_id_found = id_match.group(1)

            if not is_data_row:
                merged_match = re.match(r"^\s*\d+\.\s*(22\d{8})", cell1.replace(" ", "").replace("\n", ""))
                if merged_match:
                    is_data_row = True
                    app_id_found = merged_match.group(1)

            if not is_data_row:
                merged_match2 = re.match(r"^\s*\d+\.\s*(22\d{8})", cell0.replace(" ", "").replace("\n", ""))
                if merged_match2:
                    is_data_row = True
                    app_id_found = merged_match2.group(1)

            if not is_data_row:
                combined = (cell0 + " " + cell1).replace("\n", " ")
                parts_match = re.search(r"(\d+)\.\s*(22\d{8})", combined.replace(" ", ""))
                if parts_match:
                    has_data = any(str(row.iloc[col]).strip() for col in range(3, 8))
                    if has_data:
                        is_data_row = True
                        app_id_found = parts_match.group(2)

            if is_data_row and app_id_found:
                if data_row is not None:
                    prev_id = data_row.get("_app_id")
                    if prev_id and prev_id not in seen_app_ids:
                        rec = _build_connectivity_record(data_row, delib_text, run_context=context)
                        if rec:
                            records.append(rec)
                            seen_app_ids.add(prev_id)

                data_row = {"_row": row, "_app_id": app_id_found}
                delib_text = ""
            else:
                row_has_only_col0 = all(not str(row.iloc[col]).strip() for col in range(1, len(row)))
                collapsed_text = re.sub(r"\s+", " ", cell0)
                collapsed_match = re.search(r"\b\d+\.\s*(22\d{8})\b", collapsed_text)

                if row_has_only_col0 and collapsed_match:
                    collapsed_app_id = collapsed_match.group(1)
                    if data_row is not None:
                        prev_id = data_row.get("_app_id")
                        if prev_id and prev_id not in seen_app_ids:
                            rec = _build_connectivity_record(data_row, delib_text, run_context=context)
                            if rec:
                                records.append(rec)
                                seen_app_ids.add(prev_id)
                    data_row = None
                    delib_text = ""

                    if collapsed_app_id not in seen_app_ids:
                        rec = build_connectivity_record_from_page_text(
                            collapsed_app_id,
                            table.page,
                            page_text_map,
                            full_connectivity_text,
                            run_context=context,
                        )
                        if rec:
                            records.append(rec)
                            seen_app_ids.add(collapsed_app_id)
                            print(f"    App {collapsed_app_id}: recovered from collapsed row fallback")
                    continue

                row_text = " ".join([str(cell) for cell in row.values if str(cell).strip()])
                if row_text.strip():
                    delib_text += " " + row_text

    if data_row is not None:
        prev_id = data_row.get("_app_id")
        if prev_id and prev_id not in seen_app_ids:
            rec = _build_connectivity_record(data_row, delib_text, run_context=context)
            if rec:
                records.append(rec)
                seen_app_ids.add(prev_id)

    print(f"\n  CONNECTIVITY: Extracted {len(records)} records")
    return records


def extract_34th_all_data(*, run_context: ExtractionRunContext | None = None):
    """Run the full 34th meeting extraction flow."""
    context = _resolve_context(run_context)
    print("\n" + "=" * 60)
    print("34th CMETS NR Meeting - Data Extraction")
    print("=" * 60)

    if not os.path.exists(PDF_PATH_34TH):
        print(f"  ERROR: 34th CMETS PDF not found: {PDF_PATH_34TH}")
        return []

    transition_records = process_34th_transition_tables(run_context=context)
    connectivity_records = process_34th_connectivity_tables(run_context=context)
    all_records = transition_records + connectivity_records

    print(f"\n{'=' * 60}")
    print(f"34th CMETS TOTAL RECORDS: {len(all_records)}")
    print(f"  Transition: {len(transition_records)}")
    print(f"  Connectivity: {len(connectivity_records)}")
    print(f"{'=' * 60}")

    return all_records


__all__ = [
    "build_34th_page_text_map",
    "build_connectivity_record_from_page_text",
    "extract_34th_all_data",
    "extract_34th_row_segment_from_full_text",
    "extract_34th_row_segment_from_page_text",
    "process_34th_connectivity_tables",
    "process_34th_transition_tables",
    "split_34th_applicant_and_location",
]
