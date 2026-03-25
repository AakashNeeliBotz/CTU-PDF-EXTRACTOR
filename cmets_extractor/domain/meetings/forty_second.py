from __future__ import annotations

import re
from datetime import datetime

import camelot

from cmets_extractor.config import CMETS_MEETING_DATE, CMETS_MEETING_NUMBER, PDF_PATH
from cmets_extractor.domain.common.dates import get_latest_date, parse_date
from cmets_extractor.domain.common.ids import remove_leading_zeros
from cmets_extractor.domain.common.text import clean_text
from cmets_extractor.domain.data_capture_common import (
    parse_application_no_and_date,
    parse_conn_quantum,
    parse_connectivity_granted,
    parse_planned_capacity,
    parse_project_location,
    strip_ps_suffix,
)
from cmets_extractor.domain.deliberation import (
    extract_deliberation_text,
    extract_scod_date_from_deliberation,
    extract_status_from_deliberation,
    extract_voltage_from_deliberation,
)


def extract_a1_a4_tables():
    """Load the 42nd A1-A4 lattice tables."""
    print("Extracting tables from PDF...")
    tables = camelot.read_pdf(PDF_PATH, pages="5-6", flavor="lattice")
    print(f"Found {len(tables)} tables on pages 5-6")
    nine_col_tables = [table for table in tables if table.df.shape[1] == 9]
    print(f"Filtered to {len(nine_col_tables)} 9-column tables (A1-A4)")
    return nine_col_tables


def process_table(table_df, deliberation_dict, full_text):
    """Process one 42nd A1-A4 table with the existing Reg. 5.2 rules."""
    records = []

    for idx in range(1, len(table_df)):
        row = table_df.iloc[idx]
        sl_no = str(row.iloc[0]).strip()
        if not sl_no or not re.match(r"\d+", sl_no):
            continue

        record = {}
        app_id, app_date = parse_application_no_and_date(row.iloc[1])
        record["application_id_enhancement_5_2_or_revision"] = app_id
        record["application_date"] = app_date
        record["name_of_developers"] = clean_text(row.iloc[2])

        gna_id, gna_quantum, lta_id, lta_quantum = parse_conn_quantum(row.iloc[5])
        gna_id = remove_leading_zeros(gna_id)
        lta_id = remove_leading_zeros(lta_id)
        record["gna_st_ii_application_id"] = gna_id
        record["lta_application_id"] = lta_id

        voltage, substation = parse_connectivity_granted(row.iloc[8])
        if not voltage and app_id:
            delib_voltage, delib_substation = extract_voltage_from_deliberation(
                app_id,
                deliberation_dict,
                gna_id=gna_id,
                lta_id=lta_id,
            )
            if delib_voltage:
                voltage = delib_voltage
                print(f"    App {app_id}: Voltage extracted from deliberation: {voltage} kV")
            if delib_substation and not substation:
                substation = delib_substation
                print(f"    App {app_id}: Substation extracted from deliberation: {substation}")

        record["voltage_level_kv"] = voltage
        record["substation"] = strip_ps_suffix(substation)

        state, region = parse_project_location(row.iloc[3], substation)
        record["state"] = state
        record["region"] = region
        record["nature_of_applicant"] = clean_text(row.iloc[4])

        if gna_quantum:
            record["application_quantum_mw"] = gna_quantum
        elif lta_quantum:
            record["application_quantum_mw"] = lta_quantum

        record["cmets_gna_approved"] = CMETS_MEETING_NUMBER
        record["cmets_gna_meeting_date"] = CMETS_MEETING_DATE

        capacity = parse_planned_capacity(row.iloc[6])
        record["battery_injection_mw"] = capacity["bess_injection"]
        record["installed_breakup_solar_mw"] = capacity["solar"]
        record["installed_breakup_wind_mw"] = capacity["wind"]
        record["installed_breakup_hydro_mw"] = capacity.get("hydro")
        record["type"] = capacity["type"]

        table_date = clean_text(row.iloc[7])
        record["date_for_additional_capacity"] = get_latest_date(table_date)

        status = None
        if app_id:
            status = extract_status_from_deliberation(
                app_id,
                deliberation_dict,
                gna_id=gna_id,
                lta_id=lta_id,
            )
            if status:
                print(f"    App {app_id}: Status detected as '{status}'")

        record["status_of_application"] = status
        if status == "Withdrawn":
            record["voltage_level_kv"] = None

        if record.get("application_quantum_mw") is not None:
            record["granted_quantum_mw"] = record["application_quantum_mw"]

        if status == "Granted" and app_id:
            gna_op_date = extract_scod_date_from_deliberation(
                app_id,
                deliberation_dict,
                full_text,
                gna_id=gna_id,
                lta_id=lta_id,
            )
            if gna_op_date:
                record["gna_operationalization_date"] = gna_op_date
                parsed_gna = parse_date(gna_op_date)
                if parsed_gna:
                    today = datetime.now()
                    record["gna_operationalization_yes_no"] = "Yes" if parsed_gna <= today else "No"
                print(f"    App {app_id}: GNA Op Date = {gna_op_date}")

        records.append(record)

    return records


def extract_all_data():
    """Run the full 42nd A1-A4 extraction flow."""
    deliberation_dict, full_text = extract_deliberation_text()
    tables = extract_a1_a4_tables()
    all_records = []
    table_names = ["A1. June-25", "A2. July-25", "A3. August-25", "A4. September-25"]

    for index, table in enumerate(tables):
        table_name = table_names[index] if index < len(table_names) else f"Table {index + 1}"
        print(f"\nProcessing {table_name}...")
        records = process_table(table.df, deliberation_dict, full_text)
        all_records.extend(records)
        print(f"  Extracted {len(records)} records")

    print(f"\n{'=' * 60}")
    print(f"TOTAL RECORDS EXTRACTED: {len(all_records)}")
    print(f"{'=' * 60}")
    return all_records


__all__ = ["extract_a1_a4_tables", "extract_all_data", "process_table"]
