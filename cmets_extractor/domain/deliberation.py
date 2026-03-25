from __future__ import annotations

import os
import re

import fitz

from cmets_extractor.config import PDF_PATH
from cmets_extractor.domain.common.dates import parse_date


def extract_deliberation_text_for_pdf(pdf_path, start_page=1, end_page=None, truncate_before_b1=False):
    """
    Extract deliberation text and map app-id -> local deliberation segment.

    Args:
        pdf_path: source PDF path.
        start_page: 1-based start page (inclusive).
        end_page: 1-based end page (inclusive). None means end of document.
        truncate_before_b1: whether to truncate before B1 marker.
    """
    print(f"Extracting deliberation text from {os.path.basename(pdf_path)}...")
    doc = fitz.open(pdf_path)

    total_pages = len(doc)
    start_idx = max(0, int(start_page) - 1)
    end_idx_exclusive = total_pages if end_page is None else min(total_pages, int(end_page))

    full_text = ""
    for page_num in range(start_idx, end_idx_exclusive):
        full_text += (doc[page_num].get_text() or "") + "\n"

    doc.close()

    if truncate_before_b1:
        # For 42nd deliberation blocks: prevent leakage into B1 deferred section.
        b1_patterns = [
            r"B1\.\s*GNARE\s+application",
            r"B1\.\s+.*?deferred\s+in\s+\d+(?:st|nd|rd|th)\s+CMETS",
            r"B1\.\s+",
        ]
        for pattern in b1_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                print(f"  Truncating text before section B1 (found at position {match.start()})")
                full_text = full_text[:match.start()]
                break

    deliberation_dict = {}
    app_pattern = r"(22\d{8})"
    all_matches = list(re.finditer(app_pattern, full_text))

    if not all_matches:
        print("  No application IDs found in deliberation text")
        return deliberation_dict, full_text

    # Ignore in-text reference mentions like "App. No. 2200001970" while
    # building row boundaries; these references can appear inside one app's
    # deliberation and would otherwise truncate that app context too early.
    app_positions = []
    for match in all_matches:
        pos = match.start()
        prev_window = full_text[max(0, pos - 40):pos].lower()
        if re.search(r"(?:app|appl)\.?\s*no\.?\s*$", prev_window):
            continue
        app_positions.append((pos, match.group(1)))

    if not app_positions:
        app_positions = [(match.start(), match.group(1)) for match in all_matches]

    for index, (pos, app_id) in enumerate(app_positions):
        end_pos = len(full_text)
        for next_pos, next_id in app_positions[index + 1:]:
            if next_id != app_id:
                end_pos = next_pos
                break

        context = full_text[pos:end_pos]
        if app_id not in deliberation_dict:
            deliberation_dict[app_id] = context
        else:
            deliberation_dict[app_id] += "\n" + context

    print(f"  Found deliberation text for {len(deliberation_dict)} applications")
    return deliberation_dict, full_text


def extract_deliberation_text():
    """42nd-specific deliberation extraction wrapper (pages 8-28, truncate before B1)."""
    return extract_deliberation_text_for_pdf(
        PDF_PATH,
        start_page=8,
        end_page=28,
        truncate_before_b1=True,
    )


def extract_scod_date_from_deliberation(
    app_id,
    deliberation_dict,
    full_text,
    gna_id=None,
    lta_id=None,
    strict_keywords_only=False,
):
    """
    Extract the GNA Operationalization Date (SCOD) from deliberation text.

    Strategy:
    1. Look for dates near SCOD/SCoD keywords and take the last one mentioned.
    2. If no SCOD keywords are found, fall back to the furthest date in the
       truncated local deliberation block.
    """
    text = deliberation_dict.get(app_id, "")

    for alt_id in [gna_id, lta_id]:
        if alt_id and alt_id != app_id and alt_id in deliberation_dict:
            alt_text = deliberation_dict[alt_id]
            if alt_text:
                text = text + "\n" + alt_text

    if not text.strip():
        return None

    valid_ids = set()
    if app_id:
        valid_ids.add(str(app_id).lstrip("0"))
        valid_ids.add(str(app_id))
    if gna_id:
        valid_ids.add(str(gna_id).lstrip("0"))
        valid_ids.add(str(gna_id))
    if lta_id:
        valid_ids.add(str(lta_id).lstrip("0"))
        valid_ids.add(str(lta_id))

    mentioned_ids = set(re.findall(r"\b(\d{10,})\b", text))
    mentioned_ids_normalized = set()
    for mentioned_id in mentioned_ids:
        mentioned_ids_normalized.add(mentioned_id)
        mentioned_ids_normalized.add(mentioned_id.lstrip("0"))

    if not valid_ids.intersection(mentioned_ids_normalized):
        return None

    truncated_text = text
    end_markers = [
        r"noted\s+the\s+same\s*\.",
        r"agreed\s+for\s+the\s+same\s*\.",
        r"noted\s+and\s+agreed\s+for\s+the\s+same\s*\.",
    ]
    earliest_end = len(text)
    for marker in end_markers:
        matches = list(re.finditer(marker, text, re.IGNORECASE))
        if matches:
            last_end = matches[-1].end()
            if last_end < earliest_end:
                earliest_end = last_end

    if earliest_end < len(text):
        truncated_text = text[:earliest_end]

    scod_date_patterns = [
        r"S[Cc]o[Dd]\s+(?:of\s+|for[^.]*?as\s+)?(\d{2}[\.\-]\d{2}[\.\-]\d{4})",
        r"provided\s+(?:SCoD|SCOD)[^.]*?\bfrom\s+(\d{2}[\.\-]\d{2}[\.\-]\d{4})",
        r"(?:tentative\s+)?start\s+date\s+of\s+(?:SCoD|SCOD)\s+(\d{2}[\.\-]\d{2}[\.\-]\d{4})",
        r"SCOD\s+for\s+additional\s+capacity\s+as\s+(\d{2}[\.\-]\d{2}[\.\-]\d{4})",
        r"consider\s+SCOD[^.]*?as\s+(\d{2}[\.\-]\d{2}[\.\-]\d{4})",
        r"agreed\s+to\s+grant[^.]*?(?:SCoD|SCOD)\s+of\s+(\d{2}[\.\-]\d{2}[\.\-]\d{4})",
        r"agreed\s+to\s+grant\s+the\s+same\s+with\s+(?:SCoD|SCOD)\s+of\s+(\d{2}[\.\-]\d{2}[\.\-]\d{4})",
        r"start\s+date\s+of\s+connectivity[^.]*?(\d{2}[\.\-]\d{2}[\.\-]\d{4})",
    ]

    scod_dates = []
    for pattern in scod_date_patterns:
        for match in re.finditer(pattern, truncated_text, re.IGNORECASE):
            date_str = match.group(1)
            parsed = parse_date(date_str)
            if parsed:
                scod_dates.append((match.start(), parsed, date_str))

    if scod_dates:
        scod_dates.sort(key=lambda item: item[0])
        return scod_dates[-1][2]

    if strict_keywords_only:
        return None

    all_dates = re.findall(r"(\d{2}[\.\-]\d{2}[\.\-]\d{4})", truncated_text)
    if all_dates:
        parsed_dates = []
        for date_str in all_dates:
            parsed = parse_date(date_str)
            if parsed:
                parsed_dates.append((parsed, date_str))

        if parsed_dates:
            parsed_dates.sort(key=lambda item: item[0], reverse=True)
            return parsed_dates[0][1]

    return None


def extract_status_from_deliberation(app_id, deliberation_dict, gna_id=None, lta_id=None):
    """
    Extract application status from deliberation text.

    Priority order:
    1. Defer -> Applied
    2. Close/Withdrawn -> Withdrawn
    3. Granted -> Granted
    4. Default -> Applied
    """
    raw_text = deliberation_dict.get(app_id, "")

    for alt_id in [gna_id, lta_id]:
        if alt_id and alt_id != app_id and alt_id in deliberation_dict:
            alt_text = deliberation_dict[alt_id]
            if alt_text:
                raw_text = raw_text + "\n" + alt_text

    if not raw_text.strip():
        return None

    valid_ids = set()
    if app_id:
        valid_ids.add(str(app_id).lstrip("0"))
        valid_ids.add(str(app_id))
    if gna_id:
        valid_ids.add(str(gna_id).lstrip("0"))
        valid_ids.add(str(gna_id))
    if lta_id:
        valid_ids.add(str(lta_id).lstrip("0"))
        valid_ids.add(str(lta_id))

    mentioned_ids = set(re.findall(r"\b(\d{10,})\b", raw_text))
    mentioned_ids_normalized = set()
    for mentioned_id in mentioned_ids:
        mentioned_ids_normalized.add(mentioned_id)
        mentioned_ids_normalized.add(mentioned_id.lstrip("0"))

    if not valid_ids.intersection(mentioned_ids_normalized):
        return None

    text = raw_text.lower()
    end_markers = [
        r"noted\s+the\s+same\s*\.",
        r"agreed\s+for\s+the\s+same\s*\.",
        r"noted\s+and\s+agreed\s+for\s+the\s+same\s*\.",
        r"noted\s+and\s+agreed\s*\.",
    ]
    last_end_pos = -1
    for marker in end_markers:
        matches = list(re.finditer(marker, text, re.IGNORECASE))
        if matches:
            pos = matches[-1].end()
            if pos > last_end_pos:
                last_end_pos = pos

    if last_end_pos > 0:
        text = text[:last_end_pos]

    defer_patterns = [
        r"decided\s+to\s+defer\s+the\s+above\s+application",
        r"decided\s+to\s+defer\s+the\s+above",
        r"it\s+was\s+decided\s+to\s+defer",
        r"application.*?may\s+be\s+taken\s+up.*?at\s+later\s+stage",
        r"shall\s+be\s+considered\s+for\s+discussion.*?next\s+cmets",
        r"considered\s+for\s+discussion.*?next\s+cmets",
        r"(?:it\s+was\s+)?decided\s+to\s+take\s+up\s+the\s+above\s+application.*?for\s+discussion.*?next\s+cmets",
        r"take\s+up\s+the\s+above\s+application.*?for\s+discussion.*?next\s+cmets",
        r"again\s+for\s+discussion\s+in\s+the\s+next\s+cmets",
        r"request\s+for\s+connectivity\s+at\s+\d+\s*kV\s+is\s+to\s+be\s+reviewed",
    ]
    for pattern in defer_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return "Applied"

    withdrawn_patterns = [
        r"it\s+was\s+decided\s+to\s+close\s+the\s+above\s+application",
        r"decided\s+to\s+close\s+the\s+above\s+application",
        r"close\s+the\s+above\s+application\s+in\s+line\s+with",
        r"decided\s+to\s+close.*?in\s+line\s+with\s+37\.10",
        r"application.*?closed\s+in\s+line\s+with",
        r"has\s+withdrawn\s+their\s+application",
        r"has\s+withdrawn\s+the\s+above\s+application",
        r"application\s+shall\s+be\s+closed\s+as\s+per\s+GNA",
        r"the\s+above\s+application\s+shall\s+be\s+closed",
    ]
    for pattern in withdrawn_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return "Withdrawn"

    granted_patterns = [
        r"shall\s+be\s+issued",
        r"agreed\s*to\s*grant",
        r"agreedto\s+grant",
        r"it\s+was\s+agreed\s+to\s+grant",
        r"start\s+date\s+of\s+connectivity\s+under\s+gna\s+shall\s+be",
        r"intimation\s+for\s+grant.*?shall\s+be\s+issued",
        r"in-principle\s+intimation\s+for\s+grant",
        r"it\s+was\s+agreed\s+to\s+grant\s+the\s+above",
        r"grant\s+the\s+above.*?agreed",
        r"being\s+taken\s+up\s+for\s+discussion\s*(?:&|and)\s*grant",
        r"taken\s+up\s+for\s+discussion\s*(?:&|and)\s*grant",
        r"proposed\s+to\s+grant\s+connectivity\s+to",
        r"proposed\s+to\s+grant\s+addition\s+of\s+generation\s+capacity",
    ]
    for pattern in granted_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return "Granted"

    return "Applied"


def extract_voltage_from_deliberation(app_id, deliberation_dict, gna_id=None, lta_id=None):
    """
    Extract voltage level and substation from deliberation text.

    Returns:
        (voltage, substation) tuple
    """
    text_parts = []
    for key in [app_id, gna_id, lta_id]:
        if key and key in deliberation_dict and deliberation_dict[key]:
            text_parts.append(deliberation_dict[key])

    if not text_parts:
        return None, None

    text = "\n".join(text_parts)

    valid_ids = set()
    if app_id:
        valid_ids.add(str(app_id).lstrip("0"))
        valid_ids.add(str(app_id))
    if gna_id:
        valid_ids.add(str(gna_id).lstrip("0"))
        valid_ids.add(str(gna_id))
    if lta_id:
        valid_ids.add(str(lta_id).lstrip("0"))
        valid_ids.add(str(lta_id))

    candidate_texts = []
    id_matches = list(re.finditer(r"\b(\d{10,})\b", text))
    for match in id_matches:
        found = match.group(1)
        if found in valid_ids or found.lstrip("0") in valid_ids:
            start = max(0, match.start() - 300)
            end = min(len(text), match.end() + 300)
            candidate_texts.append(text[start:end])

    search_text = "\n".join(candidate_texts) if candidate_texts else text

    voltage_substation_patterns = [
        r"at\s+(\d+)\s*kV\s+([A-Za-z0-9\-\s\(\)]+?)(?:\s+under\s+App)",
        r"granted\s+at\s+(\d+)\s*kV\s+([A-Za-z0-9\-\s\(\)]+?)(?:\s+under|\s+for|\s*\.)",
        r"connectivity\s+at\s+(\d+)\s*kV\s+([A-Za-z0-9\-\s\(\)]+?)(?:\s+under|\s+for|\s*\.)",
        r"(\d+)\s*kV\s+([A-Za-z0-9\-]+(?:\-[IVX]+)?(?:\s*\([^)]+\))?\s*PS)",
    ]

    for pattern in voltage_substation_patterns:
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            voltage = int(match.group(1))
            substation = match.group(2).strip()
            substation = re.sub(r"\s*\([Ss]ec[^)]*\)", "", substation).strip()
            return voltage, substation

    voltage_match = re.search(r"(\d+)\s*kV", search_text, re.IGNORECASE)
    if voltage_match:
        return int(voltage_match.group(1)), None

    return None, None
