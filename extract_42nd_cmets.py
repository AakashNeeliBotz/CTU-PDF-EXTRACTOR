"""
Compatibility entrypoint for the CMETS extractor.

The root module keeps the legacy import surface and CLI entrypoint while
delegating business logic to the extracted package modules.
"""

from __future__ import annotations

import os
import re
from datetime import datetime

import camelot
import fitz  # PyMuPDF for text extraction
import pandas as pd

from cmets_extractor.adapters.csv import save_to_csv
from cmets_extractor.adapters.element_status_workbook import (
    es_append_cmets_catalog_entries,
    es_build_existing_row_index,
    es_ensure_element_status_headers,
    es_populate_sheet_from_source_rows,
    es_write_sheet_row,
    populate_element_status_sheet_from_monitoring_pdfs,
    populate_element_status_sheet_from_nct_pdf,
    populate_element_status_sheet_from_source_pdf,
)
from cmets_extractor.adapters.pdf import get_pdf_page_count, read_camelot_lattice_tables_chunked
from cmets_extractor.adapters.workbook import (
    prepare_bulk_consumers_excel_value,
    prepare_data_capture_excel_value,
    write_bulk_consumers_to_excel,
    write_margin_to_excel,
    write_to_excel,
)
from cmets_extractor.config import *  # re-exported legacy module-level constants
from cmets_extractor.domain.bulk_consumers import (
    _build_combined_table_headers,
    _bulk_consumer_record_quality_score,
    _detect_bulk_consumers_layout,
    _detect_table_header_row_count,
    _extract_bulk_consumer_context,
    _extract_bulk_consumer_status,
    _find_bulk_consumer_header_index,
    collapse_page_ranges,
    find_bulk_consumer_candidate_pages,
)
from cmets_extractor.domain.common.dates import (
    extract_scod_date_from_text,
    get_latest_date,
    normalize_output_date_text,
    parse_date,
)
from cmets_extractor.domain.common.ids import is_lta_application_id, normalize_id_token, remove_leading_zeros
from cmets_extractor.domain.common.numbers import convert_to_numeric, parse_numeric_value, to_int_if_whole
from cmets_extractor.domain.common.text import clean_text, dedupe_preserve_order
from cmets_extractor.domain.data_capture_common import (
    _substation_match_key,
    apply_battery_duration_mwh_from_text,
    apply_known_output_normalizations,
    capacity_total_from_parsed,
    clean_substation_value,
    extract_34th_gna_date_from_text,
    extract_34th_substation_from_text,
    extract_34th_voltage_from_text,
    extract_bay_voltage_from_text,
    extract_pooling_station_substation,
    extract_requested_voltage_from_text,
    extract_standalone_application_date_from_row,
    extract_substation_scoped_voltage,
    get_region_from_substation,
    get_state_from_substation,
    has_explicit_considered_grant_location,
    is_noisy_substation_candidate,
    is_pumped_storage_nature,
    merge_capacity_breakup,
    normalize_35th_substation_name,
    normalize_lead_generator_quantum,
    normalize_state_name,
    normalize_substation,
    normalize_substation_candidate,
    parse_34th_nature_and_type,
    parse_34th_quantum,
    parse_application_no_and_date,
    parse_conn_quantum,
    parse_connectivity_granted,
    parse_planned_capacity,
    parse_project_location,
    parse_pumped_storage_quantum_details,
    parse_raw_connectivity_location,
    parse_type_capacity,
    record_quality_score,
    select_primary_substation_variant,
    strip_ps_suffix,
)
from cmets_extractor.domain.deliberation import (
    extract_deliberation_text,
    extract_deliberation_text_for_pdf,
    extract_scod_date_from_deliberation,
    extract_status_from_deliberation,
    extract_voltage_from_deliberation,
)
from cmets_extractor.domain.element_status import (
    ELEMENT_STATUS_MAPPING_RULES,
    ELEMENT_STATUS_SRC_COLS_MAP,
    build_element_status_source_data,
    build_nct_element_status_source_data,
    es_apply_nct_scope_overrides,
    es_build_nct_page_lines,
    es_calculate_nct_length,
    es_calculate_nct_mva,
    es_clean_nct_scope,
    es_clean_text,
    es_collect_nct_rows_from_page_block,
    es_compact_nct_scheme_label,
    es_detect_nct_table_kind,
    es_establishment_identity_key,
    es_extract_nct_scheme_context,
    es_extract_scheme_details,
    es_find_col,
    es_find_existing_scope_row,
    es_generate_unique_code,
    es_is_nct_header_line,
    es_is_nct_table_terminator,
    es_is_number,
    es_join_nct_fragments,
    es_merge_nct_source_rows,
    es_nct_awarded_to_from_remarks,
    es_nct_circuit_multiplier,
    es_nct_column_bounds,
    es_nct_inter_from_scheme_label,
    es_nct_mode_from_remarks,
    es_nct_scope_key,
    es_normalize_awarded_to,
    es_normalize_code,
    es_normalize_establishment_station_token,
    es_normalize_nct_context_labels,
    es_normalize_nct_text,
    es_normalize_scope_identity_text,
    es_normalize_state_labels,
    es_primary_scope_identity,
    es_register_scope_row_keys,
    es_rule_value,
    es_scope_match_keys,
    es_scope_token_key,
    es_source_scope_and_code,
    es_split_nct_line_columns,
    es_strip_optional_line_tail,
    es_table_has_header,
    es_to_float,
    extract_annexure_refs_from_text,
    extract_cmets_elements_from_deliberation,
    extract_cmets_elements_from_named_pdf_context,
    extract_dedicated_transmission_elements,
    extract_element_status_tables,
    extract_section_text,
    is_valid_cmets_element_text,
    merge_tbcb_element_tables,
    normalize_annexure_label,
    normalize_cmets_element_text,
    parse_annexure_elements_from_block,
    parse_annexure_elements_from_pdf,
    parse_cmets_section_elements,
    split_numbered_elements,
)
from cmets_extractor.domain.element_status_runtime import (
    apply_cmets_element_codes_for_meeting as _apply_cmets_element_codes_for_meeting_impl,
    apply_cmets_element_codes_to_record as _apply_cmets_element_codes_to_record_impl,
    get_annexure_elements_lookup as _get_annexure_elements_lookup_impl,
    register_all_annexure_elements as _register_all_annexure_elements_impl,
    register_cmets_elements as _register_cmets_elements_impl,
)
from cmets_extractor.domain.hybrid_context import (
    _infer_hybrid_context_from_name,
    choose_hybrid_field_context,
    extract_34th_status_from_text,
    extract_best_app_context_from_full_text,
    extract_duration_hours_from_text,
    extract_ordered_hybrid_status,
    extract_preface_context_from_full_text,
    get_hybrid_app_anchor_offset,
    has_direct_hybrid_app_anchor,
    has_explicit_applied_signal,
    has_reg52_grant_followthrough,
    has_shared_hybrid_decision_context,
    is_indirect_app_context,
    is_inline_app_reference,
    is_reference_only_context,
    promote_shared_hybrid_context,
    resolve_35th_hybrid_status,
    resolve_hybrid_status,
    scope_text_to_app,
    score_hybrid_context,
)
from cmets_extractor.domain.margin import (
    clean_margin_substation_name,
    extract_additional_info_from_pooling_ss,
    extract_margin_pooling_ss,
    propagate_state_to_parent_complex,
    replace_multiplication_patterns,
)
from cmets_extractor.domain.meetings.forty_second import (
    extract_a1_a4_tables,
    extract_all_data,
    process_table,
)
from cmets_extractor.domain.meetings.hybrid import (
    _detect_hybrid_connectivity_layout,
    _detect_hybrid_reg52_layout,
    extract_35th_all_data,
    extract_36th_all_data,
    extract_37th_all_data,
    extract_38th_all_data,
    extract_39th_all_data,
    extract_40th_all_data,
    extract_41st_all_data,
    extract_43rd_all_data,
    extract_hybrid_connectivity_records,
    extract_hybrid_meeting_data,
    extract_hybrid_reg52_records,
)
from cmets_extractor.domain.meetings.thirty_fourth import (
    build_34th_page_text_map as _build_34th_page_text_map_impl,
    build_connectivity_record_from_page_text as _build_connectivity_record_from_page_text_impl,
    extract_34th_all_data as _extract_34th_all_data_impl,
    extract_34th_row_segment_from_full_text,
    extract_34th_row_segment_from_page_text,
    process_34th_connectivity_tables as _process_34th_connectivity_tables_impl,
    process_34th_transition_tables as _process_34th_transition_tables_impl,
    split_34th_applicant_and_location,
)
from cmets_extractor.domain.re_effectiveness import (
    apply_re_effectiveness_rules,
    apply_re_effectiveness_rules_42nd,
    apply_re_effectiveness_rules_hybrid,
    build_re_effectiveness_lookup,
    components_to_type,
    extract_ids_from_application_cell,
    extract_stii_ids_from_application_cell,
    fill_empty_granted_quantum,
    is_reg52_record,
    normalize_energy_type_hint,
    normalize_project_type,
    type_to_components,
)
from cmets_extractor.pipeline import (
    _extract_bulk_consumer_substation,
    _extract_bulk_consumer_substation_from_text,
    extract_bulk_consumers_from_pdf,
    extract_margin_data,
    extract_margin_records_from_table,
    populate_element_status_sheet_from_cmets as _populate_element_status_sheet_from_cmets_impl,
    run_pipeline,
)
from cmets_extractor.run_context import build_run_context


_RUN_CONTEXT = build_run_context()

# Legacy mutable globals remain as compatibility aliases backed by the explicit run context.
ANNEXURE_ELEMENTS_CACHE = _RUN_CONTEXT.annexure_elements_cache
CMETS_ELEMENT_CATALOG = _RUN_CONTEXT.cmets_element_catalog


def get_annexure_elements_lookup(pdf_path):
    """Compatibility wrapper for the run-scoped annexure cache lookup."""
    return _get_annexure_elements_lookup_impl(pdf_path, _RUN_CONTEXT)


def register_cmets_elements(elements, category, meeting_number=None):
    """Compatibility wrapper for CMETS element-catalog registration."""
    return _register_cmets_elements_impl(
        elements,
        category,
        _RUN_CONTEXT,
        meeting_number=meeting_number,
    )


def register_all_annexure_elements(annexure_lookup, meeting_number=None):
    """Compatibility wrapper for annexure catalog registration."""
    return _register_all_annexure_elements_impl(
        annexure_lookup,
        _RUN_CONTEXT,
        meeting_number=meeting_number,
    )


def apply_cmets_element_codes_to_record(record, delib_text, annexure_lookup=None):
    """Compatibility wrapper for record-level CMETS element-code mapping."""
    return _apply_cmets_element_codes_to_record_impl(
        record,
        delib_text,
        _RUN_CONTEXT,
        annexure_lookup=annexure_lookup,
    )


def apply_cmets_element_codes_for_meeting(records, pdf_path, label):
    """Compatibility wrapper for meeting-level CMETS element-code mapping."""
    return _apply_cmets_element_codes_for_meeting_impl(
        records,
        pdf_path,
        label,
        _RUN_CONTEXT,
    )


def build_34th_page_text_map():
    return _build_34th_page_text_map_impl()


def build_connectivity_record_from_page_text(app_id, page_num, page_text_map, full_text=None):
    return _build_connectivity_record_from_page_text_impl(
        app_id,
        page_num,
        page_text_map,
        full_text,
        run_context=_RUN_CONTEXT,
    )


def process_34th_transition_tables():
    return _process_34th_transition_tables_impl(run_context=_RUN_CONTEXT)


def process_34th_connectivity_tables():
    return _process_34th_connectivity_tables_impl(run_context=_RUN_CONTEXT)


def extract_34th_all_data():
    return _extract_34th_all_data_impl(run_context=_RUN_CONTEXT)


def populate_element_status_sheet_from_cmets(output_excel_path):
    """Append CMETS ATS/DTL/CTS elements into Element Status sheet with unique codes."""
    return _populate_element_status_sheet_from_cmets_impl(output_excel_path, _RUN_CONTEXT)


if __name__ == "__main__":
    run_pipeline(run_context=_RUN_CONTEXT)
