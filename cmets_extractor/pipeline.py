from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime

from cmets_extractor.adapters.csv import save_to_csv
from cmets_extractor.adapters.element_status_workbook import (
    populate_element_status_sheet_from_cmets as _populate_element_status_sheet_from_cmets_impl,
    populate_element_status_sheet_from_monitoring_pdfs,
    populate_element_status_sheet_from_nct_pdf,
)
from cmets_extractor.adapters.workbook import (
    write_bulk_consumers_to_excel,
    write_margin_to_excel,
    write_to_excel,
)
from cmets_extractor.config import (
    CMETS_34TH_MEETING_DATE,
    CMETS_34TH_MEETING_NUMBER,
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
    CMETS_43RD_MEETING_DATE,
    CMETS_43RD_MEETING_NUMBER,
    CMETS_MEETING_DATE,
    CMETS_MEETING_NUMBER,
    NCT_PDF_PATH,
    OUTPUT_EXCEL,
    PDF_PATH,
    PDF_PATH_34TH,
    PDF_PATH_35TH,
    PDF_PATH_36TH,
    PDF_PATH_37TH,
    PDF_PATH_38TH,
    PDF_PATH_39TH,
    PDF_PATH_40TH,
    PDF_PATH_41ST,
    PDF_PATH_43RD,
)
from cmets_extractor.domain.bulk_consumers import (
    _extract_bulk_consumer_substation as _extract_bulk_consumer_substation_impl,
    _extract_bulk_consumer_substation_from_text as _extract_bulk_consumer_substation_from_text_impl,
    extract_bulk_consumers_from_pdf as _extract_bulk_consumers_from_pdf_impl,
)
from cmets_extractor.domain.data_capture_common import (
    apply_known_output_normalizations,
    clean_substation_value,
    extract_pooling_station_substation,
    normalize_state_name,
    normalize_substation_candidate,
    parse_application_no_and_date,
    parse_project_location,
    parse_raw_connectivity_location,
)
from cmets_extractor.domain.element_status import extract_section_text
from cmets_extractor.domain.element_status_runtime import apply_cmets_element_codes_for_meeting
from cmets_extractor.domain.margin import (
    extract_margin_data as _extract_margin_data_impl,
    extract_margin_records_from_table as _extract_margin_records_from_table_impl,
)
from cmets_extractor.domain.meetings.forty_second import extract_all_data
from cmets_extractor.domain.meetings.hybrid import (
    extract_35th_all_data,
    extract_36th_all_data,
    extract_37th_all_data,
    extract_38th_all_data,
    extract_39th_all_data,
    extract_40th_all_data,
    extract_41st_all_data,
    extract_43rd_all_data,
    extract_hybrid_meeting_data,
)
from cmets_extractor.domain.meetings.thirty_fourth import extract_34th_all_data
from cmets_extractor.domain.re_effectiveness import (
    apply_re_effectiveness_rules_42nd,
    apply_re_effectiveness_rules_hybrid,
    build_re_effectiveness_lookup,
    fill_empty_granted_quantum,
)
from cmets_extractor.run_context import ExtractionRunContext, build_run_context


@dataclass
class PipelineRunResult:
    """Outputs produced by one full extractor execution."""

    run_context: ExtractionRunContext
    data_capture_records: list
    bulk_records: list
    margin_records: list
    output_excel_path: str
    output_csv_path: str
    records_by_meeting: dict[str, list]
    bulk_records_by_meeting: dict[str, list]


def _build_temp_output_path(base_path):
    stem, ext = os.path.splitext(base_path)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"{stem}_{timestamp}{ext or '.xlsx'}"


def _build_temp_csv_path(base_path):
    stem, ext = os.path.splitext(base_path)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"{stem}_{timestamp}{ext or '.csv'}"


def _extract_bulk_consumer_substation_from_text(text):
    """Compatibility wrapper for the extracted Bulk Consumers substation parser."""
    return _extract_bulk_consumer_substation_from_text_impl(
        text,
        extract_section_text=extract_section_text,
        parse_raw_connectivity_location=parse_raw_connectivity_location,
        clean_substation_value=clean_substation_value,
        normalize_substation_candidate=normalize_substation_candidate,
        extract_pooling_station_substation=extract_pooling_station_substation,
    )


def _extract_bulk_consumer_substation(app_id, deliberation_dict, full_text):
    """Compatibility wrapper for the extracted Bulk Consumers substation resolver."""
    return _extract_bulk_consumer_substation_impl(
        app_id,
        deliberation_dict,
        full_text,
        extract_section_text=extract_section_text,
        parse_raw_connectivity_location=parse_raw_connectivity_location,
        clean_substation_value=clean_substation_value,
        normalize_substation_candidate=normalize_substation_candidate,
        extract_pooling_station_substation=extract_pooling_station_substation,
    )


def extract_bulk_consumers_from_pdf(pdf_path, meeting_number, meeting_date, label):
    """Compatibility wrapper for the extracted Bulk Consumers domain workflow."""
    return _extract_bulk_consumers_from_pdf_impl(
        pdf_path,
        meeting_number,
        meeting_date,
        label,
        parse_application_no_and_date=parse_application_no_and_date,
        parse_project_location=parse_project_location,
        extract_section_text=extract_section_text,
        parse_raw_connectivity_location=parse_raw_connectivity_location,
        clean_substation_value=clean_substation_value,
        normalize_substation_candidate=normalize_substation_candidate,
        extract_pooling_station_substation=extract_pooling_station_substation,
    )


def extract_margin_records_from_table(
    data_df,
    current_region=None,
    current_timeline=None,
    parent_sl_no=None,
    custom_serial_counter=0,
):
    """Compatibility wrapper for the extracted Margin table parser."""
    return _extract_margin_records_from_table_impl(
        data_df,
        current_region=current_region,
        current_timeline=current_timeline,
        parent_sl_no=parent_sl_no,
        custom_serial_counter=custom_serial_counter,
        normalize_state_name_fn=normalize_state_name,
    )


def extract_margin_data():
    """Compatibility wrapper for the extracted Margin domain workflow."""
    return _extract_margin_data_impl(normalize_state_name_fn=normalize_state_name)


def populate_element_status_sheet_from_cmets(output_excel_path, run_context: ExtractionRunContext):
    """Append CMETS ATS/DTL/CTS elements into the Element Status sheet."""
    return _populate_element_status_sheet_from_cmets_impl(
        output_excel_path,
        run_context.cmets_element_catalog,
    )


def run_pipeline(
    *,
    run_context: ExtractionRunContext | None = None,
    output_excel_path: str | None = None,
    output_csv_path: str = "extracted_data.csv",
):
    """Run the full extractor pipeline in the validated production order."""
    context = run_context if run_context is not None else build_run_context()
    context.reset()

    print("=" * 60)
    print(
        "43rd/42nd/41st/40th/39th/38th/37th/36th/35th/34th "
        "CMETS + Bulk Consumers + Margin + Element Status - Data Extraction"
    )
    print("=" * 60)

    re_lookup = build_re_effectiveness_lookup()

    records_by_meeting = {}

    records_by_meeting["43rd"] = extract_43rd_all_data()
    records_by_meeting["43rd"] = apply_re_effectiveness_rules_hybrid(
        records_by_meeting["43rd"],
        label="43rd",
        lookup=re_lookup,
    )
    records_by_meeting["43rd"] = apply_cmets_element_codes_for_meeting(
        records_by_meeting["43rd"],
        PDF_PATH_43RD,
        "43rd",
        context,
    )

    records_by_meeting["42nd"] = extract_all_data()
    records_by_meeting["42nd"] = apply_re_effectiveness_rules_42nd(
        records_by_meeting["42nd"],
        lookup=re_lookup,
    )

    records_by_meeting["41st"] = extract_41st_all_data()
    records_by_meeting["41st"] = apply_re_effectiveness_rules_hybrid(
        records_by_meeting["41st"],
        label="41st",
        lookup=re_lookup,
    )
    records_by_meeting["41st"] = apply_cmets_element_codes_for_meeting(
        records_by_meeting["41st"],
        PDF_PATH_41ST,
        "41st",
        context,
    )

    records_by_meeting["40th"] = extract_40th_all_data()
    records_by_meeting["40th"] = apply_re_effectiveness_rules_hybrid(
        records_by_meeting["40th"],
        label="40th",
        lookup=re_lookup,
    )
    records_by_meeting["40th"] = apply_cmets_element_codes_for_meeting(
        records_by_meeting["40th"],
        PDF_PATH_40TH,
        "40th",
        context,
    )

    records_by_meeting["39th"] = extract_39th_all_data()
    records_by_meeting["39th"] = apply_re_effectiveness_rules_hybrid(
        records_by_meeting["39th"],
        label="39th",
        lookup=re_lookup,
    )
    records_by_meeting["39th"] = apply_cmets_element_codes_for_meeting(
        records_by_meeting["39th"],
        PDF_PATH_39TH,
        "39th",
        context,
    )

    records_by_meeting["38th"] = extract_38th_all_data()
    records_by_meeting["38th"] = apply_re_effectiveness_rules_hybrid(
        records_by_meeting["38th"],
        label="38th",
        lookup=re_lookup,
    )
    records_by_meeting["38th"] = apply_cmets_element_codes_for_meeting(
        records_by_meeting["38th"],
        PDF_PATH_38TH,
        "38th",
        context,
    )

    records_by_meeting["37th"] = extract_37th_all_data()
    records_by_meeting["37th"] = apply_re_effectiveness_rules_hybrid(
        records_by_meeting["37th"],
        label="37th",
        lookup=re_lookup,
    )
    records_by_meeting["37th"] = apply_cmets_element_codes_for_meeting(
        records_by_meeting["37th"],
        PDF_PATH_37TH,
        "37th",
        context,
    )

    records_by_meeting["36th"] = extract_36th_all_data()
    records_by_meeting["36th"] = apply_re_effectiveness_rules_hybrid(
        records_by_meeting["36th"],
        label="36th",
        lookup=re_lookup,
    )
    records_by_meeting["36th"] = apply_cmets_element_codes_for_meeting(
        records_by_meeting["36th"],
        PDF_PATH_36TH,
        "36th",
        context,
    )

    records_by_meeting["35th"] = extract_35th_all_data()
    records_by_meeting["35th"] = apply_re_effectiveness_rules_hybrid(
        records_by_meeting["35th"],
        label="35th",
        lookup=re_lookup,
    )
    records_by_meeting["35th"] = apply_cmets_element_codes_for_meeting(
        records_by_meeting["35th"],
        PDF_PATH_35TH,
        "35th",
        context,
    )

    records_by_meeting["34th"] = extract_34th_all_data(run_context=context)
    records_by_meeting["34th"] = apply_cmets_element_codes_for_meeting(
        records_by_meeting["34th"],
        PDF_PATH_34TH,
        "34th",
        context,
    )

    all_records = (
        records_by_meeting["43rd"]
        + records_by_meeting["42nd"]
        + records_by_meeting["41st"]
        + records_by_meeting["40th"]
        + records_by_meeting["39th"]
        + records_by_meeting["38th"]
        + records_by_meeting["37th"]
        + records_by_meeting["36th"]
        + records_by_meeting["35th"]
        + records_by_meeting["34th"]
    )
    all_records = fill_empty_granted_quantum(all_records)
    all_records = apply_known_output_normalizations(all_records)

    bulk_records_by_meeting = {
        "43rd": extract_bulk_consumers_from_pdf(
            PDF_PATH_43RD,
            CMETS_43RD_MEETING_NUMBER,
            CMETS_43RD_MEETING_DATE,
            "43rd",
        ),
        "42nd": extract_bulk_consumers_from_pdf(
            PDF_PATH,
            CMETS_MEETING_NUMBER,
            CMETS_MEETING_DATE,
            "42nd",
        ),
        "41st": extract_bulk_consumers_from_pdf(
            PDF_PATH_41ST,
            CMETS_41ST_MEETING_NUMBER,
            CMETS_41ST_MEETING_DATE,
            "41st",
        ),
        "40th": extract_bulk_consumers_from_pdf(
            PDF_PATH_40TH,
            CMETS_40TH_MEETING_NUMBER,
            CMETS_40TH_MEETING_DATE,
            "40th",
        ),
        "39th": extract_bulk_consumers_from_pdf(
            PDF_PATH_39TH,
            CMETS_39TH_MEETING_NUMBER,
            CMETS_39TH_MEETING_DATE,
            "39th",
        ),
        "38th": extract_bulk_consumers_from_pdf(
            PDF_PATH_38TH,
            CMETS_38TH_MEETING_NUMBER,
            CMETS_38TH_MEETING_DATE,
            "38th",
        ),
        "37th": extract_bulk_consumers_from_pdf(
            PDF_PATH_37TH,
            CMETS_37TH_MEETING_NUMBER,
            CMETS_37TH_MEETING_DATE,
            "37th",
        ),
        "36th": extract_bulk_consumers_from_pdf(
            PDF_PATH_36TH,
            CMETS_36TH_MEETING_NUMBER,
            CMETS_36TH_MEETING_DATE,
            "36th",
        ),
        "35th": extract_bulk_consumers_from_pdf(
            PDF_PATH_35TH,
            CMETS_35TH_MEETING_NUMBER,
            CMETS_35TH_MEETING_DATE,
            "35th",
        ),
        "34th": extract_bulk_consumers_from_pdf(
            PDF_PATH_34TH,
            CMETS_34TH_MEETING_NUMBER,
            CMETS_34TH_MEETING_DATE,
            "34th",
        ),
    }
    bulk_records = (
        bulk_records_by_meeting["43rd"]
        + bulk_records_by_meeting["42nd"]
        + bulk_records_by_meeting["41st"]
        + bulk_records_by_meeting["40th"]
        + bulk_records_by_meeting["39th"]
        + bulk_records_by_meeting["38th"]
        + bulk_records_by_meeting["37th"]
        + bulk_records_by_meeting["36th"]
        + bulk_records_by_meeting["35th"]
        + bulk_records_by_meeting["34th"]
    )

    margin_records = extract_margin_data()

    print(f"\n{'=' * 60}")
    print(f"COMBINED TOTAL: {len(all_records)} records")
    print(f"  43rd CMETS: {len(records_by_meeting['43rd'])} records")
    print(f"  42nd CMETS: {len(records_by_meeting['42nd'])} records")
    print(f"  41st CMETS: {len(records_by_meeting['41st'])} records")
    print(f"  40th CMETS: {len(records_by_meeting['40th'])} records")
    print(f"  39th CMETS: {len(records_by_meeting['39th'])} records")
    print(f"  38th CMETS: {len(records_by_meeting['38th'])} records")
    print(f"  37th CMETS: {len(records_by_meeting['37th'])} records")
    print(f"  36th CMETS: {len(records_by_meeting['36th'])} records")
    print(f"  35th CMETS: {len(records_by_meeting['35th'])} records")
    print(f"  34th CMETS: {len(records_by_meeting['34th'])} records")
    print(f"  Bulk Consumers: {len(bulk_records)} records")
    print(f"    43rd CMETS: {len(bulk_records_by_meeting['43rd'])} records")
    print(f"    42nd CMETS: {len(bulk_records_by_meeting['42nd'])} records")
    print(f"    41st CMETS: {len(bulk_records_by_meeting['41st'])} records")
    print(f"    40th CMETS: {len(bulk_records_by_meeting['40th'])} records")
    print(f"    39th CMETS: {len(bulk_records_by_meeting['39th'])} records")
    print(f"    38th CMETS: {len(bulk_records_by_meeting['38th'])} records")
    print(f"    37th CMETS: {len(bulk_records_by_meeting['37th'])} records")
    print(f"    36th CMETS: {len(bulk_records_by_meeting['36th'])} records")
    print(f"    35th CMETS: {len(bulk_records_by_meeting['35th'])} records")
    print(f"    34th CMETS: {len(bulk_records_by_meeting['34th'])} records")
    print(f"  Margin sheet: {len(margin_records)} records")
    print(f"{'=' * 60}")

    effective_output_excel = output_excel_path or OUTPUT_EXCEL
    effective_output_csv = output_csv_path
    try:
        effective_output_excel = write_to_excel(
            all_records,
            output_excel_path=effective_output_excel,
        )
    except PermissionError:
        if output_excel_path is not None:
            raise
        effective_output_excel = _build_temp_output_path(OUTPUT_EXCEL)
        if output_csv_path == "extracted_data.csv":
            effective_output_csv = _build_temp_csv_path(output_csv_path)
        print(
            "\nPrimary workbook is locked; "
            f"writing output to temporary workbook: {effective_output_excel}"
        )
        if effective_output_csv != output_csv_path:
            print(f"Temporary CSV output: {effective_output_csv}")
        effective_output_excel = write_to_excel(
            all_records,
            output_excel_path=effective_output_excel,
        )

    write_bulk_consumers_to_excel(effective_output_excel, bulk_records)
    write_margin_to_excel(effective_output_excel, margin_records)
    populate_element_status_sheet_from_monitoring_pdfs(effective_output_excel)
    populate_element_status_sheet_from_nct_pdf(effective_output_excel, NCT_PDF_PATH)
    populate_element_status_sheet_from_cmets(effective_output_excel, context)
    save_to_csv(all_records, filename=effective_output_csv)

    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE!")
    print("=" * 60)
    print(f"Output file: {effective_output_excel}")

    return PipelineRunResult(
        run_context=context,
        data_capture_records=all_records,
        bulk_records=bulk_records,
        margin_records=margin_records,
        output_excel_path=effective_output_excel,
        output_csv_path=effective_output_csv,
        records_by_meeting=records_by_meeting,
        bulk_records_by_meeting=bulk_records_by_meeting,
    )


__all__ = [
    "_extract_bulk_consumer_substation",
    "_extract_bulk_consumer_substation_from_text",
    "extract_bulk_consumers_from_pdf",
    "extract_hybrid_meeting_data",
    "extract_margin_data",
    "extract_margin_records_from_table",
    "populate_element_status_sheet_from_cmets",
    "run_pipeline",
]
