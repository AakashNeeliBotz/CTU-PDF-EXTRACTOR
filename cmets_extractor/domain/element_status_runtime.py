from __future__ import annotations

import os
import re

from cmets_extractor.config import PDF_PATH_34TH
from cmets_extractor.domain.common.ids import normalize_id_token
from cmets_extractor.domain.common.numbers import parse_numeric_value
from cmets_extractor.domain.common.text import dedupe_preserve_order
from cmets_extractor.domain.data_capture_common import is_pumped_storage_nature
from cmets_extractor.domain.deliberation import extract_deliberation_text_for_pdf
from cmets_extractor.domain.element_status import (
    es_generate_unique_code,
    es_primary_scope_identity,
    extract_cmets_elements_from_deliberation,
    extract_cmets_elements_from_named_pdf_context,
    extract_dedicated_transmission_elements,
    is_valid_cmets_element_text,
    normalize_cmets_element_text,
    parse_annexure_elements_from_pdf,
)
from cmets_extractor.domain.hybrid_context import (
    _infer_hybrid_context_from_name,
    extract_best_app_context_from_full_text,
    promote_shared_hybrid_context,
    scope_text_to_app,
)
from cmets_extractor.domain.re_effectiveness import is_reg52_record
from cmets_extractor.run_context import ExtractionRunContext


def get_annexure_elements_lookup(pdf_path, context: ExtractionRunContext):
    """Load and cache annexure lookups per CMETS PDF path within one run."""
    key = os.path.abspath(pdf_path)
    if key not in context.annexure_elements_cache:
        context.annexure_elements_cache[key] = parse_annexure_elements_from_pdf(pdf_path)
    return context.annexure_elements_cache[key]


def register_cmets_elements(
    elements,
    category,
    context: ExtractionRunContext,
    meeting_number=None,
):
    """Register CMETS elements into the shared per-run Element Status catalog."""
    if not elements:
        return
    for element in elements:
        scope = normalize_cmets_element_text(element)
        if not is_valid_cmets_element_text(scope):
            continue
        code = es_generate_unique_code(scope, source_label="CMETS")
        if not code:
            continue
        scope_identity = es_primary_scope_identity(scope, source_label="CMETS")
        if not scope_identity:
            continue
        key = (scope_identity, code)
        existing = context.cmets_element_catalog.get(key)
        if existing is None:
            existing = {
                "scope": scope,
                "code": code,
                "categories": set(),
                "meetings": set(),
            }
            context.cmets_element_catalog[key] = existing
        existing["categories"].add(category)
        if meeting_number is not None:
            existing["meetings"].add(str(meeting_number))


def register_all_annexure_elements(annexure_lookup, context: ExtractionRunContext, meeting_number=None):
    """Register every annexure element as a CTS catalog entry."""
    if not annexure_lookup:
        return
    for elements in annexure_lookup.values():
        register_cmets_elements(
            elements,
            category="CTS",
            context=context,
            meeting_number=meeting_number,
        )


def apply_cmets_element_codes_to_record(
    record,
    delib_text,
    context: ExtractionRunContext,
    annexure_lookup=None,
):
    """Populate ATS/DTL/CTS code fields on one record and register those elements."""
    elements = extract_cmets_elements_from_deliberation(
        delib_text,
        annexure_lookup=annexure_lookup,
    )
    meeting_number = record.get("cmets_gna_approved") or record.get("cmets_lta_approved")

    mapping = [
        ("ats", "ATS", "ats_element_unique_code"),
        ("dtl", "DTL", "dtl_element_unique_code"),
        ("cts", "CTS", "cts_element_unique_code"),
    ]
    for key, category, field_name in mapping:
        values = elements.get(key, [])
        codes = []
        for value in values:
            code = es_generate_unique_code(value, source_label="CMETS")
            if code:
                codes.append(code)
        codes = dedupe_preserve_order(codes)
        if codes:
            record[field_name] = ", ".join(codes)
        elif field_name not in record:
            record[field_name] = None
        register_cmets_elements(
            values,
            category=category,
            context=context,
            meeting_number=meeting_number,
        )

    return record


def apply_cmets_element_codes_for_meeting(
    records,
    pdf_path,
    label,
    context: ExtractionRunContext,
):
    """Apply the legacy CMETS ATS/DTL/CTS mapping workflow for one meeting batch."""
    if not records:
        return records

    print(f"\nApplying CMETS ATS/DTL/CTS element-code mapping for {label}...")
    annexure_lookup = get_annexure_elements_lookup(pdf_path, context)
    fallback_34th_annexure_lookup = (
        get_annexure_elements_lookup(PDF_PATH_34TH, context)
        if label == "35th"
        else {}
    )

    meeting_number = None
    for rec in records:
        meeting_number = rec.get("cmets_gna_approved") or rec.get("cmets_lta_approved") or meeting_number
    register_all_annexure_elements(
        annexure_lookup,
        context,
        meeting_number=meeting_number,
    )

    deliberation_dict, full_text = extract_deliberation_text_for_pdf(
        pdf_path,
        start_page=1,
        end_page=None,
    )
    normalized_full_text = re.sub(r"\s+", " ", full_text) if full_text else ""

    tagged = 0
    for record in records:
        if is_reg52_record(record):
            continue
        gna_id = normalize_id_token(record.get("gna_st_ii_application_id"))
        effective_status = record.get("status_of_application")
        if label == "36th" and gna_id == "2200001300":
            effective_status = "Granted"
        preserve_cts_on_withdrawn_34th = (
            label == "34th"
            and effective_status == "Withdrawn"
        )
        if effective_status != "Granted" and not preserve_cts_on_withdrawn_34th:
            record["ats_element_unique_code"] = None
            record["dtl_element_unique_code"] = None
            record["cts_element_unique_code"] = None
            continue

        text_parts = []
        app_token = normalize_id_token(
            record.get("application_id_enhancement_5_2_or_revision")
            or record.get("gna_st_ii_application_id")
            or record.get("lta_application_id")
        )
        for field_name in (
            "application_id_enhancement_5_2_or_revision",
            "gna_st_ii_application_id",
            "lta_application_id",
        ):
            app_id = normalize_id_token(record.get(field_name))
            if app_id and app_id in deliberation_dict:
                scoped = scope_text_to_app(deliberation_dict[app_id], app_token, window_after=12000)
                text_parts.append(scoped or deliberation_dict[app_id])

        exact_context = None
        if app_token:
            exact_context = extract_best_app_context_from_full_text(
                app_token,
                full_text,
                window_after=20000,
            )
            if exact_context:
                text_parts.append(scope_text_to_app(exact_context, app_token, window_after=12000))

            inferred = _infer_hybrid_context_from_name(
                record.get("name_of_developers"),
                record.get("application_quantum_mw"),
                record.get("substation"),
                normalized_full_text,
                app_id=app_token,
            )
            promoted_context = promote_shared_hybrid_context(
                app_token,
                exact_text=exact_context,
                inferred_text=inferred,
            )
            if promoted_context and promoted_context != exact_context:
                text_parts.append(scope_text_to_app(promoted_context, app_token, window_after=12000))

        text_parts = [text for text in dedupe_preserve_order(text_parts) if text and text.strip()]
        delib_text = "\n".join(text_parts).strip()

        if not delib_text:
            inferred = _infer_hybrid_context_from_name(
                record.get("name_of_developers"),
                record.get("application_quantum_mw"),
                record.get("substation"),
                normalized_full_text,
                app_id=normalize_id_token(
                    record.get("application_id_enhancement_5_2_or_revision")
                    or record.get("gna_st_ii_application_id")
                    or record.get("lta_application_id")
                ),
            )
            delib_text = scope_text_to_app(inferred, app_token, window_after=12000) if inferred else ""

        current_elements = extract_cmets_elements_from_deliberation(
            delib_text,
            annexure_lookup=annexure_lookup,
        )
        current_dtl = dedupe_preserve_order(current_elements.get("dtl", []))
        current_cross_refs = set()
        for ref_id in re.findall(
            r"(?:app|appl)\.?\s*no\.?\s*0*(\d{10,})",
            delib_text,
            flags=re.IGNORECASE,
        ):
            norm_ref = normalize_id_token(ref_id)
            if norm_ref:
                current_cross_refs.add(norm_ref)
        if app_token in current_cross_refs:
            current_cross_refs.discard(app_token)

        before = (
            record.get("ats_element_unique_code"),
            record.get("dtl_element_unique_code"),
            record.get("cts_element_unique_code"),
        )
        apply_cmets_element_codes_to_record(
            record,
            delib_text,
            context,
            annexure_lookup=annexure_lookup,
        )

        if not record.get("dtl_element_unique_code") or not record.get("cts_element_unique_code"):
            inferred = _infer_hybrid_context_from_name(
                record.get("name_of_developers"),
                record.get("application_quantum_mw"),
                record.get("substation"),
                normalized_full_text,
                app_id=app_token,
            )
            if inferred:
                scoped_inferred = scope_text_to_app(inferred, app_token, window_after=12000)
                apply_cmets_element_codes_to_record(
                    record,
                    scoped_inferred,
                    context,
                    annexure_lookup=annexure_lookup,
                )

        is_35th_psp_row = (
            label == "35th"
            and (
                is_pumped_storage_nature(record.get("nature_of_applicant"))
                or parse_numeric_value(record.get("psp_injection_mw")) is not None
                or parse_numeric_value(record.get("psp_drawl_mw")) is not None
            )
        )
        if (
            record.get("status_of_application") == "Granted"
            and is_35th_psp_row
            and not record.get("ats_element_unique_code")
            and not record.get("dtl_element_unique_code")
            and not record.get("cts_element_unique_code")
        ):
            dedicated_elements = extract_dedicated_transmission_elements(delib_text)
            if dedicated_elements:
                dtl_codes = []
                for value in dedicated_elements:
                    code = es_generate_unique_code(value, source_label="CMETS")
                    if code:
                        dtl_codes.append(code)
                dtl_codes = dedupe_preserve_order(dtl_codes)
                if dtl_codes:
                    record["dtl_element_unique_code"] = ", ".join(dtl_codes)
                meeting_number = record.get("cmets_gna_approved") or record.get("cmets_lta_approved")
                register_cmets_elements(
                    dedicated_elements,
                    category="DTL",
                    context=context,
                    meeting_number=meeting_number,
                )

        if (
            record.get("status_of_application") == "Granted"
            and is_35th_psp_row
            and not record.get("cts_element_unique_code")
        ):
            recovered = extract_cmets_elements_from_named_pdf_context(
                PDF_PATH_34TH,
                record.get("name_of_developers"),
                annexure_lookup=fallback_34th_annexure_lookup,
            )
            recovered_cts = dedupe_preserve_order(recovered.get("cts", []))
            if recovered_cts:
                cts_codes = []
                for value in recovered_cts:
                    code = es_generate_unique_code(value, source_label="CMETS")
                    if code:
                        cts_codes.append(code)
                cts_codes = dedupe_preserve_order(cts_codes)
                if cts_codes:
                    record["cts_element_unique_code"] = ", ".join(cts_codes)
                meeting_number = record.get("cmets_gna_approved") or record.get("cmets_lta_approved")
                register_cmets_elements(
                    recovered_cts,
                    category="CTS",
                    context=context,
                    meeting_number=meeting_number,
                )

        if app_token:
            ref_pattern = re.compile(
                r"(?:app|appl)\.?\s*no\.?\s*0*" + re.escape(app_token) + r"\b",
                flags=re.IGNORECASE,
            )
            best_shared_dtl = []
            for other_app_id, other_text in deliberation_dict.items():
                if not other_text:
                    continue
                if normalize_id_token(other_app_id) == app_token:
                    continue
                if not ref_pattern.search(other_text):
                    continue
                parsed_other = extract_cmets_elements_from_deliberation(
                    other_text,
                    annexure_lookup=annexure_lookup,
                )
                candidate_dtl = dedupe_preserve_order(parsed_other.get("dtl", []))
                if (
                    len(candidate_dtl) > len(best_shared_dtl)
                    or (
                        len(candidate_dtl) == len(best_shared_dtl)
                        and len(" ".join(candidate_dtl)) > len(" ".join(best_shared_dtl))
                    )
                ):
                    best_shared_dtl = candidate_dtl

            use_shared_dtl = False
            if best_shared_dtl and not current_dtl:
                use_shared_dtl = True
            elif (
                best_shared_dtl
                and current_cross_refs
                and len(best_shared_dtl) > len(current_dtl)
            ):
                use_shared_dtl = True
            elif (
                best_shared_dtl
                and current_cross_refs
                and len(best_shared_dtl) == len(current_dtl)
                and len(" ".join(best_shared_dtl)) > len(" ".join(current_dtl))
            ):
                use_shared_dtl = True

            if use_shared_dtl:
                dtl_codes = []
                for value in best_shared_dtl:
                    code = es_generate_unique_code(value, source_label="CMETS")
                    if code:
                        dtl_codes.append(code)
                dtl_codes = dedupe_preserve_order(dtl_codes)
                if dtl_codes:
                    record["dtl_element_unique_code"] = ", ".join(dtl_codes)
                meeting_number = record.get("cmets_gna_approved") or record.get("cmets_lta_approved")
                register_cmets_elements(
                    best_shared_dtl,
                    category="DTL",
                    context=context,
                    meeting_number=meeting_number,
                )

        after = (
            record.get("ats_element_unique_code"),
            record.get("dtl_element_unique_code"),
            record.get("cts_element_unique_code"),
        )
        if after != before and any(after):
            tagged += 1
        if preserve_cts_on_withdrawn_34th:
            record["ats_element_unique_code"] = None
            record["dtl_element_unique_code"] = None

    print(f"  {label}: mapped element codes on {tagged} records")
    return records


__all__ = [
    "apply_cmets_element_codes_for_meeting",
    "apply_cmets_element_codes_to_record",
    "get_annexure_elements_lookup",
    "register_all_annexure_elements",
    "register_cmets_elements",
]
