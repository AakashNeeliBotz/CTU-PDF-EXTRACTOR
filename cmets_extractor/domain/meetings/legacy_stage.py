from __future__ import annotations

import re
from datetime import datetime

from cmets_extractor.adapters.pdf import read_camelot_lattice_tables_chunked
from cmets_extractor.config import (
    CMETS_14TH_MEETING_DATE,
    CMETS_14TH_MEETING_NUMBER,
    CMETS_15TH_MEETING_DATE,
    CMETS_15TH_MEETING_NUMBER,
    CMETS_16TH_MEETING_DATE,
    CMETS_16TH_MEETING_NUMBER,
    CMETS_17TH_MEETING_DATE,
    CMETS_17TH_MEETING_NUMBER,
    CMETS_18TH_MEETING_DATE,
    CMETS_18TH_MEETING_NUMBER,
    PDF_PATH_14TH,
    PDF_PATH_15TH,
    PDF_PATH_16TH,
    PDF_PATH_17TH,
    PDF_PATH_18TH,
)
from cmets_extractor.domain.common.dates import get_latest_date, normalize_output_date_text, parse_date
from cmets_extractor.domain.common.ids import remove_leading_zeros
from cmets_extractor.domain.common.numbers import parse_numeric_value
from cmets_extractor.domain.common.text import clean_text
from cmets_extractor.domain.data_capture_common import (
    clean_substation_value,
    extract_34th_voltage_from_text,
    merge_capacity_breakup,
    parse_34th_nature_and_type,
    parse_project_location,
    parse_type_capacity,
)


def _header_text(table_df, rows=2):
    parts = []
    for row_idx in range(min(rows, len(table_df))):
        parts.extend(clean_text(value) or "" for value in table_df.iloc[row_idx].tolist())
    return " | ".join(part for part in parts if part).lower()


def _is_numeric_row(value):
    text = clean_text(value)
    return bool(text and re.match(r"^\d+\.?$", text))


def _parse_mw_and_date(value):
    text = clean_text(value)
    if not text:
        return None, None

    mw = None
    date_text = None

    pair_match = re.search(
        r"([0-9]+(?:\.[0-9]+)?)\s*/\s*([0-3]?\d[\./-][01]?\d[\./-]\d{2,4})",
        text,
    )
    if pair_match:
        mw = parse_numeric_value(pair_match.group(1))
        date_text = normalize_output_date_text(pair_match.group(2))
        return mw, date_text

    reverse_pair_match = re.search(
        r"([0-3]?\d[\./-][01]?\d[\./-]\d{2,4})\s*/\s*([0-9]+(?:\.[0-9]+)?)",
        text,
    )
    if reverse_pair_match:
        date_text = normalize_output_date_text(reverse_pair_match.group(1))
        mw = parse_numeric_value(reverse_pair_match.group(2))
        return mw, date_text

    dates = re.findall(r"[0-3]?\d[\./-][01]?\d[\./-]\d{2,4}", text)
    if dates:
        date_text = normalize_output_date_text(dates[-1])

    date_spans = [match.span() for match in re.finditer(r"[0-3]?\d[\./-][01]?\d[\./-]\d{2,4}", text)]
    number_matches = []
    for match in re.finditer(r"[0-9]+(?:\.[0-9]+)?", text):
        if any(start <= match.start() < end for start, end in date_spans):
            continue
        number_matches.append(match.group(0))
    if number_matches:
        mw = parse_numeric_value(number_matches[0])

    return mw, date_text


def _extract_long_application_id(value, *, strategy="last"):
    text = clean_text(value)
    if not text:
        return None

    matches = re.findall(r"\d{7,}", text)
    if not matches:
        return None

    selected = matches[0] if strategy == "first" else matches[-1]
    return remove_leading_zeros(selected)


def _legacy_type_from_text(text):
    lower = (clean_text(text) or "").lower()
    if "hybrid" in lower:
        return "Hybrid"
    if "storage" in lower or "bess" in lower or "ess" in lower:
        return "BESS"
    if "wind" in lower:
        return "Wind"
    if "hydro" in lower:
        return "Hydro"
    if "solar" in lower:
        return "Solar"
    return None


def _apply_capacity_from_texts(record, quantum, *texts):
    parsed = {}
    for text in texts:
        parsed = merge_capacity_breakup(parsed, parse_type_capacity(text))

    energy_type = parsed.get("type") or next(
        (candidate for candidate in (_legacy_type_from_text(text) for text in texts) if candidate),
        None,
    )
    if energy_type:
        record["type"] = energy_type

    if parsed.get("solar") is not None:
        record["installed_breakup_solar_mw"] = parsed.get("solar")
    if parsed.get("wind") is not None:
        record["installed_breakup_wind_mw"] = parsed.get("wind")
    if parsed.get("hydro") is not None:
        record["installed_breakup_hydro_mw"] = parsed.get("hydro")
    if parsed.get("bess_injection") is not None:
        record["battery_injection_mw"] = parsed.get("bess_injection")

    if quantum is None or energy_type is None:
        return

    if energy_type == "Solar" and record.get("installed_breakup_solar_mw") is None:
        record["installed_breakup_solar_mw"] = quantum
    elif energy_type == "Wind" and record.get("installed_breakup_wind_mw") is None:
        record["installed_breakup_wind_mw"] = quantum
    elif energy_type == "Hydro" and record.get("installed_breakup_hydro_mw") is None:
        record["installed_breakup_hydro_mw"] = quantum
    elif energy_type == "BESS" and record.get("battery_injection_mw") is None:
        record["battery_injection_mw"] = quantum
    elif energy_type == "Hybrid" and (
        record.get("installed_breakup_solar_mw") is None
        and record.get("installed_breakup_wind_mw") is None
    ):
        record["installed_breakup_hybrid_mw"] = quantum


def _apply_common_record_fields(
    record,
    *,
    applicant_name,
    location_text,
    nature_raw,
    quantum,
    applied_start_date,
    substation_raw,
    context_text,
    meeting_number,
    meeting_date,
    status,
    treat_as_lta,
):
    if treat_as_lta:
        record["cmets_lta_approved"] = meeting_number
        record["cmets_lta_meeting_date"] = meeting_date
    else:
        record["cmets_gna_approved"] = meeting_number
        record["cmets_gna_meeting_date"] = meeting_date

    record["name_of_developers"] = applicant_name
    record["application_quantum_mw"] = quantum
    record["applied_start_date"] = applied_start_date
    record["status_of_application"] = status

    state, region = parse_project_location(location_text, substation_raw)
    record["state"] = state
    record["region"] = region

    nature, energy_type = parse_34th_nature_and_type(nature_raw)
    if nature:
        record["nature_of_applicant"] = nature
    if energy_type and "type" not in record:
        record["type"] = energy_type
    _apply_capacity_from_texts(record, quantum, nature_raw, context_text)

    substation = clean_substation_value(substation_raw, context_text, applicant_name)
    if substation:
        record["substation"] = substation

    voltage, text_substation = extract_34th_voltage_from_text(context_text)
    if text_substation and status == "Granted":
        record["substation"] = text_substation
    if status == "Withdrawn":
        voltage = None
    if voltage is not None:
        record["voltage_level_kv"] = voltage

    if status == "Granted" and quantum is not None:
        record["granted_quantum_mw"] = quantum
        if applied_start_date:
            record["gna_operationalization_date"] = applied_start_date
            parsed_gna = parse_date(applied_start_date)
            if parsed_gna:
                record["gna_operationalization_yes_no"] = (
                    "Yes" if parsed_gna <= datetime.now() else "No"
                )


def _build_stage_one_record(row, meeting_number, meeting_date, status):
    record = {}
    app_id = _extract_long_application_id(row.iloc[1], strategy="last")
    if app_id:
        record["lta_application_id"] = app_id

    applicant_name = clean_text(row.iloc[2])
    location_text = clean_text(row.iloc[3])
    application_date = normalize_output_date_text(clean_text(row.iloc[4]))
    quantum, applied_start_date = _parse_mw_and_date(row.iloc[5])
    nature_raw = clean_text(row.iloc[6])
    substation_raw = clean_text(row.iloc[7])
    context_text = clean_text(row.iloc[8])

    record["application_date"] = application_date
    _apply_common_record_fields(
        record,
        applicant_name=applicant_name,
        location_text=location_text,
        nature_raw=nature_raw,
        quantum=quantum,
        applied_start_date=applied_start_date,
        substation_raw=substation_raw,
        context_text=context_text,
        meeting_number=meeting_number,
        meeting_date=meeting_date,
        status=status,
        treat_as_lta=True,
    )
    return record


def _build_stage_two_record(row, meeting_number, meeting_date, status):
    record = {}
    app_id = _extract_long_application_id(row.iloc[1], strategy="last")
    if app_id:
        record["gna_st_ii_application_id"] = app_id

    applicant_name = clean_text(row.iloc[2])
    location_text = clean_text(row.iloc[3])
    application_date = normalize_output_date_text(clean_text(row.iloc[4]))
    stage_one_text = clean_text(row.iloc[5])
    stage_one_id = _extract_long_application_id(stage_one_text, strategy="first")
    if stage_one_id:
        record["lta_application_id"] = stage_one_id

    nature_raw = clean_text(row.iloc[6])
    generation_schedule = clean_text(row.iloc[7])
    quantum, applied_start_date = _parse_mw_and_date(row.iloc[8])
    if not applied_start_date:
        applied_start_date = get_latest_date(generation_schedule)
    substation_raw = clean_text(row.iloc[10])
    context_text = clean_text(row.iloc[11])

    record["application_date"] = application_date
    _apply_common_record_fields(
        record,
        applicant_name=applicant_name,
        location_text=location_text,
        nature_raw=nature_raw,
        quantum=quantum,
        applied_start_date=applied_start_date,
        substation_raw=substation_raw,
        context_text=context_text,
        meeting_number=meeting_number,
        meeting_date=meeting_date,
        status=status,
        treat_as_lta=False,
    )
    return record


def _build_lta_record(row, meeting_number, meeting_date, status):
    record = {}
    lta_id = _extract_long_application_id(row.iloc[1], strategy="last")
    if lta_id:
        record["lta_application_id"] = lta_id

    applicant_name = clean_text(row.iloc[2])
    application_date = normalize_output_date_text(clean_text(row.iloc[3]))
    injection_point = clean_text(row.iloc[4])
    linked_connectivity_id = _extract_long_application_id(row.iloc[5], strategy="first")
    if linked_connectivity_id:
        record["gna_st_ii_application_id"] = linked_connectivity_id
    quantum = parse_numeric_value(row.iloc[7])
    applied_start_date = get_latest_date(clean_text(row.iloc[8])) or normalize_output_date_text(
        clean_text(row.iloc[8])
    )

    record["application_date"] = application_date
    _apply_common_record_fields(
        record,
        applicant_name=applicant_name,
        location_text=injection_point,
        nature_raw=None,
        quantum=quantum,
        applied_start_date=applied_start_date,
        substation_raw=injection_point,
        context_text=clean_text(row.iloc[4]),
        meeting_number=meeting_number,
        meeting_date=meeting_date,
        status=status,
        treat_as_lta=True,
    )
    return record


def _build_mixed_category_record(row, meeting_number, meeting_date):
    category = clean_text(row.iloc[2] if len(row) > 2 else None) or ""
    category_low = category.lower()
    if "st-ii" in category_low:
        record = {}
        app_id = _extract_long_application_id(row.iloc[1], strategy="last")
        if app_id:
            record["gna_st_ii_application_id"] = app_id
        record["application_date"] = normalize_output_date_text(clean_text(row.iloc[5]))
        quantum = parse_numeric_value(row.iloc[7])
        applied_start_date = normalize_output_date_text(clean_text(row.iloc[6]))
        _apply_common_record_fields(
            record,
            applicant_name=clean_text(row.iloc[3]),
            location_text=clean_text(row.iloc[4]),
            nature_raw=clean_text(row.iloc[8]),
            quantum=quantum,
            applied_start_date=applied_start_date,
            substation_raw=clean_text(row.iloc[9]),
            context_text=clean_text(row.iloc[9]),
            meeting_number=meeting_number,
            meeting_date=meeting_date,
            status="Applied",
            treat_as_lta=False,
        )
        return record

    if "st-i" in category_low:
        record = {}
        app_id = _extract_long_application_id(row.iloc[1], strategy="last")
        if app_id:
            record["lta_application_id"] = app_id
        record["application_date"] = normalize_output_date_text(clean_text(row.iloc[5]))
        quantum = parse_numeric_value(row.iloc[7])
        applied_start_date = normalize_output_date_text(clean_text(row.iloc[6]))
        _apply_common_record_fields(
            record,
            applicant_name=clean_text(row.iloc[3]),
            location_text=clean_text(row.iloc[4]),
            nature_raw=clean_text(row.iloc[8]),
            quantum=quantum,
            applied_start_date=applied_start_date,
            substation_raw=clean_text(row.iloc[9]),
            context_text=clean_text(row.iloc[9]),
            meeting_number=meeting_number,
            meeting_date=meeting_date,
            status="Applied",
            treat_as_lta=True,
        )
        return record

    return None


def extract_stage_family_meeting_data(pdf_path, meeting_number, meeting_date, label):
    print("\n" + "=" * 60)
    print(f"{label} CMETS NR Meeting - Legacy Stage Data Extraction")
    print("=" * 60)

    status = "Granted" if meeting_number < 18 else "Applied"
    end_page = 30 if meeting_number < 18 else 12
    tables = read_camelot_lattice_tables_chunked(
        pdf_path,
        chunk_size=10,
        start_page=1,
        end_page=end_page,
    )

    records = []
    for table in tables:
        df = table.df
        if len(df) == 0:
            continue
        header = _header_text(df)

        if "application category" in header and "location requested for grant of stage-i connectivity" in header:
            for idx in range(1, len(df)):
                row = df.iloc[idx]
                if not _is_numeric_row(row.iloc[0]):
                    continue
                record = _build_mixed_category_record(row, meeting_number, meeting_date)
                if record:
                    records.append(record)
            continue

        if "location requested for grant of stage-i connectivity" in header:
            for idx in range(1, len(df)):
                row = df.iloc[idx]
                if not _is_numeric_row(row.iloc[0]):
                    continue
                records.append(_build_stage_one_record(row, meeting_number, meeting_date, status))
            continue

        if "stage-ii connectivity sought" in header and "application/ quantum of stage-i" in header:
            for idx in range(1, len(df)):
                row = df.iloc[idx]
                if not _is_numeric_row(row.iloc[0]):
                    continue
                records.append(_build_stage_two_record(row, meeting_number, meeting_date, status))
            continue

        if "quantum of lta" in header and "injection point" in header:
            for idx in range(1, len(df)):
                row = df.iloc[idx]
                if not _is_numeric_row(row.iloc[0]):
                    continue
                records.append(_build_lta_record(row, meeting_number, meeting_date, status))

    print(f"  Legacy stage-family records: {len(records)}")
    return records

def extract_14th_all_data():
    return extract_stage_family_meeting_data(
        PDF_PATH_14TH,
        CMETS_14TH_MEETING_NUMBER,
        CMETS_14TH_MEETING_DATE,
        "14th",
    )


def extract_15th_all_data():
    return extract_stage_family_meeting_data(
        PDF_PATH_15TH,
        CMETS_15TH_MEETING_NUMBER,
        CMETS_15TH_MEETING_DATE,
        "15th",
    )


def extract_16th_all_data():
    return extract_stage_family_meeting_data(
        PDF_PATH_16TH,
        CMETS_16TH_MEETING_NUMBER,
        CMETS_16TH_MEETING_DATE,
        "16th",
    )


def extract_17th_all_data():
    return extract_stage_family_meeting_data(
        PDF_PATH_17TH,
        CMETS_17TH_MEETING_NUMBER,
        CMETS_17TH_MEETING_DATE,
        "17th",
    )


def extract_18th_all_data():
    return extract_stage_family_meeting_data(
        PDF_PATH_18TH,
        CMETS_18TH_MEETING_NUMBER,
        CMETS_18TH_MEETING_DATE,
        "18th",
    )


__all__ = [
    "extract_14th_all_data",
    "extract_15th_all_data",
    "extract_16th_all_data",
    "extract_17th_all_data",
    "extract_stage_family_meeting_data",
    "extract_18th_all_data",
]
