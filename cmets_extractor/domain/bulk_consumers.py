from __future__ import annotations

import os
import re

import camelot
import fitz

from cmets_extractor.adapters.pdf import read_camelot_lattice_tables_chunked
from cmets_extractor.domain.common.dates import normalize_output_date_text
from cmets_extractor.domain.common.numbers import parse_numeric_value
from cmets_extractor.domain.common.text import clean_text, dedupe_preserve_order
from cmets_extractor.domain.deliberation import (
    extract_deliberation_text_for_pdf,
    extract_status_from_deliberation,
    extract_voltage_from_deliberation,
)
from cmets_extractor.domain.hybrid_context import (
    extract_best_app_context_from_full_text,
    extract_preface_context_from_full_text,
    scope_text_to_app,
)


def _bulk_consumer_record_quality_score(record):
    """Score Bulk Consumers rows so the more complete duplicate wins."""
    score_fields = [
        "substation",
        "region",
        "state",
        "name_of_developers",
        "quantum_within_region_mw",
        "quantum_outside_region_mw",
        "total_quantum_mw",
        "nature_of_applicant",
        "status_of_application",
        "start_date_of_gna",
        "end_date_of_gna",
    ]
    score = 0
    for key in score_fields:
        value = record.get(key)
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        score += 1
    return score


def _detect_table_header_row_count(table_df, max_rows=3):
    """Return how many leading rows belong to the header before app-id data starts."""
    if table_df is None or len(table_df) == 0:
        return 0

    scan_rows = min(max_rows, len(table_df))
    for row_idx in range(scan_rows):
        row_text = " ".join(clean_text(x) or "" for x in table_df.iloc[row_idx].tolist())
        if re.search(r"\b22\d{8}\b", row_text):
            return max(1, row_idx)
    return scan_rows


def _build_combined_table_headers(table_df, max_rows=3):
    """Combine multi-row Camelot headers into one lowercase header per column."""
    if table_df is None or len(table_df) == 0:
        return []

    header_rows = _detect_table_header_row_count(table_df, max_rows=max_rows)
    headers = []
    for col_idx in range(table_df.shape[1]):
        parts = []
        for row_idx in range(header_rows):
            cell_value = clean_text(table_df.iloc[row_idx, col_idx])
            if cell_value:
                parts.append(cell_value)
        headers.append(" ".join(dedupe_preserve_order(parts)).lower())
    return headers


def _find_bulk_consumer_header_index(headers, keyword_groups):
    """Locate one Bulk Consumers source column by keyword fragments."""
    if not headers:
        return None

    if not any(isinstance(group, (list, tuple, set)) for group in keyword_groups):
        keyword_groups = [keyword_groups]

    for idx, header in enumerate(headers):
        header_text = (header or "").lower()
        compact_header = re.sub(r"\s+", "", header_text)
        for group in keyword_groups:
            matched = True
            for token in group:
                token_text = str(token).lower()
                compact_token = re.sub(r"\s+", "", token_text)
                if token_text in header_text or compact_token in compact_header:
                    continue
                matched = False
                break
            if matched:
                return idx
    return None


def _detect_bulk_consumers_layout(table_df):
    """Identify GNARE tables that should populate the Bulk Consumers sheet."""
    if table_df is None or len(table_df) == 0 or table_df.shape[1] < 7:
        return None

    headers = _build_combined_table_headers(table_df, max_rows=3)
    header_text = " ".join(headers)
    if not (
        ("gnare" in header_text or "gna" in header_text)
        and "applicant" in header_text
        and "total" in header_text
    ):
        return None

    layout = {
        "app_idx": _find_bulk_consumer_header_index(
            headers,
            [
                ("application", "date"),
                ("application", "id"),
            ],
        ),
        "applicant_idx": _find_bulk_consumer_header_index(
            headers,
            [
                ("name", "applicant"),
                ("name", "developer"),
            ],
        ),
        "within_idx": _find_bulk_consumer_header_index(
            headers,
            [
                ("gnare", "within", "region"),
                ("gna", "within", "region"),
            ],
        ),
        "outside_idx": _find_bulk_consumer_header_index(
            headers,
            [
                ("gnare", "outside", "region"),
                ("gna", "outside", "region"),
            ],
        ),
        "total_idx": _find_bulk_consumer_header_index(
            headers,
            [
                ("total", "gnare", "required"),
                ("total", "gna", "required"),
                ("total", "quantum", "gnare"),
                ("total", "quantum", "gna"),
                ("total", "gnare", "applied"),
                ("total", "gna", "applied"),
            ],
        ),
        "nature_idx": _find_bulk_consumer_header_index(
            headers,
            [
                ("nature", "applicant"),
            ],
        ),
        "start_idx": _find_bulk_consumer_header_index(
            headers,
            [
                ("start", "date", "gnare"),
                ("start", "date", "gna"),
            ],
        ),
        "end_idx": _find_bulk_consumer_header_index(
            headers,
            [
                ("end", "date", "gnare"),
                ("end", "date", "gna"),
            ],
        ),
    }

    required_fields = ("app_idx", "applicant_idx", "within_idx", "outside_idx", "total_idx")
    if any(layout.get(field) is None for field in required_fields):
        return None
    return layout


def _extract_bulk_consumer_context(app_id, deliberation_dict, full_text):
    """Build the best local app-specific GNARE discussion context available."""
    contexts = []

    direct_text = deliberation_dict.get(app_id)
    if direct_text:
        scoped_direct = scope_text_to_app(direct_text, app_id, window_after=9000)
        if scoped_direct:
            contexts.append(scoped_direct)

    best_context = extract_best_app_context_from_full_text(app_id, full_text, window_after=9000)
    if best_context:
        scoped_best = scope_text_to_app(best_context, app_id, window_after=9000)
        if scoped_best and scoped_best not in contexts:
            contexts.append(scoped_best)

    preface_context = extract_preface_context_from_full_text(app_id, full_text)
    if preface_context:
        scoped_preface = scope_text_to_app(preface_context, app_id, window_after=9000)
        if scoped_preface and scoped_preface not in contexts:
            contexts.append(scoped_preface)

    return "\n".join(part for part in contexts if part).strip()


def find_bulk_consumer_candidate_pages(pdf_path, max_page=40):
    """Find page numbers whose text looks like GNARE/Bulk Consumers tables."""
    if not pdf_path or not os.path.exists(pdf_path):
        return []

    try:
        doc = fitz.open(pdf_path)
    except Exception:
        return []

    page_limit = len(doc) if max_page is None else min(len(doc), int(max_page))
    matches = []
    for page_idx in range(page_limit):
        raw_text = doc[page_idx].get_text() or ""
        text = re.sub(r"\s+", " ", raw_text).lower()
        if not text:
            continue
        if (
            ("gnare" in text or "gna within region" in text or "gnare within region" in text)
            and (
                "application id" in text
                or "application no" in text
                or "name of the applicant" in text
                or "nature of applicant" in text
                or "outside region" in text
                or "within region" in text
                or "total quantum" in text
            )
        ):
            matches.append(page_idx + 1)

    doc.close()
    return dedupe_preserve_order(matches)


def collapse_page_ranges(page_numbers):
    """Collapse sorted page numbers into inclusive contiguous ranges."""
    if not page_numbers:
        return []

    ordered = sorted({int(page) for page in page_numbers})
    ranges = []
    start = ordered[0]
    end = ordered[0]
    for page_no in ordered[1:]:
        if page_no == end + 1:
            end = page_no
            continue
        ranges.append((start, end))
        start = end = page_no
    ranges.append((start, end))
    return ranges


def _extract_bulk_consumer_substation_from_text(
    text,
    *,
    extract_section_text,
    parse_raw_connectivity_location,
    clean_substation_value,
    normalize_substation_candidate,
    extract_pooling_station_substation,
):
    """Extract the GNARE dedicated-transmission substation from one deliberation block."""
    if not text:
        return None

    section_text = extract_section_text(
        text,
        [
            r"Details\s+of\s+Transmission\s+System\s+for\s+Grant\s+of\s+GNA(?:RE)?\s*:?",
        ],
        [
            r"\bB\.\s",
            r"\bC\.\s",
            r"\bD\.\s",
            r"\bM/s\b",
            r"\b\d{1,3}\.?\s*22\d{8}\b",
        ],
    )
    dedicated_text = extract_section_text(
        section_text or text,
        [
            r"\bA\.\s*Dedicated\s+Transmission\s+system\s+for\s+GNA(?:RE)?\b",
        ],
        [
            r"\bB\.\s",
            r"\bC\.\s",
            r"\bD\.\s",
        ],
    )
    search_text = dedicated_text or section_text or text
    kv_prefix = r"(?:\d+(?:\s*kV)?(?:/\d+\s*kV?){0,3}\s+)?"

    directional_patterns = [
        r"\bS\s*/\s*S\s+([A-Za-z0-9][A-Za-z0-9()/\-\s]+?)(?=\s*(?:of\b|\(|,|\.|and\b|which\b|is\b|$))",
        r"\bSub\s+Station\s+([A-Za-z0-9][A-Za-z0-9()/\-\s]+?)(?=\s*(?:\(|of\b|,|\.|and\b|which\b|is\b|$))",
    ]

    candidate_patterns = [
        rf"proposed\s+ISTS\s+interconnection\s+at\s+({kv_prefix}[A-Za-z0-9()/\-\s]+?(?:\bS\s*/\s*S\b|\bSS\b|\bPS\b|\bGSS\b|\bsubstation\b|\bpooling\s+station\b))",
        rf"\bat\s+(?:existing\s+|proposed\s+)?({kv_prefix}[A-Za-z0-9()/\-\s]+?(?:\bS\s*/\s*S\b|\bSS\b|\bPS\b|\bsubstation\b|\bpooling\s+station\b))",
        rf"connected\s+to\s+(?:intra[-\s]?state\s+(?:network|transmission\s+system)(?:\s+of\s+[A-Za-z0-9()/\-\s&]+)?\s+)?(?:at\s+)?({kv_prefix}[A-Za-z0-9()/\-\s]+?(?:\bS\s*/\s*S\b|\bSS\b|\bPS\b|\bGSS\b|\bsubstation\b))",
        rf"\blevel\s+of\s+({kv_prefix}[A-Za-z0-9()/\-\s]+?(?:\bS\s*/\s*S\b|\bSS\b|\bPS\b|\bsubstation\b))",
    ]

    candidates = []
    for pattern in directional_patterns + candidate_patterns:
        for match in re.finditer(pattern, search_text, re.IGNORECASE):
            candidate_text = clean_text(match.group(1))
            if not candidate_text:
                continue
            if re.search(r"\bline\b.*\b(?:to|from)\b", candidate_text, re.IGNORECASE):
                continue
            candidate_variants = [candidate_text]
            if "&" in candidate_text:
                candidate_variants.extend(
                    fragment.strip()
                    for fragment in re.split(r"\s*&\s*", candidate_text)
                    if fragment and fragment.strip()
                )

            for variant in reversed(candidate_variants):
                _, parsed_substation = parse_raw_connectivity_location(
                    variant,
                    allow_low_voltage=True,
                )
                cleaned = parsed_substation or clean_substation_value(variant)
                cleaned = normalize_substation_candidate(cleaned)
                if cleaned:
                    candidates.append(cleaned)
                    break

    if candidates:
        return candidates[-1]

    pooling_station = extract_pooling_station_substation(search_text)
    if pooling_station:
        return pooling_station

    return None


def _extract_bulk_consumer_substation(
    app_id,
    deliberation_dict,
    full_text,
    *,
    extract_section_text,
    parse_raw_connectivity_location,
    clean_substation_value,
    normalize_substation_candidate,
    extract_pooling_station_substation,
):
    """Resolve one Bulk Consumers substation from the app's GNARE deliberation."""
    context = _extract_bulk_consumer_context(app_id, deliberation_dict, full_text)
    if not context:
        return None

    substation = _extract_bulk_consumer_substation_from_text(
        context,
        extract_section_text=extract_section_text,
        parse_raw_connectivity_location=parse_raw_connectivity_location,
        clean_substation_value=clean_substation_value,
        normalize_substation_candidate=normalize_substation_candidate,
        extract_pooling_station_substation=extract_pooling_station_substation,
    )
    if substation:
        return substation

    _, fallback_substation = extract_voltage_from_deliberation(app_id, {app_id: context})
    return fallback_substation


def _extract_bulk_consumer_status(app_id, deliberation_dict, full_text):
    """Apply DTBC-style status logic to GNARE rows, with revoked support."""
    context = _extract_bulk_consumer_context(app_id, deliberation_dict, full_text)
    if not context:
        return None

    low = context.lower()
    revoked_patterns = [
        r"\brevoked\b",
        r"\bstands\s+revoked\b",
        r"\bshall\s+stand\s+revoked\b",
        r"\bdecided\s+to\s+revoke\b",
    ]
    if any(re.search(pattern, low, re.IGNORECASE) for pattern in revoked_patterns):
        return "Revoked"

    grant_patterns = [
        r"\bit\s+was\s+decided\s+to\s+grant\b",
        r"\bdecided\s+to\s+grant\s+gnare\b",
        r"\bdecided\s+to\s+grant\b",
    ]
    if any(re.search(pattern, low, re.IGNORECASE) for pattern in grant_patterns):
        return "Granted"

    return extract_status_from_deliberation(app_id, {app_id: context})


def extract_bulk_consumers_from_pdf(
    pdf_path,
    meeting_number,
    meeting_date,
    label,
    *,
    parse_application_no_and_date,
    parse_project_location,
    extract_section_text,
    parse_raw_connectivity_location,
    clean_substation_value,
    normalize_substation_candidate,
    extract_pooling_station_substation,
):
    """Extract Bulk Consumers rows from GNARE tables in one CMETS PDF."""
    print("\n" + "=" * 60)
    print(f"{label} CMETS NR Meeting - Bulk Consumers Extraction")
    print("=" * 60)

    if not os.path.exists(pdf_path):
        print(f"  ERROR: PDF not found: {pdf_path}")
        return []

    deliberation_dict, full_text = extract_deliberation_text_for_pdf(
        pdf_path,
        start_page=1,
        end_page=None,
        truncate_before_b1=False,
    )
    candidate_pages = find_bulk_consumer_candidate_pages(pdf_path, max_page=40)
    if candidate_pages:
        print(f"  Bulk Consumers candidate pages: {candidate_pages}")
        tables = []
        for start_page, end_page in collapse_page_ranges(candidate_pages):
            tables.extend(
                read_camelot_lattice_tables_chunked(
                    pdf_path,
                    chunk_size=max(1, end_page - start_page + 1),
                    start_page=start_page,
                    end_page=end_page,
                )
            )
            for page_no in range(start_page, end_page + 1):
                try:
                    tables.extend(
                        list(
                            camelot.read_pdf(
                                pdf_path,
                                pages=str(page_no),
                                flavor="stream",
                                suppress_stdout=True,
                            )
                        )
                    )
                except Exception as exc:
                    print(f"  WARNING: Bulk Consumers stream fallback skipped page {page_no}: {exc}")
    else:
        tables = read_camelot_lattice_tables_chunked(pdf_path, end_page=40)

    records_by_app_id = {}
    ordered_app_ids = []
    matched_tables = 0

    for table in tables:
        table_df = table.df
        layout = _detect_bulk_consumers_layout(table_df)
        if not layout:
            continue

        matched_tables += 1
        print(
            f"  Bulk Consumers GNARE table detected on page "
            f"{getattr(table, 'page', '?')} with shape {table_df.shape}"
        )

        data_start_row = 1
        for row_idx in range(min(6, len(table_df))):
            row_text = " ".join(clean_text(x) or "" for x in table_df.iloc[row_idx].tolist())
            if re.search(r"\b22\d{8}\b", row_text):
                data_start_row = row_idx
                break

        for row_idx in range(data_start_row, len(table_df)):
            row = table_df.iloc[row_idx]
            row_text = " ".join(clean_text(x) or "" for x in row.tolist())
            if not row_text or not re.search(r"\b22\d{8}\b", row_text):
                continue

            app_cell = row.iloc[layout["app_idx"]]
            app_id, _ = parse_application_no_and_date(app_cell)
            if not app_id:
                app_match = re.search(r"\b(22\d{8})\b", row_text)
                app_id = app_match.group(1) if app_match else None
            if not app_id:
                continue

            if app_id not in records_by_app_id:
                ordered_app_ids.append(app_id)

            context = _extract_bulk_consumer_context(app_id, deliberation_dict, full_text)
            substation = None
            if context:
                substation = _extract_bulk_consumer_substation_from_text(
                    context,
                    extract_section_text=extract_section_text,
                    parse_raw_connectivity_location=parse_raw_connectivity_location,
                    clean_substation_value=clean_substation_value,
                    normalize_substation_candidate=normalize_substation_candidate,
                    extract_pooling_station_substation=extract_pooling_station_substation,
                )
            if not substation and context:
                _, substation = extract_voltage_from_deliberation(app_id, {app_id: context})
            state, region = parse_project_location(context, substation=substation)

            record = {
                "region": region,
                "state": state,
                "substation": substation,
                "name_of_developers": clean_text(row.iloc[layout["applicant_idx"]]),
                "group": None,
                "gna_application_id": app_id,
                "cmets_gna_approved": meeting_number,
                "cmets_gna_meeting_date": meeting_date,
                "gna_type": None,
                "quantum_within_region_mw": parse_numeric_value(row.iloc[layout["within_idx"]]),
                "quantum_outside_region_mw": parse_numeric_value(row.iloc[layout["outside_idx"]]),
                "total_quantum_mw": parse_numeric_value(row.iloc[layout["total_idx"]]),
                "nature_of_applicant": (
                    clean_text(row.iloc[layout["nature_idx"]])
                    if layout.get("nature_idx") is not None
                    else None
                ),
                "status_of_application": _extract_bulk_consumer_status(
                    app_id,
                    deliberation_dict,
                    full_text,
                ),
                "start_date_of_gna": (
                    normalize_output_date_text(row.iloc[layout["start_idx"]])
                    if layout.get("start_idx") is not None
                    else None
                ),
                "end_date_of_gna": (
                    normalize_output_date_text(row.iloc[layout["end_idx"]])
                    if layout.get("end_idx") is not None
                    else None
                ),
            }

            if not clean_text(record.get("name_of_developers")):
                continue
            if (
                record.get("quantum_within_region_mw") is None
                and record.get("quantum_outside_region_mw") is None
                and record.get("total_quantum_mw") is None
            ):
                continue

            score = _bulk_consumer_record_quality_score(record)
            existing = records_by_app_id.get(app_id)
            if existing is None or score > existing[0]:
                records_by_app_id[app_id] = (score, record)

    records = [records_by_app_id[app_id][1] for app_id in ordered_app_ids if app_id in records_by_app_id]
    print(
        f"  Bulk Consumers summary for {label}: "
        f"tables={matched_tables}, rows={len(records)}"
    )
    return records
