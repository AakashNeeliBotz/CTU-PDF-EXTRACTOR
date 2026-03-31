from __future__ import annotations

import os
import re
from datetime import datetime

from cmets_extractor.adapters.pdf import read_camelot_lattice_tables_chunked
from cmets_extractor.config import (
    CMETS_19TH_MEETING_DATE,
    CMETS_19TH_MEETING_NUMBER,
    CMETS_35TH_MEETING_DATE,
    CMETS_35TH_MEETING_NUMBER,
    CMETS_36TH_MEETING_DATE,
    CMETS_36TH_MEETING_NUMBER,
    CMETS_37TH_MEETING_DATE,
    CMETS_37TH_MEETING_NUMBER,
    CMETS_38TH_MEETING_DATE,
    CMETS_38TH_MEETING_NUMBER,
    CMETS_39TH_MEETING_DATE,
    CMETS_39TH_MEETING_NUMBER,
    CMETS_40TH_MEETING_DATE,
    CMETS_40TH_MEETING_NUMBER,
    CMETS_41ST_MEETING_DATE,
    CMETS_41ST_MEETING_NUMBER,
    CMETS_20TH_MEETING_DATE,
    CMETS_20TH_MEETING_NUMBER,
    CMETS_21ST_MEETING_DATE,
    CMETS_21ST_MEETING_NUMBER,
    CMETS_25TH_MEETING_DATE,
    CMETS_25TH_MEETING_NUMBER,
    CMETS_26TH_MEETING_DATE,
    CMETS_26TH_MEETING_NUMBER,
    CMETS_27TH_MEETING_DATE,
    CMETS_27TH_MEETING_NUMBER,
    CMETS_28TH_MEETING_DATE,
    CMETS_28TH_MEETING_NUMBER,
    CMETS_29TH_MEETING_DATE,
    CMETS_29TH_MEETING_NUMBER,
    CMETS_30TH_MEETING_DATE,
    CMETS_30TH_MEETING_NUMBER,
    CMETS_31ST_MEETING_DATE,
    CMETS_31ST_MEETING_NUMBER,
    CMETS_32ND_MEETING_DATE,
    CMETS_32ND_MEETING_NUMBER,
    CMETS_33RD_MEETING_DATE,
    CMETS_33RD_MEETING_NUMBER,
    CMETS_43RD_MEETING_DATE,
    CMETS_43RD_MEETING_NUMBER,
    PDF_PATH_19TH,
    PDF_PATH_20TH,
    PDF_PATH_21ST,
    PDF_PATH_25TH,
    PDF_PATH_26TH,
    PDF_PATH_27TH,
    PDF_PATH_28TH,
    PDF_PATH_29TH,
    PDF_PATH_30TH,
    PDF_PATH_31ST,
    PDF_PATH_32ND,
    PDF_PATH_33RD,
    PDF_PATH_35TH,
    PDF_PATH_36TH,
    PDF_PATH_37TH,
    PDF_PATH_38TH,
    PDF_PATH_39TH,
    PDF_PATH_40TH,
    PDF_PATH_41ST,
    PDF_PATH_43RD,
)
from cmets_extractor.domain.common.dates import (
    extract_scod_date_from_text,
    get_latest_date,
    normalize_output_date_text,
    parse_date,
)
from cmets_extractor.domain.common.ids import is_lta_application_id, remove_leading_zeros
from cmets_extractor.domain.common.numbers import parse_numeric_value, to_int_if_whole
from cmets_extractor.domain.common.text import clean_text
from cmets_extractor.domain.data_capture_common import (
    apply_battery_duration_mwh_from_text,
    capacity_total_from_parsed,
    clean_substation_value,
    extract_34th_gna_date_from_text,
    extract_34th_substation_from_text,
    extract_34th_voltage_from_text,
    extract_bay_voltage_from_text,
    extract_pooling_station_substation,
    extract_standalone_application_date_from_row,
    extract_substation_scoped_voltage,
    has_explicit_considered_grant_location,
    is_pumped_storage_nature,
    merge_capacity_breakup,
    normalize_35th_substation_name,
    normalize_lead_generator_quantum,
    normalize_substation_candidate,
    parse_34th_nature_and_type,
    parse_34th_quantum,
    parse_application_no_and_date,
    parse_conn_quantum,
    parse_connectivity_granted,
    parse_project_location,
    parse_pumped_storage_quantum_details,
    parse_raw_connectivity_location,
    parse_type_capacity,
    record_quality_score,
    strip_ps_suffix,
)
from cmets_extractor.domain.deliberation import (
    extract_deliberation_text_for_pdf,
    extract_scod_date_from_deliberation,
    extract_status_from_deliberation,
    extract_voltage_from_deliberation,
)
from cmets_extractor.domain.hybrid_context import (
    _infer_hybrid_context_from_name,
    choose_hybrid_field_context,
    extract_best_app_context_from_full_text,
    extract_ordered_hybrid_status,
    extract_preface_context_from_full_text,
    has_direct_hybrid_app_anchor,
    has_explicit_applied_signal,
    has_reg52_grant_followthrough,
    is_indirect_app_context,
    is_reference_only_context,
    promote_shared_hybrid_context,
    resolve_35th_hybrid_status,
    resolve_hybrid_status,
    scope_text_to_app,
)
from cmets_extractor.domain.re_effectiveness import normalize_energy_type_hint


def _detect_hybrid_reg52_layout(table_df):
    """Identify supported hybrid/additional-capacity table layouts."""
    if table_df is None or table_df.shape[1] not in (9, 10) or len(table_df) == 0:
        return None

    num_cols = table_df.shape[1]
    header_cells = [clean_text(table_df.iloc[0, col_idx]) or "" for col_idx in range(num_cols)]
    header_text = " ".join(header_cells).lower()

    if not ("application no" in header_text or "application id" in header_text):
        return None
    if "planned additional capacity" not in header_text:
        return None
    if "gnare within region" in header_text or "gna within region" in header_text:
        return None

    if num_cols == 9 and "already granted connectivity" in header_text:
        h6 = header_cells[6].lower()
        h7 = header_cells[7].lower()
        if "planned additional capacity" in h6:
            return {
                "app_idx": 1,
                "applicant_idx": 2,
                "project_idx": 3,
                "submission_date_idx": None,
                "nature_idx": 4,
                "conn_quantum_idx": 5,
                "already_granted_idx": None,
                "planned_idx": 6,
                "date_idx": 7,
                "connectivity_idx": 8,
            }

        if "planned additional capacity" in h7 and "connectivity location" in h6:
            return {
                "app_idx": 1,
                "applicant_idx": 2,
                "project_idx": 3,
                "submission_date_idx": None,
                "nature_idx": 4,
                "conn_quantum_idx": 5,
                "already_granted_idx": None,
                "planned_idx": 7,
                "date_idx": 8,
                "connectivity_idx": 6,
            }

    if (
        num_cols == 10
        and "application number of already granted connectivity" in header_text
        and "connectivity location" in header_text
    ):
        return {
            "app_idx": 1,
            "applicant_idx": 2,
            "project_idx": 3,
            "submission_date_idx": 4,
            "nature_idx": 5,
            "conn_quantum_idx": None,
            "already_granted_idx": 6,
            "planned_idx": 7,
            "date_idx": 8,
            "connectivity_idx": 9,
        }

    return None


def _detect_hybrid_connectivity_layout(table_df):
    """Identify supported hybrid connectivity table layouts."""
    if table_df is None or table_df.shape[1] not in (10, 11) or len(table_df) == 0:
        return None

    header_cells = [clean_text(value) or "" for value in table_df.iloc[0].tolist()]
    header = " ".join(header_cells).lower()

    if "connectivity location" not in header and "nearest pooling station" not in header:
        return None
    if "already granted connectivity" in header:
        return None
    if "gna within region" in header or "gnare within region" in header:
        return None
    if not ("application no" in header or "application id" in header):
        return None

    if (
        "connectivity quantum" in header
        and "start date of connectivity" in header
        and "submission date" not in header
    ):
        return {
            "app_idx": 1,
            "applicant_idx": 2,
            "project_idx": 3,
            "submission_date_idx": None,
            "nature_idx": 4,
            "capacity_idx": 5,
            "mode_idx": 6,
            "quantum_idx": 7,
            "start_idx": 8,
            "location_idx": 9,
            "preserve_original_on_reduced": False,
        }

    if (
        "submission date" in header
        and "nature of applicant" in header
        and "criterion" in header
        and ("connectivity quantum" in header or "injection at ists point" in header)
    ):
        return {
            "app_idx": 1,
            "applicant_idx": 2,
            "project_idx": 3,
            "submission_date_idx": 4,
            "nature_idx": 5,
            "capacity_idx": None,
            "mode_idx": 6,
            "quantum_idx": 7,
            "start_idx": 8,
            "location_idx": 9,
            "preserve_original_on_reduced": True,
        }

    if (
        "date of application" in header
        and "connectivity sought" in header
        and "generation schedule" in header
        and "criterion" in header
    ):
        return {
            "app_idx": 1,
            "applicant_idx": 2,
            "project_idx": 3,
            "submission_date_idx": 4,
            "nature_idx": 6,
            "capacity_idx": None,
            "mode_idx": 8,
            "quantum_idx": None,
            "start_idx": None,
            "location_idx": 9,
            "preserve_original_on_reduced": False,
            "combined_quantum_date_idx": 5,
            "generation_schedule_idx": 7,
        }

    return None


def _parse_legacy_connectivity_sought(value):
    """Parse older 'Connectivity Sought (MW)/date' cells used in 19th-21st meetings."""
    text = clean_text(value)
    if not text:
        return None, None

    quantum = None
    date_text = None

    match = re.search(
        r"(\d+(?:\.\d+)?)\s*/\s*([0-3]?\d[\./-][01]?\d[\./-]\d{2,4})",
        text,
    )
    if match:
        quantum = parse_numeric_value(match.group(1))
        date_text = normalize_output_date_text(match.group(2))
        return quantum, date_text

    numbers = re.findall(r"\d+(?:\.\d+)?", text)
    if numbers:
        quantum = parse_numeric_value(numbers[0])

    dates = re.findall(r"[0-3]?\d[\./-][01]?\d[\./-]\d{2,4}", text)
    if dates:
        date_text = normalize_output_date_text(dates[-1])

    return quantum, date_text


def _row_has_embedded_serial_and_app(app_cell):
    """Detect rows where serial number and app id are merged in one cell."""
    app_text = clean_text(app_cell)
    if not app_text:
        return False
    return bool(re.match(r"^\d+\.?\s+\d{10}\b", app_text))


def _upsert_record(records_by_app_id, app_id, record):
    """Keep the highest-quality duplicate record per app id."""
    score = record_quality_score(record)
    existing = records_by_app_id.get(app_id)
    if existing is None or score > existing[0]:
        records_by_app_id[app_id] = (score, record)


def extract_hybrid_reg52_records(pdf_path, meeting_number, meeting_date, deliberation_dict, full_text):
    """Extract Regulation 5.2 / additional-capacity rows from hybrid meetings."""
    print(f"\nHybrid Reg 5.2 extraction: {os.path.basename(pdf_path)}")
    tables = read_camelot_lattice_tables_chunked(pdf_path)
    records_by_app_id = {}
    normalized_full_text = re.sub(r"\s+", " ", full_text) if full_text else ""

    for table in tables:
        df = table.df
        layout = _detect_hybrid_reg52_layout(df)
        if not layout:
            continue

        for idx in range(1, len(df)):
            row = df.iloc[idx]
            sl_no = clean_text(row.iloc[0])
            if not sl_no or not re.match(r"^\d+\.?$", str(sl_no)):
                continue

            app_id, app_date = parse_application_no_and_date(row.iloc[layout["app_idx"]])
            if not app_id:
                continue
            if layout.get("submission_date_idx") is not None and not app_date:
                app_date = clean_text(row.iloc[layout["submission_date_idx"]])

            record = {
                "application_id_enhancement_5_2_or_revision": app_id,
                "application_date": app_date,
                "name_of_developers": clean_text(row.iloc[layout["applicant_idx"]]),
                "nature_of_applicant": clean_text(row.iloc[layout["nature_idx"]]),
                "cmets_gna_meeting_date": meeting_date,
            }

            conn_cell_idx = layout.get("conn_quantum_idx")
            if conn_cell_idx is not None:
                gna_id, gna_quantum, lta_id, lta_quantum = parse_conn_quantum(row.iloc[conn_cell_idx])
            else:
                gna_id, gna_quantum, lta_id, lta_quantum = parse_conn_quantum(
                    row.iloc[layout["already_granted_idx"]]
                )
            gna_id = remove_leading_zeros(gna_id)
            lta_id = remove_leading_zeros(lta_id)
            record["gna_st_ii_application_id"] = gna_id
            record["lta_application_id"] = lta_id
            record["cmets_gna_approved"] = meeting_number

            voltage, substation = parse_connectivity_granted(row.iloc[layout["connectivity_idx"]])
            if not voltage and app_id:
                delib_voltage, delib_substation = extract_voltage_from_deliberation(
                    app_id,
                    deliberation_dict,
                    gna_id=gna_id,
                    lta_id=lta_id,
                )
                if delib_voltage:
                    voltage = delib_voltage
                if delib_substation and not substation:
                    substation = delib_substation
            record["voltage_level_kv"] = voltage
            record["substation"] = strip_ps_suffix(substation)

            state, region = parse_project_location(
                row.iloc[layout["project_idx"]],
                record.get("substation"),
            )
            record["state"] = state
            record["region"] = region

            planned_capacity = parse_type_capacity(row.iloc[layout["planned_idx"]])
            record["type"] = planned_capacity.get("type")
            record["installed_breakup_solar_mw"] = planned_capacity.get("solar")
            record["installed_breakup_wind_mw"] = planned_capacity.get("wind")
            record["installed_breakup_hydro_mw"] = planned_capacity.get("hydro")
            record["battery_injection_mw"] = planned_capacity.get("bess_injection")
            if planned_capacity.get("explicit_breakup"):
                record["_explicit_type_breakup"] = True
            if planned_capacity.get("headline_total") is not None:
                record["_capacity_headline_total"] = planned_capacity.get("headline_total")

            planned_total = capacity_total_from_parsed(planned_capacity)
            connectivity_quantum = gna_quantum if gna_quantum is not None else lta_quantum
            if connectivity_quantum is not None:
                record["_existing_connectivity_quantum"] = to_int_if_whole(connectivity_quantum)
            generation_components = []
            for key, label in (("solar", "Solar"), ("wind", "Wind"), ("hydro", "Hydro")):
                value = parse_numeric_value(planned_capacity.get(key))
                if value is not None:
                    generation_components.append((label, value))
            if (
                connectivity_quantum is not None
                and len(generation_components) == 1
                and float(generation_components[0][1]) < float(connectivity_quantum)
            ):
                record["_incremental_re_component_addition"] = generation_components[0][0]

            if (
                connectivity_quantum is not None
                and planned_capacity.get("bess_injection") is not None
                and generation_components
            ):
                record["application_quantum_mw"] = to_int_if_whole(connectivity_quantum)
            elif (
                planned_total is not None
                and connectivity_quantum is not None
                and float(planned_total) < float(connectivity_quantum)
            ):
                record["application_quantum_mw"] = to_int_if_whole(connectivity_quantum)
                if planned_capacity.get("type") == "Hybrid":
                    record["installed_breakup_hybrid_mw"] = planned_total
            elif planned_total is not None:
                record["application_quantum_mw"] = planned_total
            elif connectivity_quantum is not None:
                record["application_quantum_mw"] = connectivity_quantum
            if (
                record.get("type") == "Hybrid"
                and record.get("installed_breakup_solar_mw") is None
                and record.get("installed_breakup_wind_mw") is None
                and record.get("battery_injection_mw") is None
                and planned_total is not None
                and record.get("installed_breakup_hybrid_mw") is None
            ):
                record["installed_breakup_hybrid_mw"] = planned_total

            table_date = clean_text(row.iloc[layout["date_idx"]])
            record["date_for_additional_capacity"] = get_latest_date(table_date)

            delib_text = deliberation_dict.get(app_id, "")
            app_context = extract_best_app_context_from_full_text(
                app_id,
                full_text,
                window_after=20000,
            )
            inferred_context = _infer_hybrid_context_from_name(
                record.get("name_of_developers"),
                record.get("application_quantum_mw"),
                record.get("substation"),
                normalized_full_text,
                app_id=app_id,
            )
            app_context = promote_shared_hybrid_context(
                app_id,
                exact_text=app_context,
                inferred_text=inferred_context,
            )
            field_text = choose_hybrid_field_context(
                app_id,
                exact_text=app_context,
                delib_text=delib_text,
                inferred_text=inferred_context,
            )
            raw_app_context = app_context
            raw_delib_text = delib_text
            raw_inferred_context = inferred_context
            raw_field_text = field_text
            preface_context = extract_preface_context_from_full_text(
                app_id,
                full_text,
                lookback=3600,
                lookahead=500,
            )
            app_context = scope_text_to_app(app_context, app_id, window_after=12000)
            delib_text = scope_text_to_app(delib_text, app_id, window_after=12000)
            inferred_context = scope_text_to_app(inferred_context, app_id, window_after=12000)
            field_text = scope_text_to_app(field_text, app_id, window_after=12000)

            app_quantum = record.get("application_quantum_mw")
            if (
                record.get("type") == "Hybrid"
                and record.get("installed_breakup_solar_mw") is None
                and record.get("installed_breakup_wind_mw") is None
                and record.get("battery_injection_mw") is None
            ):
                best_breakup = None
                best_score = -1
                seen_texts = set()
                for source_text in (field_text, app_context, delib_text, inferred_context):
                    normalized_source = clean_text(source_text)
                    if not normalized_source or normalized_source in seen_texts:
                        continue
                    seen_texts.add(normalized_source)
                    parsed_breakup = parse_type_capacity(normalized_source)
                    total_breakup = capacity_total_from_parsed(parsed_breakup)
                    if total_breakup is None:
                        continue
                    score = 0
                    if parsed_breakup.get("explicit_breakup"):
                        score += 3
                    if parsed_breakup.get("solar") is not None:
                        score += 1
                    if parsed_breakup.get("wind") is not None:
                        score += 1
                    if parsed_breakup.get("bess_injection") is not None:
                        score += 1
                    if app_quantum is not None:
                        diff = abs(float(total_breakup) - float(app_quantum))
                        tolerance = max(1.0, float(app_quantum) * 0.05)
                        if diff <= 0.5:
                            score += 4
                        elif diff <= tolerance:
                            score += 2
                    if score > best_score:
                        best_score = score
                        best_breakup = parsed_breakup

                if best_breakup is not None:
                    record["installed_breakup_solar_mw"] = best_breakup.get("solar")
                    record["installed_breakup_wind_mw"] = best_breakup.get("wind")
                    record["installed_breakup_hydro_mw"] = best_breakup.get("hydro")
                    record["battery_injection_mw"] = best_breakup.get("bess_injection")
                    derived_type = best_breakup.get("type")
                    if derived_type:
                        record["type"] = derived_type
                    if (
                        record.get("installed_breakup_solar_mw") is not None
                        or record.get("installed_breakup_wind_mw") is not None
                        or record.get("battery_injection_mw") is not None
                    ):
                        record["installed_breakup_hybrid_mw"] = None
            reference_only_context = (
                not has_direct_hybrid_app_anchor(field_text, app_id)
                and (
                    is_reference_only_context(field_text)
                    or is_indirect_app_context(field_text, app_id)
                )
            )
            status = extract_status_from_deliberation(
                app_id,
                deliberation_dict,
                gna_id=gna_id,
                lta_id=lta_id,
            )
            status = resolve_hybrid_status(
                status,
                exact_text=app_context,
                delib_text=delib_text,
                inferred_text=inferred_context,
                app_id=app_id,
            )
            if int(meeting_number) == CMETS_35TH_MEETING_NUMBER:
                status = resolve_35th_hybrid_status(status, field_text, app_context)
            if (
                status == "Applied"
                and not reference_only_context
                and not has_explicit_applied_signal(field_text)
                and has_reg52_grant_followthrough(field_text)
            ):
                status = "Granted"
            record["status_of_application"] = status
            apply_battery_duration_mwh_from_text(
                record,
                field_text,
                app_context,
                delib_text,
                inferred_context,
                raw_field_text,
                raw_app_context,
                raw_delib_text,
                raw_inferred_context,
                preface_context,
            )
            if int(meeting_number) == CMETS_36TH_MEETING_NUMBER and record.get("voltage_level_kv") is None:
                for source_text in (
                    field_text,
                    app_context,
                    delib_text,
                    inferred_context,
                    raw_field_text,
                    raw_app_context,
                    raw_delib_text,
                    raw_inferred_context,
                ):
                    bay_voltage, bay_substation = extract_bay_voltage_from_text(
                        source_text,
                        record.get("substation"),
                    )
                    if bay_voltage is None:
                        continue
                    record["voltage_level_kv"] = bay_voltage
                    if bay_substation and not record.get("substation"):
                        record["substation"] = bay_substation
                    break

            if field_text and not reference_only_context:
                parsed_voltage, parsed_substation = extract_34th_voltage_from_text(field_text)
                if parsed_voltage is not None and record.get("voltage_level_kv") is None:
                    record["voltage_level_kv"] = parsed_voltage
                if parsed_substation:
                    override_substation = normalize_substation_candidate(strip_ps_suffix(parsed_substation))
                    if override_substation:
                        record["substation"] = override_substation

            if status == "Withdrawn":
                record["voltage_level_kv"] = None
            elif status != "Granted" and reference_only_context:
                record["voltage_level_kv"] = None
                record["substation"] = None

            if status == "Granted" and record.get("application_quantum_mw") is not None:
                record["granted_quantum_mw"] = record["application_quantum_mw"]

            gna_date = None
            for source_text in (field_text, app_context, delib_text, inferred_context):
                if not source_text:
                    continue
                gna_date = extract_34th_gna_date_from_text(source_text)
                if gna_date:
                    break
            if not gna_date and status == "Granted":
                for source_text in (
                    field_text,
                    app_context,
                    delib_text,
                    inferred_context,
                    raw_field_text,
                    raw_app_context,
                    raw_delib_text,
                    raw_inferred_context,
                    preface_context,
                ):
                    gna_date = extract_scod_date_from_text(source_text)
                    if gna_date:
                        break
            if not gna_date and status == "Granted":
                gna_date = extract_scod_date_from_deliberation(
                    app_id,
                    deliberation_dict,
                    full_text,
                    gna_id=gna_id,
                    lta_id=lta_id,
                    strict_keywords_only=True,
                )
            if gna_date:
                record["gna_operationalization_date"] = gna_date
                if not record.get("date_for_additional_capacity"):
                    record["date_for_additional_capacity"] = normalize_output_date_text(gna_date)
                parsed_gna = parse_date(gna_date)
                if parsed_gna and status == "Granted":
                    today = datetime.now()
                    record["gna_operationalization_yes_no"] = "Yes" if parsed_gna <= today else "No"

            _upsert_record(records_by_app_id, app_id, record)

    records = [item[1] for item in records_by_app_id.values()]
    print(f"  Hybrid Reg 5.2 records: {len(records)}")
    return records


def extract_hybrid_connectivity_records(pdf_path, meeting_number, meeting_date, deliberation_dict, full_text):
    """Extract connectivity-style rows from hybrid meetings."""
    print(f"\nHybrid connectivity extraction: {os.path.basename(pdf_path)}")
    tables = read_camelot_lattice_tables_chunked(pdf_path)
    records_by_app_id = {}
    normalized_full_text = re.sub(r"\s+", " ", full_text) if full_text else ""
    last_record_app_id = None

    for table in tables:
        df = table.df
        layout = _detect_hybrid_connectivity_layout(df)
        if not layout:
            continue

        for idx in range(1, len(df)):
            row = df.iloc[idx]
            spillover_date = extract_standalone_application_date_from_row(row)
            if spillover_date and last_record_app_id:
                existing = records_by_app_id.get(last_record_app_id)
                if existing and not clean_text(existing[1].get("application_date")):
                    existing[1]["application_date"] = spillover_date
                continue

            sl_no = clean_text(row.iloc[0])
            app_cell = clean_text(row.iloc[layout["app_idx"]])
            if not (
                (sl_no and re.match(r"^\d+\.?$", str(sl_no)))
                or _row_has_embedded_serial_and_app(app_cell)
            ):
                continue

            app_id, app_date = parse_application_no_and_date(app_cell)
            if not app_id:
                continue
            if layout.get("submission_date_idx") is not None and not app_date:
                app_date = clean_text(row.iloc[layout["submission_date_idx"]])

            record = {
                "application_date": app_date,
                "name_of_developers": clean_text(row.iloc[layout["applicant_idx"]]),
                "mode_criteria": clean_text(row.iloc[layout["mode_idx"]]),
                "applied_start_date": (
                    clean_text(row.iloc[layout["start_idx"]])
                    if layout.get("start_idx") is not None
                    else None
                ),
            }

            if is_lta_application_id(app_id):
                record["lta_application_id"] = remove_leading_zeros(app_id)
                record["gna_st_ii_application_id"] = None
                record["cmets_lta_approved"] = meeting_number
                record["cmets_lta_meeting_date"] = meeting_date
            else:
                record["gna_st_ii_application_id"] = remove_leading_zeros(app_id)
                record["lta_application_id"] = None
                record["cmets_gna_approved"] = meeting_number
                record["cmets_gna_meeting_date"] = meeting_date

            substation_raw = clean_text(row.iloc[layout["location_idx"]])
            state, region = parse_project_location(
                clean_text(row.iloc[layout["project_idx"]]),
                substation_raw,
            )
            record["state"] = state
            record["region"] = region

            nature_raw = clean_text(row.iloc[layout["nature_idx"]])
            nature, energy_type = parse_34th_nature_and_type(nature_raw)
            energy_type = (
                normalize_energy_type_hint(energy_type)
                or normalize_energy_type_hint(nature_raw)
                or energy_type
            )
            record["nature_of_applicant"] = nature
            is_psp_row = is_pumped_storage_nature(nature_raw)

            quantum_raw = (
                clean_text(row.iloc[layout["quantum_idx"]])
                if layout.get("quantum_idx") is not None
                else None
            )
            if layout.get("combined_quantum_date_idx") is not None:
                combined_raw = clean_text(row.iloc[layout["combined_quantum_date_idx"]])
                combined_quantum, combined_start_date = _parse_legacy_connectivity_sought(combined_raw)
                app_quantum = combined_quantum
                granted_quantum = None
                if combined_start_date:
                    record["applied_start_date"] = combined_start_date
            else:
                app_quantum, granted_quantum = parse_34th_quantum(
                    quantum_raw,
                    preserve_original_on_reduced=bool(layout.get("preserve_original_on_reduced")),
                )
            raw_app_quantum = parse_numeric_value(app_quantum)
            psp_injection, psp_drawl = parse_pumped_storage_quantum_details(quantum_raw, nature_raw)
            if psp_injection is not None:
                record["psp_injection_mw"] = psp_injection
            if psp_drawl is not None:
                record["psp_drawl_mw"] = psp_drawl
            app_quantum = normalize_lead_generator_quantum(app_quantum, nature)
            granted_quantum = normalize_lead_generator_quantum(granted_quantum, nature)
            record["application_quantum_mw"] = app_quantum
            if granted_quantum is not None:
                record["granted_quantum_mw"] = granted_quantum
            capacity_seed_quantum = app_quantum
            if (
                app_quantum is not None
                and granted_quantum is not None
                and float(granted_quantum) < float(app_quantum)
            ):
                capacity_seed_quantum = granted_quantum

            delib_text = deliberation_dict.get(app_id, "")
            app_context = extract_best_app_context_from_full_text(
                app_id,
                full_text,
                window_after=20000,
            )
            table_capacity_text = (
                clean_text(row.iloc[layout["capacity_idx"]])
                if layout.get("capacity_idx") is not None
                else None
            )
            generation_schedule_text = (
                clean_text(row.iloc[layout["generation_schedule_idx"]])
                if layout.get("generation_schedule_idx") is not None
                else None
            )
            cap_info = parse_type_capacity(table_capacity_text)
            nature_cap_info = parse_type_capacity(nature_raw)
            text_cap_info = parse_type_capacity(delib_text) if delib_text and layout.get("capacity_idx") is not None else None
            cap_info = merge_capacity_breakup(cap_info, nature_cap_info)
            cap_info = merge_capacity_breakup(cap_info, text_cap_info)
            record["type"] = cap_info.get("type") or energy_type
            record["installed_breakup_solar_mw"] = cap_info.get("solar")
            record["installed_breakup_wind_mw"] = cap_info.get("wind")
            record["installed_breakup_hydro_mw"] = cap_info.get("hydro")
            record["battery_injection_mw"] = cap_info.get("bess_injection")
            if cap_info.get("explicit_breakup"):
                record["_explicit_type_breakup"] = True
            if cap_info.get("headline_total") is not None:
                record["_capacity_headline_total"] = cap_info.get("headline_total")
            if is_psp_row:
                record["type"] = "PSP"

            if not record.get("applied_start_date") and generation_schedule_text:
                record["applied_start_date"] = get_latest_date(generation_schedule_text)

            precise_capacity_total = capacity_total_from_parsed(cap_info)
            current_app_quantum = parse_numeric_value(record.get("application_quantum_mw"))
            current_granted_quantum = parse_numeric_value(record.get("granted_quantum_mw"))
            if (
                precise_capacity_total is not None
                and current_app_quantum is not None
                and record.get("type") in {"Solar", "Wind", "Hydro"}
                and cap_info.get("explicit_breakup")
                and not re.search(r"\d+\.\d+", quantum_raw or "")
                and float(current_app_quantum).is_integer()
                and not float(precise_capacity_total).is_integer()
                and abs(float(precise_capacity_total) - float(current_app_quantum)) <= 0.5
            ):
                record["application_quantum_mw"] = precise_capacity_total
                if (
                    current_granted_quantum is not None
                    and abs(float(current_granted_quantum) - float(current_app_quantum)) < 0.001
                ):
                    record["granted_quantum_mw"] = precise_capacity_total
                capacity_seed_quantum = precise_capacity_total

            if (
                capacity_seed_quantum is not None
                and record.get("type") == "Hybrid"
                and record.get("installed_breakup_solar_mw") is None
                and record.get("installed_breakup_wind_mw") is None
                and record.get("battery_injection_mw") is None
            ):
                record["installed_breakup_hybrid_mw"] = capacity_seed_quantum

            if capacity_seed_quantum is not None:
                if record["installed_breakup_solar_mw"] is None and record.get("type") == "Solar":
                    record["installed_breakup_solar_mw"] = capacity_seed_quantum
                if record["installed_breakup_wind_mw"] is None and record.get("type") == "Wind":
                    record["installed_breakup_wind_mw"] = capacity_seed_quantum
                if record["installed_breakup_hydro_mw"] is None and record.get("type") == "Hydro":
                    record["installed_breakup_hydro_mw"] = capacity_seed_quantum
                if record["battery_injection_mw"] is None and record.get("type") == "BESS" and not is_psp_row:
                    record["battery_injection_mw"] = capacity_seed_quantum

            inferred_context = _infer_hybrid_context_from_name(
                record.get("name_of_developers"),
                app_quantum,
                substation_raw,
                normalized_full_text,
                app_id=app_id,
            )
            app_context = promote_shared_hybrid_context(
                app_id,
                exact_text=app_context,
                inferred_text=inferred_context,
            )
            field_text = choose_hybrid_field_context(
                app_id,
                exact_text=app_context,
                delib_text=delib_text,
                inferred_text=inferred_context,
            )
            app_context = scope_text_to_app(app_context, app_id, window_after=12000)
            delib_text = scope_text_to_app(delib_text, app_id, window_after=12000)
            inferred_context = scope_text_to_app(inferred_context, app_id, window_after=12000)
            field_text = scope_text_to_app(field_text, app_id, window_after=12000)
            apply_battery_duration_mwh_from_text(
                record,
                field_text,
                app_context,
                delib_text,
                inferred_context,
            )
            if is_psp_row and (record.get("psp_injection_mw") is None or record.get("psp_drawl_mw") is None):
                for source_text in (field_text, app_context, delib_text, inferred_context):
                    if not source_text:
                        continue
                    psp_injection, psp_drawl = parse_pumped_storage_quantum_details(
                        source_text,
                        nature_raw,
                    )
                    if record.get("psp_injection_mw") is None and psp_injection is not None:
                        record["psp_injection_mw"] = psp_injection
                    if record.get("psp_drawl_mw") is None and psp_drawl is not None:
                        record["psp_drawl_mw"] = psp_drawl
                    if record.get("psp_injection_mw") is not None and record.get("psp_drawl_mw") is not None:
                        break
            if is_psp_row and (record.get("psp_injection_mw") is not None or record.get("psp_drawl_mw") is not None):
                record["battery_injection_mw"] = None
            reference_only_context = (
                not has_direct_hybrid_app_anchor(field_text, app_id)
                and (
                    is_reference_only_context(field_text)
                    or is_indirect_app_context(field_text, app_id)
                )
            )
            status = extract_status_from_deliberation(
                app_id,
                deliberation_dict,
                gna_id=record.get("gna_st_ii_application_id"),
            )
            status = resolve_hybrid_status(
                status,
                exact_text=app_context,
                delib_text=delib_text,
                inferred_text=inferred_context,
                app_id=app_id,
            )
            if int(meeting_number) == CMETS_35TH_MEETING_NUMBER:
                status = resolve_35th_hybrid_status(
                    status,
                    field_text,
                    app_context,
                    delib_text,
                    inferred_context,
                )

            if (
                status != "Granted"
                and raw_app_quantum is not None
                and not float(raw_app_quantum).is_integer()
                and "lead generator" in clean_text(nature_raw).lower()
            ):
                record["application_quantum_mw"] = to_int_if_whole(raw_app_quantum)

            raw_voltage, raw_substation = parse_raw_connectivity_location(
                substation_raw,
                allow_low_voltage=True,
            )

            voltage = raw_voltage
            text_substation = None
            if field_text and not reference_only_context:
                parsed_voltage, parsed_substation = extract_34th_voltage_from_text(field_text)
                parsed_substation = normalize_substation_candidate(parsed_substation)
                if parsed_voltage is not None and not (raw_voltage is not None and raw_substation):
                    voltage = parsed_voltage
                if parsed_substation:
                    text_substation = parsed_substation

            loc_voltage, _ = parse_connectivity_granted(substation_raw)
            delib_voltage, delib_substation = extract_voltage_from_deliberation(
                app_id,
                deliberation_dict,
                gna_id=record.get("gna_st_ii_application_id"),
            )
            delib_substation = normalize_substation_candidate(delib_substation)
            for source_text in (app_context, delib_text, inferred_context):
                if not source_text:
                    continue
                parsed_voltage, parsed_substation = extract_34th_voltage_from_text(source_text)
                parsed_substation = normalize_substation_candidate(parsed_substation)
                if parsed_voltage is not None and voltage is None:
                    voltage = parsed_voltage
                if parsed_substation and not text_substation:
                    text_substation = parsed_substation

            if status == "Granted" and int(meeting_number) == CMETS_36TH_MEETING_NUMBER:
                direct_contexts = []
                for source_text in (field_text, app_context, delib_text):
                    if not source_text:
                        continue
                    scoped_direct = scope_text_to_app(source_text, app_id, window_after=8000)
                    if has_direct_hybrid_app_anchor(scoped_direct, app_id):
                        direct_contexts.append(scoped_direct)
                direct_has_applied = any(
                    extract_ordered_hybrid_status(text) == "Applied"
                    or has_explicit_applied_signal(text)
                    for text in direct_contexts
                )
                direct_has_granted = any(
                    extract_ordered_hybrid_status(text) == "Granted"
                    for text in direct_contexts
                )
                if direct_has_applied and not direct_has_granted:
                    status = "Applied"
            if int(meeting_number) == CMETS_36TH_MEETING_NUMBER and has_explicit_applied_signal(field_text):
                status = "Applied"

            record["status_of_application"] = status
            considered_substation = None
            grant_side_substation = None
            if status != "Granted" and delib_text and has_explicit_considered_grant_location(delib_text):
                considered_substation = normalize_substation_candidate(
                    extract_34th_substation_from_text(delib_text)
                )
            if status == "Granted":
                if voltage is None and delib_voltage is not None:
                    voltage = delib_voltage
                if voltage is None and loc_voltage is not None:
                    voltage = loc_voltage
                if delib_substation and not text_substation:
                    text_substation = delib_substation
                if int(meeting_number) == CMETS_36TH_MEETING_NUMBER:
                    for source_text in (field_text, app_context, delib_text):
                        grant_voltage, grant_substation = extract_bay_voltage_from_text(source_text)
                        if grant_voltage is not None and voltage is None:
                            voltage = grant_voltage
                        grant_substation = normalize_substation_candidate(grant_substation)
                        if grant_substation:
                            grant_side_substation = grant_substation
                            text_substation = grant_substation
                            break
                substation_candidates = []
                for source_text in (field_text, app_context, delib_text, inferred_context):
                    candidate = normalize_substation_candidate(
                        extract_34th_substation_from_text(source_text)
                    )
                    if candidate:
                        substation_candidates.append(candidate)
                if substation_candidates:
                    preferred_substation = grant_side_substation or substation_candidates[-1]
                    normalized_raw = normalize_substation_candidate(raw_substation)
                    if (
                        not grant_side_substation
                        and normalized_raw
                        and preferred_substation == normalized_raw
                    ):
                        for candidate in reversed(substation_candidates):
                            if candidate != normalized_raw:
                                preferred_substation = candidate
                                break
                    text_substation = preferred_substation
                if voltage is None:
                    for source_text in (field_text, app_context, delib_text, inferred_context):
                        scoped_voltage = extract_substation_scoped_voltage(
                            source_text,
                            raw_substation or text_substation,
                        )
                        if scoped_voltage is not None:
                            voltage = scoped_voltage
                            break
            else:
                if raw_voltage is None and loc_voltage is not None:
                    raw_voltage = loc_voltage
                voltage = raw_voltage
                if int(meeting_number) == CMETS_36TH_MEETING_NUMBER and not considered_substation:
                    for source_text in (field_text, app_context, delib_text, inferred_context):
                        if not source_text:
                            continue
                        _, grant_substation = extract_bay_voltage_from_text(
                            source_text,
                            raw_substation or substation_raw,
                        )
                        grant_substation = normalize_substation_candidate(grant_substation)
                        if grant_substation:
                            considered_substation = grant_substation
                            break
                        if (
                            extract_ordered_hybrid_status(source_text) == "Granted"
                            or has_explicit_considered_grant_location(source_text)
                        ):
                            candidate = normalize_substation_candidate(
                                extract_34th_substation_from_text(source_text)
                            )
                            if candidate:
                                considered_substation = candidate
                                break
                if considered_substation:
                    text_substation = considered_substation

            substation = raw_substation or clean_substation_value(
                substation_raw,
                field_text if not raw_substation else None,
                record.get("name_of_developers"),
            )
            if text_substation:
                substation = text_substation
            if (
                int(meeting_number) != CMETS_35TH_MEETING_NUMBER
                and raw_substation
                and substation
                and re.match(r"^\s*bays?\s+at\s+", str(raw_substation), re.IGNORECASE)
            ):
                trimmed_raw = normalize_35th_substation_name(raw_substation)
                if clean_text(trimmed_raw) == clean_text(substation):
                    substation = raw_substation
            if int(meeting_number) == CMETS_35TH_MEETING_NUMBER:
                substation = normalize_35th_substation_name(substation)
                if not substation or clean_text(substation) in {"-", "na", "n/a"}:
                    for source_text in (field_text, app_context, delib_text, inferred_context):
                        pooled_substation = extract_pooling_station_substation(source_text)
                        if pooled_substation:
                            substation = pooled_substation
                            break
            if status == "Withdrawn":
                voltage = None
            elif status != "Granted" and reference_only_context:
                voltage = None

            record["substation"] = substation
            record["voltage_level_kv"] = voltage

            if status == "Granted" and app_quantum is not None and granted_quantum is None:
                record["granted_quantum_mw"] = app_quantum

            gna_date = None
            date_contexts = []
            for source_text in (field_text, app_context, delib_text, inferred_context):
                if not source_text:
                    continue
                date_contexts.append(
                    (
                        1 if has_direct_hybrid_app_anchor(source_text, app_id) else 0,
                        source_text,
                    )
                )
            date_contexts.sort(key=lambda item: item[0], reverse=True)
            for _, source_text in date_contexts:
                gna_date = extract_34th_gna_date_from_text(source_text)
                if gna_date:
                    break
            if not gna_date and status == "Granted":
                for source_text in (field_text, app_context, delib_text, inferred_context):
                    gna_date = extract_scod_date_from_text(source_text)
                    if gna_date:
                        break
            if not gna_date and status == "Granted":
                gna_date = extract_scod_date_from_deliberation(
                    app_id,
                    deliberation_dict,
                    full_text,
                    gna_id=record.get("gna_st_ii_application_id"),
                    strict_keywords_only=True,
                )
            if gna_date:
                record["gna_operationalization_date"] = gna_date
                parsed_gna = parse_date(gna_date)
                if parsed_gna and status == "Granted":
                    today = datetime.now()
                    record["gna_operationalization_yes_no"] = "Yes" if parsed_gna <= today else "No"

            _upsert_record(records_by_app_id, app_id, record)
            last_record_app_id = app_id

    records = [item[1] for item in records_by_app_id.values()]
    print(f"  Hybrid connectivity records: {len(records)}")
    return records


def extract_hybrid_meeting_data(pdf_path, meeting_number, meeting_date, label, include_reg52=True):
    """Run connectivity-style and Reg. 5.2 extraction for one hybrid meeting."""
    print("\n" + "=" * 60)
    print(f"{label} CMETS NR Meeting - Hybrid Data Extraction")
    print("=" * 60)

    if not os.path.exists(pdf_path):
        print(f"  ERROR: PDF not found: {pdf_path}")
        return []

    deliberation_dict, full_text = extract_deliberation_text_for_pdf(
        pdf_path,
        start_page=1,
        end_page=None,
    )

    connectivity_records = extract_hybrid_connectivity_records(
        pdf_path,
        meeting_number,
        meeting_date,
        deliberation_dict,
        full_text,
    )
    reg52_records = []
    if include_reg52:
        reg52_records = extract_hybrid_reg52_records(
            pdf_path,
            meeting_number,
            meeting_date,
            deliberation_dict,
            full_text,
        )
    all_records = connectivity_records + reg52_records
    print(f"\n{'=' * 60}")
    print(f"{label} CMETS TOTAL RECORDS: {len(all_records)}")
    print(f"  Connectivity-style: {len(connectivity_records)}")
    print(f"  Regulation 5.2: {len(reg52_records)}")
    print(f"{'=' * 60}")
    return all_records


def extract_39th_all_data():
    return extract_hybrid_meeting_data(
        PDF_PATH_39TH,
        CMETS_39TH_MEETING_NUMBER,
        CMETS_39TH_MEETING_DATE,
        "39th",
    )


def extract_43rd_all_data():
    return extract_hybrid_meeting_data(
        PDF_PATH_43RD,
        CMETS_43RD_MEETING_NUMBER,
        CMETS_43RD_MEETING_DATE,
        "43rd",
    )


def extract_40th_all_data():
    return extract_hybrid_meeting_data(
        PDF_PATH_40TH,
        CMETS_40TH_MEETING_NUMBER,
        CMETS_40TH_MEETING_DATE,
        "40th",
    )


def extract_41st_all_data():
    return extract_hybrid_meeting_data(
        PDF_PATH_41ST,
        CMETS_41ST_MEETING_NUMBER,
        CMETS_41ST_MEETING_DATE,
        "41st",
    )


def extract_35th_all_data():
    return extract_hybrid_meeting_data(
        PDF_PATH_35TH,
        CMETS_35TH_MEETING_NUMBER,
        CMETS_35TH_MEETING_DATE,
        "35th",
    )


def extract_38th_all_data():
    return extract_hybrid_meeting_data(
        PDF_PATH_38TH,
        CMETS_38TH_MEETING_NUMBER,
        CMETS_38TH_MEETING_DATE,
        "38th",
    )


def extract_37th_all_data():
    return extract_hybrid_meeting_data(
        PDF_PATH_37TH,
        CMETS_37TH_MEETING_NUMBER,
        CMETS_37TH_MEETING_DATE,
        "37th",
    )


def extract_36th_all_data():
    return extract_hybrid_meeting_data(
        PDF_PATH_36TH,
        CMETS_36TH_MEETING_NUMBER,
        CMETS_36TH_MEETING_DATE,
        "36th",
    )


def extract_33rd_all_data():
    return extract_hybrid_meeting_data(
        PDF_PATH_33RD,
        CMETS_33RD_MEETING_NUMBER,
        CMETS_33RD_MEETING_DATE,
        "33rd",
        include_reg52=False,
    )


def extract_32nd_all_data():
    return extract_hybrid_meeting_data(
        PDF_PATH_32ND,
        CMETS_32ND_MEETING_NUMBER,
        CMETS_32ND_MEETING_DATE,
        "32nd",
        include_reg52=False,
    )


def extract_31st_all_data():
    return extract_hybrid_meeting_data(
        PDF_PATH_31ST,
        CMETS_31ST_MEETING_NUMBER,
        CMETS_31ST_MEETING_DATE,
        "31st",
        include_reg52=False,
    )


def extract_30th_all_data():
    return extract_hybrid_meeting_data(
        PDF_PATH_30TH,
        CMETS_30TH_MEETING_NUMBER,
        CMETS_30TH_MEETING_DATE,
        "30th",
        include_reg52=False,
    )


def extract_29th_all_data():
    return extract_hybrid_meeting_data(
        PDF_PATH_29TH,
        CMETS_29TH_MEETING_NUMBER,
        CMETS_29TH_MEETING_DATE,
        "29th",
        include_reg52=False,
    )


def extract_28th_all_data():
    return extract_hybrid_meeting_data(
        PDF_PATH_28TH,
        CMETS_28TH_MEETING_NUMBER,
        CMETS_28TH_MEETING_DATE,
        "28th",
        include_reg52=False,
    )


def extract_27th_all_data():
    return extract_hybrid_meeting_data(
        PDF_PATH_27TH,
        CMETS_27TH_MEETING_NUMBER,
        CMETS_27TH_MEETING_DATE,
        "27th",
        include_reg52=False,
    )


def extract_26th_all_data():
    return extract_hybrid_meeting_data(
        PDF_PATH_26TH,
        CMETS_26TH_MEETING_NUMBER,
        CMETS_26TH_MEETING_DATE,
        "26th",
        include_reg52=False,
    )


def extract_25th_all_data():
    return extract_hybrid_meeting_data(
        PDF_PATH_25TH,
        CMETS_25TH_MEETING_NUMBER,
        CMETS_25TH_MEETING_DATE,
        "25th",
        include_reg52=False,
    )


def extract_21st_all_data():
    return extract_hybrid_meeting_data(
        PDF_PATH_21ST,
        CMETS_21ST_MEETING_NUMBER,
        CMETS_21ST_MEETING_DATE,
        "21st",
        include_reg52=False,
    )


def extract_20th_all_data():
    return extract_hybrid_meeting_data(
        PDF_PATH_20TH,
        CMETS_20TH_MEETING_NUMBER,
        CMETS_20TH_MEETING_DATE,
        "20th",
        include_reg52=False,
    )


def extract_19th_all_data():
    return extract_hybrid_meeting_data(
        PDF_PATH_19TH,
        CMETS_19TH_MEETING_NUMBER,
        CMETS_19TH_MEETING_DATE,
        "19th",
        include_reg52=False,
    )


__all__ = [
    "_detect_hybrid_connectivity_layout",
    "_detect_hybrid_reg52_layout",
    "extract_35th_all_data",
    "extract_36th_all_data",
    "extract_37th_all_data",
    "extract_38th_all_data",
    "extract_39th_all_data",
    "extract_40th_all_data",
    "extract_41st_all_data",
    "extract_43rd_all_data",
    "extract_33rd_all_data",
    "extract_32nd_all_data",
    "extract_31st_all_data",
    "extract_30th_all_data",
    "extract_29th_all_data",
    "extract_28th_all_data",
    "extract_27th_all_data",
    "extract_26th_all_data",
    "extract_25th_all_data",
    "extract_21st_all_data",
    "extract_20th_all_data",
    "extract_19th_all_data",
    "extract_hybrid_connectivity_records",
    "extract_hybrid_meeting_data",
    "extract_hybrid_reg52_records",
]
