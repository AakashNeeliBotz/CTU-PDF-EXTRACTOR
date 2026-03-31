from __future__ import annotations

import re
from datetime import datetime

from cmets_extractor.adapters.pdf import read_camelot_lattice_tables_chunked
from cmets_extractor.config import (
    CMETS_22ND_MEETING_DATE,
    CMETS_22ND_MEETING_NUMBER,
    CMETS_23RD_MEETING_DATE,
    CMETS_23RD_MEETING_NUMBER,
    CMETS_24TH_MEETING_DATE,
    CMETS_24TH_MEETING_NUMBER,
    PDF_PATH_22ND,
    PDF_PATH_23RD,
    PDF_PATH_24TH,
)
from cmets_extractor.domain.common.dates import get_latest_date, normalize_output_date_text, parse_date
from cmets_extractor.domain.common.ids import remove_leading_zeros
from cmets_extractor.domain.common.numbers import parse_numeric_value
from cmets_extractor.domain.common.text import clean_text
from cmets_extractor.domain.data_capture_common import (
    clean_substation_value,
    extract_34th_voltage_from_text,
    get_region_from_substation,
    get_state_from_substation,
    parse_conn_quantum,
    parse_project_location,
)


def _header_text(table_df, rows=2):
    parts = []
    for row_idx in range(min(rows, len(table_df))):
        parts.extend(clean_text(value) or "" for value in table_df.iloc[row_idx].tolist())
    return " | ".join(part for part in parts if part).lower()


def _is_numeric_row(value):
    text = clean_text(value)
    return bool(text and re.match(r"^\d+\.?$", text))


def _row_text(row):
    values = row.tolist() if hasattr(row, "tolist") else list(row)
    return " ".join(clean_text(value) or "" for value in values).strip()


def _cell(row, idx):
    if hasattr(row, "iloc"):
        return row.iloc[idx]
    return row[idx]


def _normalize_date(value):
    return get_latest_date(value) or normalize_output_date_text(clean_text(value))


def _extract_ids_and_quantum(details_text):
    gna_id, gna_quantum, lta_id, lta_quantum = parse_conn_quantum(details_text)
    text = clean_text(details_text) or ""
    stage_ids = []

    stage_section = re.search(
        r"(?:st-ii|stage-ii)\s*:\s*(.*?)(?:lta\s*:|$)",
        text,
        re.IGNORECASE,
    )
    if stage_section:
        stage_ids = re.findall(r"\d{7,}", stage_section.group(1))
        if stage_ids:
            gna_id = remove_leading_zeros(stage_ids[0])

    lta_section = re.search(r"lta\s*:\s*(.*)", text, re.IGNORECASE)
    if lta_section:
        lta_ids = re.findall(r"\d{7,}", lta_section.group(1))
        if lta_ids:
            lta_id = remove_leading_zeros(lta_ids[-1])
    elif stage_section:
        tail_ids = re.findall(r"\d{7,}", text[stage_section.end():])
        tail_ids = [remove_leading_zeros(candidate) for candidate in tail_ids]
        tail_ids = [candidate for candidate in tail_ids if candidate not in {remove_leading_zeros(x) for x in stage_ids}]
        if tail_ids:
            lta_id = tail_ids[-1]

    for candidate in re.findall(r"\d{7,}", text):
        candidate = remove_leading_zeros(candidate)
        if candidate.startswith("04"):
            if not lta_id:
                lta_id = candidate
        elif not gna_id:
            gna_id = candidate
        elif not lta_id and candidate != gna_id:
            lta_id = candidate

    if gna_id:
        gna_id = remove_leading_zeros(gna_id)
    if lta_id:
        lta_id = remove_leading_zeros(lta_id)

    if lta_quantum is None or gna_quantum is None:
        mw_matches = re.findall(r"(\d+(?:\.\d+)?)\s*MW", clean_text(details_text) or "", re.IGNORECASE)
        if mw_matches:
            fallback_quantum = parse_numeric_value(mw_matches[-1])
            if lta_id and lta_quantum is None:
                lta_quantum = fallback_quantum
            elif gna_id and gna_quantum is None:
                gna_quantum = fallback_quantum

    return gna_id, gna_quantum, lta_id, lta_quantum


def _extract_any_voltage_and_substation(text, fallback_substation=None):
    voltage, text_substation = extract_34th_voltage_from_text(text)
    substation = text_substation or clean_substation_value(fallback_substation)

    if voltage is None:
        slash_match = re.findall(r"(\d+(?:/\d+){0,3})\s*kV", clean_text(text) or "", re.IGNORECASE)
        if slash_match:
            kv_parts = [int(part) for part in slash_match[-1].split("/") if int(part) >= 132]
            if kv_parts:
                voltage = kv_parts[-1]

    if substation is None:
        station_match = re.search(
            r"kV\s+([A-Za-z0-9][A-Za-z0-9\-\(\)\s/]*?(?:\bPS\b|\bS\s*/\s*S\b|\bS/s\b|\bSubstation\b))",
            clean_text(text) or "",
            re.IGNORECASE,
        )
        if station_match:
            substation = clean_substation_value(station_match.group(1))

    return voltage, substation


def _set_state_and_region(record, location_text=None, substation=None):
    if clean_text(location_text):
        state, region = parse_project_location(location_text, substation)
        if state:
            record["state"] = state
        if region:
            record["region"] = region
        return

    substation_text = clean_text(substation)
    if substation_text:
        state = get_state_from_substation(substation_text)
        region = get_region_from_substation(substation_text)
        if state:
            record["state"] = state
        if region:
            record["region"] = region
            return

    record["region"] = "NR"


def _set_gna_effective_date(record, gna_date):
    gna_date = _normalize_date(gna_date)
    if not gna_date:
        return

    record["gna_operationalization_date"] = gna_date
    parsed = parse_date(gna_date)
    if parsed:
        record["gna_operationalization_yes_no"] = "Yes" if parsed <= datetime.now() else "No"


def _build_transition_grant_record(row, delib_text, *, meeting_number, meeting_date, layout):
    record = {
        "cmets_gna_approved": meeting_number,
        "cmets_gna_meeting_date": meeting_date,
        "status_of_application": "Granted",
        "name_of_developers": clean_text(_cell(row, layout["applicant_idx"])),
    }

    details_text = clean_text(_cell(row, layout["details_idx"]))
    gna_id, gna_quantum, lta_id, lta_quantum = _extract_ids_and_quantum(details_text)
    if gna_id:
        record["gna_st_ii_application_id"] = gna_id
    if lta_id:
        record["lta_application_id"] = lta_id

    substation_raw = clean_text(_cell(row, layout["pooling_idx"]))
    combined_text = " ".join(
        part
        for part in [
            details_text,
            clean_text(_cell(row, layout["bay_idx"])) if layout.get("bay_idx") is not None else None,
            delib_text,
        ]
        if part
    )
    voltage, parsed_substation = _extract_any_voltage_and_substation(combined_text, substation_raw)
    substation = parsed_substation or clean_substation_value(substation_raw)
    if substation:
        record["substation"] = substation
    if voltage is not None:
        record["voltage_level_kv"] = voltage
    _set_state_and_region(record, None, substation)

    quantum = None
    if layout.get("quantum_idx") is not None:
        quantum = parse_numeric_value(_cell(row, layout["quantum_idx"]))
    if quantum is None:
        quantum = lta_quantum if lta_quantum is not None else gna_quantum
    record["application_quantum_mw"] = quantum
    if quantum is not None:
        record["granted_quantum_mw"] = quantum

    applied_start_date = None
    if layout.get("applied_start_idx") is not None:
        applied_start_date = _normalize_date(_cell(row, layout["applied_start_idx"]))
    record["applied_start_date"] = applied_start_date

    gna_date = None
    if layout.get("expected_idx") is not None:
        gna_date = _normalize_date(_cell(row, layout["expected_idx"]))
    if not gna_date and meeting_number == CMETS_22ND_MEETING_NUMBER and layout.get("expected_idx") is None:
        gna_date = "01.10.2023"
    if not gna_date:
        gna_date = _normalize_date(combined_text)
    _set_gna_effective_date(record, gna_date)

    return record


def _build_effective_target_record(row, *, meeting_number, meeting_date):
    record = {
        "cmets_gna_approved": meeting_number,
        "cmets_gna_meeting_date": meeting_date,
        "status_of_application": "Granted",
        "name_of_developers": clean_text(_cell(row, 1)),
    }

    details_text = clean_text(_cell(row, 2))
    gna_id, gna_quantum, lta_id, _ = _extract_ids_and_quantum(details_text)
    if gna_id:
        record["gna_st_ii_application_id"] = gna_id
    if lta_id:
        record["lta_application_id"] = lta_id

    quantum = parse_numeric_value(_cell(row, 3)) or gna_quantum
    record["application_quantum_mw"] = quantum
    if quantum is not None:
        record["granted_quantum_mw"] = quantum

    record["region"] = "NR"
    _set_gna_effective_date(record, "01.10.2023")
    return record


def _build_simple_grant_record(row, delib_text, *, meeting_number, meeting_date):
    record = {
        "cmets_gna_approved": meeting_number,
        "cmets_gna_meeting_date": meeting_date,
        "status_of_application": "Granted",
        "name_of_developers": clean_text(_cell(row, 1)),
    }

    quantum = parse_numeric_value(_cell(row, 2))
    record["application_quantum_mw"] = quantum
    if quantum is not None:
        record["granted_quantum_mw"] = quantum

    combined_text = " ".join(
        part for part in [clean_text(_cell(row, 4)), delib_text] if part
    )
    voltage, substation = _extract_any_voltage_and_substation(combined_text)
    if substation:
        record["substation"] = substation
    if voltage is not None:
        record["voltage_level_kv"] = voltage
    _set_state_and_region(record, None, substation)

    record["applied_start_date"] = _normalize_date(_cell(row, 5))
    _set_gna_effective_date(record, _cell(row, 6))
    return record


def _build_withdrawn_transition_record(row, delib_text, *, meeting_number, meeting_date, layout):
    record = {
        "cmets_gna_approved": meeting_number,
        "cmets_gna_meeting_date": meeting_date,
        "status_of_application": "Withdrawn",
        "name_of_developers": clean_text(_cell(row, layout["applicant_idx"])),
    }

    detail_parts = [clean_text(_cell(row, idx)) for idx in layout["detail_indices"]]
    details_text = " ".join(part for part in detail_parts if part)
    gna_id, gna_quantum, lta_id, lta_quantum = _extract_ids_and_quantum(details_text)
    if gna_id:
        record["gna_st_ii_application_id"] = gna_id
    if lta_id:
        record["lta_application_id"] = lta_id

    quantum = lta_quantum if lta_quantum is not None else gna_quantum
    if quantum is not None:
        record["application_quantum_mw"] = quantum

    substation = None
    if layout.get("pooling_idx") is not None:
        substation = clean_substation_value(_cell(row, layout["pooling_idx"]))
    if not substation:
        _, substation = _extract_any_voltage_and_substation(" ".join([details_text, delib_text]))
    if substation:
        record["substation"] = substation
    _set_state_and_region(record, None, substation)
    return record


def _normalize_transition_row(row):
    values = list(row.tolist() if hasattr(row, "tolist") else row)
    if not values:
        return values

    first = clean_text(values[0])
    second = clean_text(values[1]) if len(values) > 1 else None

    first_match = re.match(r"^(\d+)\s+(.+)$", first or "")
    if first_match and (not second):
        values[0] = first_match.group(1)
        if len(values) > 1:
            values[1] = first_match.group(2)
        return values

    second_match = re.match(r"^(\d+)\s+(.+)$", second or "")
    if second_match and not first:
        values[0] = second_match.group(1)
        values[1] = second_match.group(2)

    return values


def _is_new_transition_row(row, layout):
    serial_text = clean_text(_cell(row, 0))
    applicant_text = clean_text(_cell(row, layout["applicant_idx"])) if layout.get("applicant_idx") is not None else None
    return bool(
        serial_text
        and re.match(r"^\d+\.?$", serial_text)
        and applicant_text
        and re.search(r"[A-Za-z]", applicant_text)
    )


def _process_row_stream(tables, builder, layout):
    records = []
    data_row = None
    delib_text = ""

    for table in tables:
        df = table.df
        for idx in range(1, len(df)):
            row = _normalize_transition_row(df.iloc[idx])
            if _is_new_transition_row(row, layout):
                if data_row is not None:
                    record = builder(data_row, delib_text, layout=layout)
                    if record:
                        records.append(record)
                data_row = row
                delib_text = ""
                continue

            row_text = _row_text(row)
            if row_text:
                delib_text = (delib_text + " " + row_text).strip()

    if data_row is not None:
        record = builder(data_row, delib_text, layout=layout)
        if record:
            records.append(record)

    return records


def _extract_22nd_transition_records(pdf_path, meeting_number, meeting_date):
    tables = read_camelot_lattice_tables_chunked(
        pdf_path,
        chunk_size=8,
        start_page=18,
        end_page=31,
    )

    withdrawn_legacy_tables = []
    close_tables = []
    effective_target_tables = []
    seven_col_tables = []
    eight_col_tables = []

    for table in tables:
        df = table.df
        if len(df) == 0:
            continue
        header = _header_text(df, rows=2)
        if "mtoa" in header:
            continue
        if "details of application under process" in header and "gna transition" in header:
            close_tables.append(table)
            continue
        if "lta effective on target" in header:
            effective_target_tables.append(table)
            continue
        if "connectivity (st-ii for re)" in header and "gna transition" in header:
            withdrawn_legacy_tables.append(table)
            continue
        if "st-ii connectivity & lta details" not in header:
            continue
        if "expected start date of conn. under gna" in header:
            eight_col_tables.append(table)
        elif "lta / connectivity start date as per intimations" in header:
            seven_col_tables.append(table)

    records = []

    records.extend(
        _process_row_stream(
            withdrawn_legacy_tables,
            lambda row, delib_text, layout: _build_withdrawn_transition_record(
                row,
                delib_text,
                meeting_number=meeting_number,
                meeting_date=meeting_date,
                layout=layout,
            ),
            {
                "applicant_idx": 1,
                "detail_indices": (2, 3),
                "pooling_idx": 4,
            },
        )
    )

    for table in close_tables:
        df = table.df
        for idx in range(1, len(df)):
            row = df.iloc[idx]
            if not _is_numeric_row(row.iloc[0]):
                continue
            records.append(
                _build_withdrawn_transition_record(
                    row,
                    "",
                    meeting_number=meeting_number,
                    meeting_date=meeting_date,
                    layout={
                        "applicant_idx": 1,
                        "detail_indices": (2,),
                    },
                )
            )

    for table in effective_target_tables:
        df = table.df
        for idx in range(1, len(df)):
            row = df.iloc[idx]
            if not _is_numeric_row(row.iloc[0]):
                continue
            records.append(
                _build_effective_target_record(
                    row,
                    meeting_number=meeting_number,
                    meeting_date=meeting_date,
                )
            )

    records.extend(
        _process_row_stream(
            seven_col_tables,
            lambda row, delib_text, layout: _build_transition_grant_record(
                row,
                delib_text,
                meeting_number=meeting_number,
                meeting_date=meeting_date,
                layout=layout,
            ),
            {
                "applicant_idx": 1,
                "details_idx": 2,
                "pooling_idx": 3,
                "applied_start_idx": 4,
                "bay_idx": 5,
                "expected_idx": None,
            },
        )
    )

    records.extend(
        _process_row_stream(
            eight_col_tables,
            lambda row, delib_text, layout: _build_transition_grant_record(
                row,
                delib_text,
                meeting_number=meeting_number,
                meeting_date=meeting_date,
                layout=layout,
            ),
            {
                "applicant_idx": 1,
                "details_idx": 2,
                "pooling_idx": 3,
                "applied_start_idx": 4,
                "bay_idx": 5,
                "expected_idx": 6,
            },
        )
    )

    return records


def _extract_23rd_transition_records(pdf_path, meeting_number, meeting_date):
    tables = read_camelot_lattice_tables_chunked(
        pdf_path,
        chunk_size=5,
        start_page=28,
        end_page=32,
    )
    relevant_tables = []
    for table in tables:
        header = _header_text(table.df, rows=2)
        if table.df.shape[1] == 9 and "applicant" in header and "expected" in header and "gna" in header:
            relevant_tables.append(table)

    return _process_row_stream(
        relevant_tables,
        lambda row, delib_text, layout: _build_transition_grant_record(
            row,
            delib_text,
            meeting_number=meeting_number,
            meeting_date=meeting_date,
            layout=layout,
        ),
        {
            "applicant_idx": 1,
            "details_idx": 2,
            "pooling_idx": 3,
            "quantum_idx": 4,
            "bay_idx": 5,
            "applied_start_idx": 6,
            "expected_idx": 7,
        },
    )


def _extract_24th_transition_records(pdf_path, meeting_number, meeting_date):
    tables = read_camelot_lattice_tables_chunked(
        pdf_path,
        chunk_size=1,
        start_page=4,
        end_page=4,
    )
    records = []
    for table in tables:
        df = table.df
        header = _header_text(df, rows=2)
        if "connectivity effective" not in header or "actual start date of gna" not in header:
            continue
        for idx in range(1, len(df)):
            row = df.iloc[idx]
            if not _is_numeric_row(row.iloc[0]):
                continue
            records.append(
                _build_simple_grant_record(
                    row,
                    "",
                    meeting_number=meeting_number,
                    meeting_date=meeting_date,
                )
            )
    return records


def extract_transition_family_meeting_data(pdf_path, meeting_number, meeting_date, label):
    print("\n" + "=" * 60)
    print(f"{label} CMETS NR Meeting - Legacy Transition Data Extraction")
    print("=" * 60)

    if meeting_number == CMETS_22ND_MEETING_NUMBER:
        records = _extract_22nd_transition_records(pdf_path, meeting_number, meeting_date)
    elif meeting_number == CMETS_23RD_MEETING_NUMBER:
        records = _extract_23rd_transition_records(pdf_path, meeting_number, meeting_date)
    elif meeting_number == CMETS_24TH_MEETING_NUMBER:
        records = _extract_24th_transition_records(pdf_path, meeting_number, meeting_date)
    else:
        records = []

    print(f"  Legacy transition-family records: {len(records)}")
    return records


def extract_22nd_all_data():
    return extract_transition_family_meeting_data(
        PDF_PATH_22ND,
        CMETS_22ND_MEETING_NUMBER,
        CMETS_22ND_MEETING_DATE,
        "22nd",
    )


def extract_23rd_all_data():
    return extract_transition_family_meeting_data(
        PDF_PATH_23RD,
        CMETS_23RD_MEETING_NUMBER,
        CMETS_23RD_MEETING_DATE,
        "23rd",
    )


def extract_24th_all_data():
    return extract_transition_family_meeting_data(
        PDF_PATH_24TH,
        CMETS_24TH_MEETING_NUMBER,
        CMETS_24TH_MEETING_DATE,
        "24th",
    )


__all__ = [
    "extract_22nd_all_data",
    "extract_23rd_all_data",
    "extract_24th_all_data",
    "extract_transition_family_meeting_data",
]
