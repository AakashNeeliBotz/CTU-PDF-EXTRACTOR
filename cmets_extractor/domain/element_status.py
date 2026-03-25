from __future__ import annotations

import hashlib
import os
import re

import fitz
import pandas as pd
import pdfplumber

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

from cmets_extractor.domain.common.text import clean_text, dedupe_preserve_order
from cmets_extractor.domain.deliberation import extract_deliberation_text_for_pdf


ELEMENT_STATUS_SRC_COLS_MAP = {
    "Scope": ["Name", "Scope"],
    "SPV": ["SPV", "Transfe"],
    "Locs": ["Total", "Locs"],
    "Found": ["Found", "ation", "Nos"],
    "Erect": ["Erecti", "on", "Nos"],
    "String": ["Stringin", "g"],
    "Civil": ["Civil", "works"],
    "EqptRec": ["Eqpt", "Receive"],
    "EqptEre": ["Eqpt", "Erectio"],
    "OrgSCOD": [
        ["Target", "Org"],
        ["Target", "Orig"],
        ["Completion", "Origina"],
    ],
    "AntSCOD": ["Target", "Anticipate"],
    "Remarks": ["Remarks"],
    "Length": ["Lengt", "h"],
    "AwardedTo": ["Exec", "Agenc"],
    "MVA": ["MVA"],
    "Mode": ["Impl", "Mode"],
}

ELEMENT_STATUS_MAPPING_RULES = {
    3: "InterIntra",
    4: "Scheme",
    6: "MVA",
    9: "Mode",
    15: "AwardedTo",
    16: "SPV",
    17: "Length",
    18: "Locs",
    19: "Found",
    20: "Erect",
    21: "String",
    22: "CALC_FOUND",
    23: "CALC_ERECT",
    24: "CALC_STRING",
    25: "Civil",
    26: "EqptRec",
    27: "EqptEre",
    28: "OrgSCOD",
    29: "AntSCOD",
    30: "Remarks",
    2: "ElementCode",
}


def normalize_annexure_label(token):
    """Normalize annexure token into canonical key form: ANNEXURE-II."""
    if not token:
        return None
    cleaned = re.sub(r"[^A-Za-z0-9]", "", str(token)).upper()
    if not cleaned:
        return None
    return f"ANNEXURE-{cleaned}"


def normalize_cmets_element_text(text):
    """Normalize one CMETS transmission element text for stable matching/coding."""
    if not text:
        return None
    value = str(text).replace("\n", " ")
    value = re.sub(r"\s+", " ", value).strip()
    value = re.split(r"\bMinutes\s+of\b", value, maxsplit=1, flags=re.IGNORECASE)[0].strip()
    value = re.split(r"\bPage\s*\|", value, maxsplit=1, flags=re.IGNORECASE)[0].strip()
    value = re.split(r"\bSl\.?\s*No\.?\b", value, maxsplit=1, flags=re.IGNORECASE)[0].strip()
    value = re.sub(r"^[\-–•]+\s*", "", value).strip()
    value = re.sub(r"^\(?[ivxlcdm]+\)?\s*[\.\)]\s*\.?\s*", "", value, flags=re.IGNORECASE).strip()
    value = re.sub(r"^\d+\s*[\.\)]\s*", "", value).strip()
    value = re.sub(
        r"\s*[-–]\s*Under\s+Applicant\s+Scope\s*$",
        " - Under Applicant Scope",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(
        r"\s*[-–]\s*Under\s+the\s+scope\s+of\s+ISTS\s*$",
        " - Under the scope of ISTS",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(
        r"(?:\s*[-–]\s*Under\s+the\s+scope\s+of\s+ISTS){2,}\s*$",
        " - Under the scope of ISTS",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(
        r"Under\s+the\s+scope\s+of\s+ISTS\s+[-–]\s+Under\s+the\s+scope\s+of\s+ISTS",
        "Under the scope of ISTS",
        value,
        flags=re.IGNORECASE,
    )
    value = value.strip(" .;:")
    return value or None


def is_valid_cmets_element_text(text):
    """Return True when text looks like an actual CMETS transmission element."""
    if not text:
        return False
    low = str(text).strip().lower()
    if not low:
        return False
    if low in {"nil", "nill", "na", "n/a", "none"}:
        return False
    if low.startswith("as per annexure"):
        return False
    if re.fullmatch(r"annexure[-\s]*[a-z0-9]+", low):
        return False
    if low.startswith("details of transmission system for connectivity under gna"):
        return False
    if len(low) > 700:
        return False
    if len(low.split()) > 85:
        return False
    if re.search(r"\bapplication\s+no\b|\bsl\.?\s*no\b|page\s*\|", low):
        return False
    if re.search(r"\bconn\s*bg\d?\b|loa\s+or\s+ppa", low):
        return False
    narrative_patterns = [
        r"it\s+was\s+informed",
        r"it\s+was\s+proposed",
        r"accordingly",
        r"same\s+was\s+noted",
        r"agreed\s+for\s+the\s+same",
        r"asked\s+to\s+submit",
        r"shall\s+be\s+informed",
        r"joint\s+study\s+meeting",
        r"committee\s+meeting",
        r"has\s+applied\s+for\s+connectivity",
    ]
    for pattern in narrative_patterns:
        if re.search(pattern, low):
            return False
    asset_keywords = [
        "line",
        "bay",
        "reactor",
        "ict",
        "transformer",
        "substation",
        "s/s",
        "terminal station",
        "hvdc",
        "ehvac",
        "pooling station",
        "system strengthening",
        "lilo",
        "upgradation",
        "augmentation",
        "switchyard",
        "bus reactor",
        "associated transmission system",
        "transmission system",
        "dispersal of power",
    ]
    if not any(keyword in low for keyword in asset_keywords):
        return False
    return True


def split_numbered_elements(text):
    """Split text into numbered/roman-list elements when list markers are present."""
    if not text:
        return []
    normalized = re.sub(r"\s+", " ", str(text)).strip()
    pattern = r"(?:(?<=\s)|^)(?:\(?[ivxlcdm]+\)?|\d+)\s*[\.\)]\s*\.?\s*"
    matches = list(re.finditer(pattern, normalized, flags=re.IGNORECASE))
    if not matches:
        return []

    parts = []
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(normalized)
        part = normalized[start:end].strip(" .;:-")
        if part:
            parts.append(part)
    return parts


def extract_section_text(text, start_patterns, end_patterns):
    """Extract one section block using flexible start/end markers."""
    if not text:
        return ""

    start_match = None
    for pattern in start_patterns:
        start_match = re.search(pattern, text, re.IGNORECASE)
        if start_match:
            break
    if not start_match:
        return ""

    start = start_match.end()
    tail = text[start:]
    end = len(text)
    for pattern in end_patterns:
        match = re.search(pattern, tail, re.IGNORECASE)
        if match:
            candidate = start + match.start()
            if candidate < end:
                end = candidate
    return text[start:end].strip()


def parse_annexure_elements_from_block(block_text):
    """Parse numbered CTS elements from one annexure text block."""
    if not block_text:
        return []

    elements = []
    current = None
    pending_numbered_item = False
    lines = [re.sub(r"\s+", " ", line).strip() for line in str(block_text).splitlines()]

    def flush_current():
        nonlocal current
        if not current:
            return
        norm = normalize_cmets_element_text(current)
        if is_valid_cmets_element_text(norm):
            elements.append(norm)
        current = None

    for line in lines:
        if not line:
            continue
        if re.search(r"^Annexure\s*[-–]?\s*[A-Za-z0-9]+\b", line, re.IGNORECASE):
            continue
        if re.search(r"^\s*Minutes\s+of\s+", line, re.IGNORECASE):
            continue
        if re.search(r"^\s*Page\s*\|", line, re.IGNORECASE):
            continue
        if re.search(
            r"^Transmission\s+system\s+for\s+Connectivity\s+under\s+GNA",
            line,
            re.IGNORECASE,
        ):
            continue

        if re.match(r"^\s*\d+\s*[\.\)]\s*$", line):
            flush_current()
            pending_numbered_item = True
            continue

        item_match = re.match(r"^\s*\d+\s*[\.\)]\s*(.+)$", line)
        if item_match:
            flush_current()
            current = item_match.group(1).strip()
            pending_numbered_item = False
            continue

        if pending_numbered_item:
            current = line
            pending_numbered_item = False
            continue

        if current:
            if (
                re.search(
                    r"(transmission\s+system\s+for\s+connectivity|additional\s+system\s+for\s+connectivity)",
                    line,
                    re.IGNORECASE,
                )
                or line.endswith(":")
            ):
                flush_current()
                continue
            current = f"{current} {line}".strip()

    flush_current()
    return dedupe_preserve_order(elements)


def parse_annexure_elements_from_pdf(pdf_path):
    """Extract annexure -> CTS element list mapping from one CMETS PDF."""
    lookup = {}
    if not os.path.exists(pdf_path):
        return lookup

    try:
        doc = fitz.open(pdf_path)
    except Exception:
        return lookup

    current_annexure = None
    for page in doc:
        page_text = page.get_text() or ""
        lines = [
            re.sub(r"\s+", " ", text).strip()
            for text in page_text.splitlines()
            if text and text.strip()
        ]
        if not lines:
            continue

        heading = None
        for line in lines[:12]:
            match = re.match(
                r"^Annexure\s*[-–]?\s*([A-Za-z0-9]+)\b",
                line,
                flags=re.IGNORECASE,
            )
            if match:
                heading = normalize_annexure_label(match.group(1))
                break
        if heading:
            current_annexure = heading
        if not current_annexure:
            continue

        elements = parse_annexure_elements_from_block("\n".join(lines))
        if not elements:
            continue
        existing = lookup.get(current_annexure, [])
        lookup[current_annexure] = dedupe_preserve_order(existing + elements)

    doc.close()
    return lookup


def extract_annexure_refs_from_text(text):
    """Extract referenced annexure keys from one CTS section text."""
    if not text:
        return []
    refs = []
    for token in re.findall(r"Annexure\s*[-–]?\s*([A-Za-z0-9]+)", str(text), flags=re.IGNORECASE):
        label = normalize_annexure_label(token)
        if label:
            refs.append(label)
    return dedupe_preserve_order(refs)


def parse_cmets_section_elements(section_text):
    """Parse ATS/DTL/CTS elements from one section body."""
    if not section_text:
        return []

    text = re.sub(r"\s+", " ", str(section_text)).strip()
    if not text:
        return []
    if re.match(r"^(?:nil|nill|na|n/a|none)\b", text, re.IGNORECASE):
        return []

    parts = split_numbered_elements(text)
    if not parts:
        parts = [part.strip() for part in re.split(r"\s*;\s*", text) if part.strip()]
        if not parts:
            parts = [text]

    result = []
    for part in parts:
        normalized = normalize_cmets_element_text(part)
        if is_valid_cmets_element_text(normalized):
            result.append(normalized)
    return dedupe_preserve_order(result)


def extract_cmets_elements_from_deliberation(text, annexure_lookup=None):
    """
    Extract ATS/DTL/CTS elements from one app deliberation text.
    CTS supports both inline list items and annexure references.
    """
    annexure_lookup = annexure_lookup or {}
    parsed = {"ats": [], "dtl": [], "cts": []}
    if not text:
        return parsed

    normalized = re.sub(r"\s+", " ", str(text)).strip()
    if not normalized:
        return parsed

    ats_text = extract_section_text(
        normalized,
        start_patterns=[r"A\.\s*Associated\s+Transmission\s+System\s*\(ATS\)\s*:?\s*"],
        end_patterns=[
            r"B\.\s*Dedicated\s+Transmission\s+System\s+for\s+Connectivity\s+under\s+GNA\s*:?\s*",
            r"B\.\s*Transmission\s+System\s+under\s+applicant\s+scope\s*:?\s*",
            r"Transmission\s+System\s+under\s+applicant\s+scope\s*:?\s*",
            r"C\.\s*Common\s+Transmission\s+System\s+for\s+Connectivity\s+under\s+GNA\s*:?\s*",
            r"C\.\s*Transmission\s+system\s+for\s+Connectivity\s+under\s+GNA\s*:?\s*",
            r"C\.\s*Transmission\s+System\s+under\s+ISTS\s+scope\s*:?\s*",
        ],
    )
    dtl_text = extract_section_text(
        normalized,
        start_patterns=[
            r"B\.\s*Dedicated\s+Transmission\s+System\s+for\s+Connectivity\s+under\s+GNA\s*:?\s*",
            r"B\.\s*Transmission\s+System\s+under\s+applicant\s+scope\s*:?\s*",
            r"Transmission\s+System\s+under\s+applicant\s+scope\s*:?\s*",
        ],
        end_patterns=[
            r"C\.\s*Common\s+Transmission\s+System\s+for\s+Connectivity\s+under\s+GNA\s*:?\s*",
            r"C\.\s*Transmission\s+system\s+for\s+Connectivity\s+under\s+GNA\s*:?\s*",
            r"Transmission\s+system\s+for\s+Connectivity\s+under\s+GNA\s*:?\s*",
            r"C\.\s*Transmission\s+System\s+under\s+ISTS\s+scope\s*:?\s*",
            r"Transmission\s+System\s+under\s+ISTS\s+scope\s*:?\s*",
            r"Start\s+Date\s+of\s+Connectivity\s+under\s+GNA",
        ],
    )
    cts_text = extract_section_text(
        normalized,
        start_patterns=[
            r"C\.\s*Common\s+Transmission\s+System\s+for\s+Connectivity\s+under\s+GNA\s*:?\s*",
            r"C\.\s*Transmission\s+system\s+for\s+Connectivity\s+under\s+GNA\s*:?\s*",
            r"Transmission\s+system\s+for\s+Connectivity\s+under\s+GNA\s*:?\s*",
            r"C\.\s*Transmission\s+System\s+under\s+ISTS\s+scope\s*:?\s*",
            r"Transmission\s+System\s+under\s+ISTS\s+scope\s*:?\s*",
        ],
        end_patterns=[
            r"Start\s+Date\s+of\s+Connectivity\s+under\s+GNA",
            r"Accordingly",
        ],
    )

    parsed["ats"] = parse_cmets_section_elements(ats_text)
    parsed["dtl"] = parse_cmets_section_elements(dtl_text)
    parsed["cts"] = parse_cmets_section_elements(cts_text)

    annexure_refs = extract_annexure_refs_from_text(cts_text)
    if annexure_refs:
        parsed["cts"] = []
    for ref in annexure_refs:
        parsed["cts"].extend(annexure_lookup.get(ref, []))
    parsed["cts"] = dedupe_preserve_order(
        [
            value
            for value in (normalize_cmets_element_text(item) for item in parsed["cts"])
            if is_valid_cmets_element_text(value)
        ]
    )
    return parsed


def extract_dedicated_transmission_elements(text):
    """
    Parse DTL-like inline elements from narrative text when A/B/C sections are absent.
    Useful for rows that only mention one dedicated line in free-form text.
    """
    if not text:
        return []
    normalized = re.sub(r"\s+", " ", str(text)).strip()
    if not normalized:
        return []

    candidates = []
    patterns = [
        r"dedicated\s+transmission\s+system\s+of\s+([^.;\n]{5,260})",
        r"through\s+already\s+allocated\s+dedicated\s+transmission\s+system\s+of\s+([^.;\n]{5,260})",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, normalized, re.IGNORECASE):
            value = normalize_cmets_element_text(match.group(1))
            if is_valid_cmets_element_text(value):
                candidates.append(value)
    return dedupe_preserve_order(candidates)


def extract_cmets_elements_from_named_pdf_context(pdf_path, applicant_name, annexure_lookup=None):
    """Recover CMETS ATS/DTL/CTS elements by searching another meeting PDF for the applicant name."""
    parsed = {"ats": [], "dtl": [], "cts": []}
    if not pdf_path or not applicant_name or not os.path.exists(pdf_path):
        return parsed

    deliberation_dict, full_text = extract_deliberation_text_for_pdf(
        pdf_path,
        start_page=1,
        end_page=None,
    )
    normalized_full_text = re.sub(r"\s+", " ", full_text) if full_text else ""
    applicant_key = clean_text(applicant_name)
    if not normalized_full_text or not applicant_key:
        return parsed

    best_score = -1
    for match in re.finditer(re.escape(applicant_key), normalized_full_text, re.IGNORECASE):
        start = max(0, match.start() - 2500)
        end = min(len(normalized_full_text), match.end() + 10000)
        window = normalized_full_text[start:end]
        candidate = extract_cmets_elements_from_deliberation(
            window,
            annexure_lookup=annexure_lookup,
        )
        score = (
            10 * len(candidate.get("cts", []))
            + 5 * len(candidate.get("dtl", []))
            + len(candidate.get("ats", []))
        )
        if score > best_score:
            parsed = candidate
            best_score = score

    return parsed


def es_clean_text(value):
    """Normalize text for matching in Element Status logic."""
    if value is None or pd.isna(value):
        return None
    text = str(value).strip().replace("\n", " ").replace("\r", " ").replace("\t", " ")
    text = text.replace("û", "-").replace("–", "-").replace("—", "-")
    text = re.sub(r"\s+", " ", text).strip()
    return text.lower()


def es_to_float(value):
    """Safe float conversion helper."""
    try:
        return float(value) if value is not None and not pd.isna(value) else 0.0
    except Exception:
        return 0.0


def es_is_number(value):
    """Check whether a string can be converted to a numeric value."""
    if not isinstance(value, str):
        return False, None
    token = value.strip()
    if not token:
        return False, None
    try:
        if token.isdigit():
            return True, int(token)
        if re.match(r"^-?\d+(\.\d+)?$", token):
            num = float(token)
            if num.is_integer():
                return True, int(num)
            return True, num
    except Exception:
        pass
    return False, None


def es_find_col(df, keywords):
    """Find source column by checking keyword fragments in header text."""
    keyword_groups = keywords
    if not any(isinstance(item, (list, tuple, set)) for item in keywords):
        keyword_groups = [keywords]

    for col in df.columns:
        col_text = str(col).lower()
        for group in keyword_groups:
            if all(str(item).lower() in col_text for item in group):
                return col
    return None


def es_scope_token_key(value):
    """Convert one scope identity string into a compact lowercase token key."""
    if not value:
        return None
    token = re.sub(r"[^a-z0-9]", "", str(value).lower())
    return token or None


def es_normalize_scope_identity_text(text):
    """Normalize one transmission-scope string for semantic dedupe."""
    if not text:
        return None
    value = normalize_cmets_element_text(text) or str(text)
    value = es_normalize_nct_text(value)

    replacements = (
        (r"\bsub[- ]?station\b", " ps"),
        (r"\bs\s*/\s*s\b", " ps"),
        (r"\bs/s\b", " ps"),
        (r"\bpooling station\b", " ps"),
        (r"\bpooling ss\b", " ps"),
        (r"\bdouble\s+circuit\b", " dc"),
        (r"\bd\s*/\s*c\b", " dc"),
        (r"\bsingle\s+circuit\b", " sc"),
        (r"\bs\s*/\s*c\b", " sc"),
        (r"\brishabdeo\b", "rishabhdeo"),
    )
    for pattern, replacement in replacements:
        value = re.sub(pattern, replacement, value, flags=re.IGNORECASE)

    value = re.sub(r"\bat a suitable location near\b", " near ", value, flags=re.IGNORECASE)
    value = re.sub(r"\bat suitable location near\b", " near ", value, flags=re.IGNORECASE)
    value = re.sub(r"\bat a suitable location\b", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"\bat suitable location\b", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"\s+", " ", value).strip(" -,:;")
    return value or None


def es_strip_optional_line_tail(text):
    """Drop reactor-attachment wording from line scopes when it follows the same base line."""
    normalized = es_normalize_scope_identity_text(text)
    if not normalized:
        return None
    if (
        re.search(r"\bline\b", normalized, flags=re.IGNORECASE)
        and re.search(r"\balong with\b", normalized, flags=re.IGNORECASE)
        and re.search(r"\breactor\b", normalized, flags=re.IGNORECASE)
    ):
        trimmed = re.split(r"\balong with\b", normalized, maxsplit=1, flags=re.IGNORECASE)[0]
        trimmed = trimmed.strip(" -,:;")
        if trimmed:
            return trimmed
    return normalized


def es_normalize_establishment_station_token(value):
    """Normalize extracted station/location fragments used in establishment dedupe."""
    if not value:
        return None
    text = es_normalize_scope_identity_text(value)
    if not text:
        return None
    text = re.sub(r"\b(?:at|near|a|an|the|suitable|location)\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bps\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip(" -,:;")
    return es_scope_token_key(text)


def es_establishment_identity_key(text):
    """Create a broader identity key for one-time establishment scopes."""
    normalized = es_normalize_scope_identity_text(text)
    if not normalized or not re.match(r"^establishment of\b", normalized, flags=re.IGNORECASE):
        return None

    mw_values = re.findall(r"(\d+(?:\.\d+)?)\s*mw\b", normalized, flags=re.IGNORECASE)
    lead_mw = mw_values[0].rstrip("0").rstrip(".") if mw_values else None
    station_terms = []

    patterns = (
        r"\b([A-Za-z0-9()/-]+(?:\s+[A-Za-z0-9()/-]+){0,4})\s+terminal station\b",
        r"\bnear\s+([A-Za-z0-9()/-]+(?:\s+[A-Za-z0-9()/-]+){0,4})\s+ps\b",
        r"\b([A-Za-z0-9()/-]+(?:\s+[A-Za-z0-9()/-]+){0,4})\s+ps\b",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, normalized, flags=re.IGNORECASE):
            station_token = es_normalize_establishment_station_token(match.group(1))
            if station_token:
                station_terms.append(station_token)

    station_terms = dedupe_preserve_order(station_terms)
    if not station_terms and not lead_mw:
        return None

    key_parts = ["establishment"]
    if lead_mw:
        key_parts.append(lead_mw)
    key_parts.extend(station_terms[:3])
    return "|".join(key_parts)


def es_scope_match_keys(scope_text, source_label=None):
    """Return ordered semantic-match keys for one transmission scope."""
    normalized = es_normalize_scope_identity_text(scope_text)
    if not normalized:
        return []

    keys = []
    establishment_key = es_establishment_identity_key(normalized)
    if establishment_key:
        keys.append(establishment_key)

    line_core = es_strip_optional_line_tail(normalized)
    line_core_key = es_scope_token_key(line_core)
    if line_core_key:
        keys.append(line_core_key)

    exact_key = es_scope_token_key(normalized)
    if exact_key:
        keys.append(exact_key)

    return dedupe_preserve_order(key for key in keys if key)


def es_primary_scope_identity(scope_text, source_label=None):
    """Return the primary stable identity token used for codes and catalog keys."""
    match_keys = es_scope_match_keys(scope_text, source_label=source_label)
    return match_keys[0] if match_keys else None


def es_generate_unique_code(element_name, source_label=None):
    """Generate stable 5-char hash code for one semantic element identity."""
    identity = es_primary_scope_identity(element_name, source_label=source_label)
    if not identity:
        return None
    hash_str = hashlib.md5(identity.encode()).hexdigest()[:5].upper()
    return f"EL-{hash_str}"


def es_find_existing_scope_row(match_keys, code_key, index_by_full, index_by_scope):
    """Resolve the first existing sheet row for one scope across all alias keys."""
    if code_key:
        for match_key in match_keys:
            row_num = index_by_full.get((match_key, code_key))
            if row_num is not None:
                return row_num
    for match_key in match_keys:
        row_num = index_by_scope.get(match_key)
        if row_num is not None:
            return row_num
    return None


def es_register_scope_row_keys(match_keys, code_key, row_num, index_by_full, index_by_scope):
    """Register all alias keys for one written Element Status row."""
    for match_key in match_keys:
        if code_key and (match_key, code_key) not in index_by_full:
            index_by_full[(match_key, code_key)] = row_num
        if match_key not in index_by_scope:
            index_by_scope[match_key] = row_num


def es_normalize_awarded_to(value):
    """Keep awarded-agency labels consistent in the workbook."""
    if value is None or pd.isna(value):
        return value
    text = es_normalize_nct_text(value)
    if not text:
        return None
    if re.search(r"\bpower\s*grid\b|\bpowergrid\b|\bpgcil\b", text, flags=re.IGNORECASE):
        return "PGCIL"
    return text


def es_normalize_state_labels(value):
    """Canonicalize state abbreviations used in Element Status fields."""
    if value is None or pd.isna(value):
        return value

    text = str(value).strip()
    if not text:
        return text

    replacements = {
        r"\bmp\b": "Madhya Pradesh",
        r"\bm\.p\.\b": "Madhya Pradesh",
    }
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    return re.sub(r"\s+", " ", text).strip()


def es_extract_scheme_details(text):
    """
    Extract (Inter/Intra, Scheme) context from parent scope rows.
    Returns ("", "") when no region context is detected.
    """
    if not text:
        return None, None

    text = text.replace("\n", " ").strip()

    text = re.sub(r"\s*\(?SPV\s*[:].*?(?:\)|$)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*,\s*SPV.*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*\(SPV.*?\)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*\([\d\.]+\s*GW\)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*\(CKM.*?\)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\(Part\s*[-–]?\s*\d+\s*:.*?\)", "", text, flags=re.IGNORECASE)

    regions_list = [
        "Rajasthan REZ",
        "Gujarat REZ",
        "Khavda RE Park",
        "Khavda",
        "Rajasthan",
        "Gujarat",
        "Madhya Pradesh",
        "MP",
        "M.P.",
        "Karnataka",
        "Tamil Nadu",
        "TN",
        "Andhra",
        "Telangana",
        "Ananthapuram",
        "Kurnool",
        "Bhadla",
        "Sikar",
        "Fatehgarh",
        "Kadeoni",
        "Koppal",
        "Gadag",
        "Bidar",
        "Rajnandgaon",
        "Kallam",
        "KPS[0-9]*",
        "KPS",
        "Bikaner Complex",
        "Bikaner",
    ]
    regions_list.sort(key=len, reverse=True)
    region_pattern = r"(" + "|".join([re.escape(region) for region in regions_list]) + r")(?:[- ]?[IVX]+)?"

    part_of_match = re.search(
        r"as part of\s+(.*?Scheme|.*?REZ(?: Phase[- ]?[IVX]*)?)",
        text,
        re.IGNORECASE,
    )
    if part_of_match:
        region_match = re.search(region_pattern, part_of_match.group(1), re.IGNORECASE)
    else:
        region_match = re.search(region_pattern, text, re.IGNORECASE)

    region = region_match.group(1) if region_match else None
    if region:
        region = es_normalize_state_labels(region)
        if "KPS" in region.upper():
            region = region.upper()

    if not region:
        return "", ""

    text = re.sub(r"REZPhase", "Phase", text, flags=re.IGNORECASE)
    phase_match = re.search(r"((?:Phase|Ph)\s*[-–]?\s*[IVX0-9]+)", text, re.IGNORECASE)
    phase = phase_match.group(1) if phase_match else ""
    phase = re.sub(r"Ph\s*[-–]", "Phase-", phase, flags=re.IGNORECASE)
    phase = re.sub(r"\s*[-–]\s*", "-", phase)
    phase = re.sub(r"\s+", " ", phase)

    parts_candidates = re.finditer(
        r"(Part(?!\s+of\b)\s*[-–]?\s*[A-Z0-9]+(?:[\s,&]+[A-Z0-9]+)*)",
        text,
        re.IGNORECASE,
    )
    clean_parts = []
    for item in parts_candidates:
        value = item.group(1)
        value = re.sub(r"\s*[-–]\s*", " ", value)
        clean_parts.append(value)

    parts_paren = re.findall(r"(\(Part\s*[-–]?\s*\d+\))", text, re.IGNORECASE)
    final_parts = []
    for part in parts_paren:
        final_parts.append(part)
    for candidate in clean_parts:
        candidate_norm = re.sub(r"\s", "", candidate).lower()
        is_duplicate = False
        for part in parts_paren:
            part_norm = re.sub(r"[\(\)\-\s]", "", part).lower()
            if candidate_norm in part_norm:
                is_duplicate = True
                break
        if not is_duplicate:
            final_parts.append(candidate)

    part_str = " ".join(final_parts).strip()

    scheme_parts = [region]
    if phase:
        scheme_parts.append(phase)
    if part_str:
        scheme_parts.append(part_str)

    scheme = " ".join(scheme_parts).strip()
    inter_intra = f"{region} {phase}".strip()
    scheme = es_normalize_state_labels(re.sub(r"\s+", " ", scheme))
    inter_intra = es_normalize_state_labels(re.sub(r"\s+", " ", inter_intra))
    return inter_intra, scheme


def es_normalize_nct_text(text):
    """Normalize extracted NCT text while preserving readable scope labels."""
    if not text:
        return ""

    value = str(text)
    replacements = {
        "\xa0": " ",
        "•": " ",
        "": " ",
        "●": " ",
        "▪": " ",
        "–": "-",
        "—": "-",
        "−": "-",
        "“": '"',
        "”": '"',
        "’": "'",
    }
    for source, target in replacements.items():
        value = value.replace(source, target)

    value = value.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r"(?<=\d)\s*\.\s*", ".", value)
    value = re.sub(r"\s+([,.;:)])", r"\1", value)
    value = re.sub(r"([(])\s+", r"\1", value)
    value = re.sub(r"\s*-\s*", "-", value)
    return value.strip(" -")


def es_join_nct_fragments(fragments):
    """Join positioned text fragments from one NCT table line."""
    return es_normalize_nct_text(" ".join(str(fragment) for fragment in fragments if fragment))


def es_nct_scope_key(text):
    """Dedupe NCT elements by normalized transmission-scope text only."""
    return es_primary_scope_identity(text, source_label="NCT")


def es_build_nct_page_lines(page, y_tolerance=7.0):
    """Extract page text with x/y coordinates and group it into top-to-bottom lines."""
    items = []

    def visitor(text, cm, tm, font_dict, font_size):
        x = tm[4]
        y = tm[5]
        if text and text.strip():
            items.append((float(x), float(y), text))

    page.extract_text(visitor_text=visitor)
    items.sort(key=lambda item: (-item[1], item[0]))

    lines = []
    for x, y, text in items:
        if not lines or abs(lines[-1]["y"] - y) > y_tolerance:
            lines.append({"y": y, "chunks": [(x, text)]})
        else:
            lines[-1]["chunks"].append((x, text))

    for line in lines:
        line["chunks"].sort(key=lambda item: item[0])
        line["text"] = es_join_nct_fragments(chunk_text for _, chunk_text in line["chunks"])

    return lines


def es_detect_nct_table_kind(header_source):
    """Detect which NCT table schema is present in one header line or page-line list."""
    if isinstance(header_source, list):
        for line in header_source:
            kind = es_detect_nct_table_kind(line.get("text", ""))
            if kind:
                return kind
        return None

    header_text = str(header_source).lower()
    if (
        "scope of the transmission" in header_text
        and "original" in header_text
        and "revised" in header_text
    ):
        return "scope_original_revised"
    if (
        "scope of the transmission" in header_text
        and "capacity" in header_text
        and "estimated" in header_text
        and "implementation" in header_text
    ):
        return "scope_capacity_cost"
    if (
        "scope of the transmission" in header_text
        and "capacity /km" in header_text
        and "remarks" in header_text
    ):
        return "scope_capacity_remarks"
    if "scope of the transmission" in header_text and "capacity /km" in header_text:
        return "scope_capacity"
    return None


def es_is_nct_header_line(text):
    """Identify table-header lines so they can be skipped during row parsing."""
    if not text:
        return False
    lower = text.lower()
    return (
        lower.startswith("sl.")
        or lower.startswith("sl no")
        or lower.startswith("sl.no")
        or lower == "no."
        or lower == "scheme"
        or "scope of the transmission" in lower
        or "original scope of the" in lower
        or "revised scope of the" in lower
        or "capacity /km" in lower
        or ("capacity" in lower and "estimated" in lower and "implementation" in lower)
        or lower == "transmission scheme"
    )


def es_nct_column_bounds(table_kind):
    """Hard-coded column bands for the current 35th NCT PDF layouts."""
    if table_kind == "scope_original_revised":
        return {
            "serial_end": 100,
            "scope_start": 100,
            "scope_end": 255,
        }
    if table_kind == "scope_capacity_remarks":
        return {
            "serial_end": 95,
            "scope_start": 95,
            "scope_end": 250,
            "capacity_start": 250,
            "capacity_end": 430,
            "remarks_start": 430,
        }
    if table_kind == "scope_capacity_cost":
        return {
            "serial_end": 120,
            "scope_start": 120,
            "scope_end": 260,
            "capacity_start": 260,
            "capacity_end": 375,
        }
    return {
        "serial_end": 95,
        "scope_start": 95,
        "scope_end": 320,
        "capacity_start": 320,
    }


def es_split_nct_line_columns(line, table_kind):
    """Split one positioned NCT line into the columns relevant to extraction."""
    bounds = es_nct_column_bounds(table_kind)
    columns = {
        "serial": [],
        "scope": [],
        "capacity": [],
        "remarks": [],
    }

    for x, text in line.get("chunks", []):
        if x < bounds["serial_end"]:
            columns["serial"].append(text)
            continue
        if bounds["scope_start"] <= x < bounds["scope_end"]:
            columns["scope"].append(text)
            continue

        if table_kind == "scope_original_revised":
            continue

        if table_kind == "scope_capacity_remarks":
            if bounds["capacity_start"] <= x < bounds["capacity_end"]:
                columns["capacity"].append(text)
            elif x >= bounds["remarks_start"]:
                columns["remarks"].append(text)
            continue

        if x >= bounds["capacity_start"]:
            if table_kind == "scope_capacity_cost" and x >= bounds["capacity_end"]:
                continue
            columns["capacity"].append(text)

    return {key: es_join_nct_fragments(value) for key, value in columns.items()}


def es_is_nct_table_terminator(line_text):
    """Detect narrative lines that mark the end of the current NCT table."""
    if not line_text:
        return False
    lower = line_text.lower()
    return (
        lower.startswith("note:")
        or lower.startswith("annexure-")
        or "list of participants" in lower
        or "summary of the deliberations" in lower
        or lower.startswith("total (rs")
        or re.match(r"^\d+\.\d+(?:\.\d+)?\b", lower) is not None
        or re.match(r"^[ivxlcdm]+\.", lower) is not None
    )


def es_clean_nct_scope(scope_text):
    """Keep only the primary transmission element name from the NCT scope column."""
    if not scope_text:
        return None

    cleaned = es_normalize_nct_text(scope_text)
    cut_patterns = (
        r"future space provisions\s*:",
        r"additional space for future expansion\s*:",
        r"additional space for future expansion\b",
        r"additional space for future\b",
    )
    for pattern in cut_patterns:
        match = re.search(pattern, cleaned, flags=re.IGNORECASE)
        if match:
            cleaned = cleaned[:match.start()]
            break

    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -,:;")
    return cleaned or None


def es_calculate_nct_mva(scope_text):
    """Sum base MVA capacities from the cleaned NCT scope text."""
    if not scope_text:
        return None

    text = es_clean_nct_scope(scope_text)
    if not text:
        return None

    text = re.sub(r"\([^)]*single\s+phase\s+units?[^)]*\)", "", text, flags=re.IGNORECASE)
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*MVA\b", text, flags=re.IGNORECASE)
    if not matches:
        return None

    total = sum(float(multiplier) * float(mva) for multiplier, mva in matches)
    return int(total) if float(total).is_integer() else round(total, 2)


def es_nct_circuit_multiplier(scope_text):
    """Map line descriptors to the required circuit multiplier."""
    text = (scope_text or "").lower()
    has_quad = "quad" in text
    has_dc = (
        re.search(r"\bd\s*/\s*c\b", text) is not None
        or re.search(r"\bdouble\s+circuit\b", text) is not None
    )
    if has_quad and has_dc:
        return 2
    if has_quad:
        return 4
    if has_dc:
        return 2
    return 1


def es_calculate_nct_length(scope_text, capacity_text=None):
    """Extract km values and apply D/c or quad multipliers from the scope text."""
    for source_text in (capacity_text, scope_text):
        if not source_text:
            continue
        km_values = re.findall(r"(\d+(?:\.\d+)?)\s*km\b", source_text, flags=re.IGNORECASE)
        if not km_values:
            continue
        base_length = sum(float(value) for value in km_values)
        total_length = base_length * es_nct_circuit_multiplier(scope_text or source_text)
        return int(total_length) if float(total_length).is_integer() else round(total_length, 2)
    return None


def es_nct_inter_from_scheme_label(scheme_label):
    """Remove phase/part suffixes for the Inter/Intra column."""
    if not scheme_label:
        return None

    value = es_normalize_nct_text(scheme_label)
    value = re.sub(r"\s+Phase[- ]?[IVX0-9]+\b", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\s*-?Part\s*[A-Z0-9]+\b", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\s+", " ", value).strip(" -")
    return value or None


def es_normalize_nct_context_labels(inter_intra, scheme):
    """Apply the requested workbook labels for known NCT scheme contexts."""
    inter_value = es_normalize_nct_text(inter_intra) if inter_intra else inter_intra
    scheme_value = es_normalize_nct_text(scheme) if scheme else scheme

    if inter_value and inter_value.lower() == "tumkur-ii":
        inter_value = "Augmentation of Tumkur-II"
    if scheme_value and scheme_value.lower() == "tumkur-ii":
        scheme_value = "Augmentation of Tumkur-II"

    if inter_value and inter_value.upper() == "WR-ER":
        inter_value = "WR-ER Inter Regional Network"
    if scheme_value and re.fullmatch(r"WR-ER\s*-?\s*Part\s*A", scheme_value, flags=re.IGNORECASE):
        scheme_value = "WR-ER Inter-Regional Network Expansion - Part A"

    return inter_value, scheme_value


def es_nct_mode_from_remarks(remarks):
    """Use remarks-driven mode when the NCT minutes explicitly name one."""
    text = es_normalize_nct_text(remarks)
    if not text:
        return "NCT"
    if re.search(r"\brtm\b", text, flags=re.IGNORECASE):
        return "RTM"
    if re.search(r"\btbcb\b", text, flags=re.IGNORECASE):
        return "TBCB"
    return "NCT"


def es_nct_awarded_to_from_remarks(remarks):
    """Extract awarded agency from remarks where the NCT tables mention one."""
    text = es_normalize_nct_text(remarks)
    if not text:
        return None
    if re.search(r"\bpower\s*grid\b|\bpowergrid\b|\bpgcil\b", text, flags=re.IGNORECASE):
        return "PGCIL"
    return None


def es_apply_nct_scope_overrides(scope, mode_value, awarded_to):
    """Apply verified NCT workbook overrides for scope-specific metadata."""
    normalized_scope = es_normalize_nct_text(scope).lower()
    if (
        "conversion of 765 kv bus reactor bays to 765 kv slr line bays" in normalized_scope
        and "raichur new" in normalized_scope
    ):
        return "RTM", "PGCIL"
    return mode_value, awarded_to


def es_compact_nct_scheme_label(raw_text):
    """Compact a verbose NCT heading/title into the Scheme field requested by the user."""
    if not raw_text:
        return None

    text = es_normalize_nct_text(raw_text)
    if not text:
        return None

    wr_er_match = re.search(r"\bWR-ER\b.*?\bPart\s*([A-Z0-9]+)\b", text, flags=re.IGNORECASE)
    if wr_er_match:
        return f"WR-ER -Part {wr_er_match.group(1).upper()}"
    if re.search(r"\bWR-ER\b", text, flags=re.IGNORECASE):
        return "WR-ER"

    integration_match = re.search(
        r"transmission\s+(?:system|scheme)\s+for\s+integration\s+of\s+(.+)",
        text,
        flags=re.IGNORECASE,
    )
    if integration_match:
        value = integration_match.group(1)
        value = re.sub(r"\bREZ\b", "", value, flags=re.IGNORECASE)
        value = re.sub(r"\bscheme\b", "", value, flags=re.IGNORECASE)
        return es_normalize_nct_text(value)

    strengthen_match = re.search(
        r"transmission\s+system\s+strengthening\s+at\s+([A-Za-z0-9()/-]+)",
        text,
        flags=re.IGNORECASE,
    )
    if strengthen_match:
        return es_normalize_nct_text(strengthen_match.group(1))

    mundra_match = re.search(
        r"manufacturing\s+potential\s+in\s+(.+?)\s+under\s+(Phase[- ]?[A-Z0-9]+)"
        r"(?:\s*:\s*(Part\s*[A-Z0-9]+))?",
        text,
        flags=re.IGNORECASE,
    )
    if mundra_match:
        location_text = mundra_match.group(1)
        location = (
            "Mundra"
            if re.search(r"\bMundra\b", location_text, flags=re.IGNORECASE)
            else es_normalize_nct_text(location_text)
        )
        phase = es_normalize_nct_text(mundra_match.group(2))
        part = es_normalize_nct_text(mundra_match.group(3)) if mundra_match.group(3) else None
        return " ".join(part_value for part_value in (location, phase, part) if part_value)

    leh_match = re.search(
        r"renewable\s+energy\s+parks\s+in\s+([A-Za-z][A-Za-z0-9() -]+)",
        text,
        flags=re.IGNORECASE,
    )
    if leh_match:
        location_text = leh_match.group(1)
        if re.search(r"\bLeh\b", location_text, flags=re.IGNORECASE):
            return "Leh"
        return es_normalize_nct_text(location_text)

    return es_normalize_nct_text(text)


def es_extract_nct_scheme_context(buffer_text):
    """Resolve Scheme and Inter/Intra context from the heading immediately above NCT tables."""
    if not buffer_text:
        return None, None

    normalized = es_normalize_nct_text(buffer_text)
    lower = normalized.lower()
    labels = []

    quoted_titles = re.findall(r'"([^"]+)"', normalized)
    if "review of transmission scheme" in lower and quoted_titles:
        for title in quoted_titles:
            label = es_compact_nct_scheme_label(title)
            if label:
                labels.append(label)
    elif re.search(r"\bWR-ER\b.*inter-regional network expansion scheme", normalized, flags=re.IGNORECASE):
        label = es_compact_nct_scheme_label(normalized)
        if label:
            labels = [label]
    elif "transmission system strengthening at" in lower:
        label = es_compact_nct_scheme_label(normalized)
        if label:
            labels = [label]
    elif "manufacturing potential in" in lower and "phase" in lower:
        label = es_compact_nct_scheme_label(normalized)
        if label:
            labels = [label]
    elif "renewable energy parks in" in lower:
        label = es_compact_nct_scheme_label(normalized)
        if label:
            labels = [label]

    labels = dedupe_preserve_order(label for label in labels if label)
    if not labels:
        return None, None

    scheme = " & ".join(labels)
    inter_intra = " & ".join(filter(None, (es_nct_inter_from_scheme_label(label) for label in labels)))
    return inter_intra or None, scheme or None


def es_merge_nct_source_rows(existing, new_row):
    """Merge duplicate NCT rows by Transmission Scope, filling missing fields only."""
    if not existing:
        return dict(new_row)

    merged = dict(existing)
    for key in ("InterIntra", "Scheme", "MVA", "Length", "Remarks", "Mode", "AwardedTo", "ElementCode"):
        if not merged.get(key) and new_row.get(key):
            merged[key] = new_row.get(key)
    return merged


def es_collect_nct_rows_from_page_block(
    reader,
    page_numbers,
    inter_intra,
    scheme,
    source_rows,
    forced_kind=None,
    initial_header_skip=0,
):
    """Collect one verified NCT table block into the shared source-row map."""
    active_table_kind = forced_kind
    current_row = None
    first_page = True

    def flush_current_row():
        nonlocal current_row
        if not current_row:
            return

        scope = es_clean_nct_scope(current_row.get("scope"))
        if not scope:
            current_row = None
            return

        scope = re.sub(r"\s+Scheme$", "", scope, flags=re.IGNORECASE).strip()
        scope_key = es_nct_scope_key(scope)
        if not scope_key:
            current_row = None
            return

        remarks = es_normalize_nct_text(current_row.get("remarks")) or None
        if remarks and (
            remarks.lower() == "none"
            or remarks.lower().startswith("none ")
            or re.fullmatch(r"rs\.?\s*\d+(?:\.\d+)?", remarks, flags=re.IGNORECASE)
        ):
            remarks = None

        final_inter_intra, final_scheme = es_normalize_nct_context_labels(inter_intra, scheme)
        awarded_to = es_nct_awarded_to_from_remarks(remarks)
        mode_value = es_nct_mode_from_remarks(remarks)
        mode_value, awarded_to = es_apply_nct_scope_overrides(scope, mode_value, awarded_to)

        output_row = {
            "Scope": scope,
            "InterIntra": final_inter_intra,
            "Scheme": final_scheme,
            "MVA": es_calculate_nct_mva(scope),
            "Length": es_calculate_nct_length(scope, current_row.get("capacity")),
            "Remarks": remarks,
            "Mode": mode_value,
            "AwardedTo": awarded_to,
            "ElementCode": es_generate_unique_code(scope, source_label="NCT"),
        }
        source_rows[scope_key] = es_merge_nct_source_rows(source_rows.get(scope_key), output_row)
        current_row = None

    for page_num in page_numbers:
        page = reader.pages[page_num - 1]
        page_lines = es_build_nct_page_lines(page)
        if not page_lines:
            first_page = False
            continue

        for line_index, line in enumerate(page_lines):
            line_text = line.get("text")
            if not line_text:
                continue

            if first_page and forced_kind and line_index < initial_header_skip:
                continue

            header_kind = es_detect_nct_table_kind(line_text)
            if header_kind and es_is_nct_header_line(line_text):
                if active_table_kind and header_kind != active_table_kind:
                    flush_current_row()
                active_table_kind = header_kind
                continue

            if active_table_kind and es_is_nct_header_line(line_text):
                continue

            if active_table_kind and es_is_nct_table_terminator(line_text):
                flush_current_row()
                active_table_kind = None
                continue

            if not active_table_kind:
                continue

            columns = es_split_nct_line_columns(line, active_table_kind)
            serial_text = columns.get("serial")
            scope_text = columns.get("scope")
            capacity_text = columns.get("capacity")
            remarks_text = columns.get("remarks")

            has_new_row = bool(serial_text and re.fullmatch(r"\d+\.?", serial_text))
            if has_new_row and scope_text:
                flush_current_row()
                current_row = {
                    "scope": scope_text,
                    "capacity": capacity_text or None,
                    "remarks": remarks_text or None,
                }
                continue

            if current_row:
                if scope_text:
                    current_row["scope"] = es_normalize_nct_text(
                        f"{current_row.get('scope', '')} {scope_text}"
                    )
                if capacity_text:
                    current_row["capacity"] = es_normalize_nct_text(
                        f"{current_row.get('capacity', '')} {capacity_text}"
                    )
                if remarks_text:
                    current_row["remarks"] = es_normalize_nct_text(
                        f"{current_row.get('remarks', '')} {remarks_text}"
                    )

        first_page = False

    flush_current_row()


def build_nct_element_status_source_data(pdf_path):
    """Parse 35th NCT minutes tables into Element Status source rows."""
    if PdfReader is None:
        print("  WARNING: pypdf is not available; skipping NCT Element Status extraction.")
        return {}
    if not os.path.exists(pdf_path):
        print(f"  WARNING: NCT PDF not found: {pdf_path}")
        return {}

    print(f"\nExtracting Element Status (NCT) rows from: {os.path.basename(pdf_path)}")
    reader = PdfReader(pdf_path)
    source_rows = {}

    es_collect_nct_rows_from_page_block(
        reader,
        range(4, 8),
        inter_intra="Kurnool-V & Ananthapuram-III",
        scheme="Kurnool-V Phase-I & Ananthapuram-III Phase-I",
        source_rows=source_rows,
    )
    es_collect_nct_rows_from_page_block(
        reader,
        range(9, 11),
        inter_intra="Tumkur-II",
        scheme="Tumkur-II",
        source_rows=source_rows,
    )
    es_collect_nct_rows_from_page_block(
        reader,
        range(31, 38),
        inter_intra="WR-ER",
        scheme="WR-ER -Part A",
        source_rows=source_rows,
        forced_kind="scope_capacity_cost",
        initial_header_skip=3,
    )

    print(f"  NCT source records prepared: {len(source_rows)}")
    return source_rows


def es_table_has_header(table):
    """Detect the standard Element Status table header in an extracted table."""
    if not table:
        return False
    for row in table[:5]:
        row_str = " ".join([str(cell).lower() for cell in row if cell])
        has_sn = any(token in row_str for token in ("sn", "s.n", "sl.no", "sl. no"))
        has_scope = any(token in row_str for token in ("scope", "name", "project", "element"))
        if has_sn and has_scope:
            return True
    return False


def extract_element_status_tables(pdf_path, source_label, target_texts=None):
    """Extract monitoring tables for one Element Status source PDF."""
    print(f"\nExtracting Element Status ({source_label}) tables from: {os.path.basename(pdf_path)}")
    all_tables = []
    started = False
    target_texts = [str(text).lower() for text in (target_texts or []) if text]

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables() or []
            cleaned_tables = []
            for table in tables:
                if not table:
                    continue
                cleaned_table = []
                for row in table:
                    if not row:
                        continue
                    cleaned_row = []
                    for cell in row:
                        if isinstance(cell, str):
                            cleaned_row.append(cell.strip())
                        else:
                            cleaned_row.append(cell)
                    cleaned_table.append(cleaned_row)
                if cleaned_table:
                    cleaned_tables.append(cleaned_table)

            if not started:
                page_text = page.extract_text() or ""
                page_text_lc = page_text.lower()
                if any(target_text in page_text_lc for target_text in target_texts):
                    started = True
                    print(f"  Element Status section found at page {page_num}")
                elif any(es_table_has_header(table) for table in cleaned_tables):
                    started = True
                    print(f"  Element Status table header detected at page {page_num}")

            if not started:
                continue

            all_tables.extend(cleaned_tables)

    print(f"  Extracted raw tables: {len(all_tables)}")
    return all_tables


def merge_tbcb_element_tables(tables):
    """Merge split page tables into one logical table."""
    if not tables:
        return []

    def is_header(row):
        if not row or not row[0]:
            return False
        value = str(row[0]).lower()
        return "sn" in value or "s.n" in value or "sl.no" in value or "sl. no" in value

    start_idx = 0
    start_row_idx = 0
    found_start = False

    for table_index, table in enumerate(tables):
        if not table:
            continue
        for row_index, row in enumerate(table[:5]):
            if es_table_has_header([row]):
                start_idx = table_index
                start_row_idx = row_index
                found_start = True
                break
        if found_start:
            break

    if not found_start:
        print("  WARNING: Could not identify standard TBCB header. Using first extracted table.")

    merged = [row[:] for row in tables[start_idx][start_row_idx:] if row]

    for next_table in tables[start_idx + 1 :]:
        if not next_table:
            continue
        rows_to_add = next_table[1:] if is_header(next_table[0]) else next_table
        for row in rows_to_add:
            if row:
                merged.append(row)
    return merged


def build_element_status_source_data(pdf_path, source_label, target_texts=None):
    """Build normalized source dataset keyed by cleaned transmission scope."""
    raw_tables = extract_element_status_tables(
        pdf_path,
        source_label=source_label,
        target_texts=target_texts,
    )
    merged_data = merge_tbcb_element_tables(raw_tables)
    if not merged_data:
        print(f"  WARNING: No merged {source_label} table data found.")
        return {}, {}

    headers = merged_data[0]
    data_rows = merged_data[1:]
    if not headers or not data_rows:
        print(f"  WARNING: {source_label} table appears empty after merge.")
        return {}, {}

    clean_headers = []
    seen = {}
    for idx, header in enumerate(headers):
        col_name = str(header).strip() if header else f"Col_{idx}"
        if col_name in seen:
            seen[col_name] += 1
            col_name = f"{col_name}_{seen[col_name]}"
        else:
            seen[col_name] = 0
        clean_headers.append(col_name)

    df_src = pd.DataFrame(data_rows, columns=clean_headers)

    src_cols = {}
    for key, keywords in ELEMENT_STATUS_SRC_COLS_MAP.items():
        found_col = es_find_col(df_src, keywords)
        if found_col:
            src_cols[key] = found_col
        else:
            print(f"  WARNING: Missing source column for {key} ({keywords}) in {source_label}")

    scope_col = src_cols.get("Scope")
    if not scope_col:
        print(f"  WARNING: Scope column was not detected in {source_label} table.")
        return {}, {}

    sn_col = es_find_col(df_src, ["SN"]) or es_find_col(df_src, ["S.N"]) or es_find_col(df_src, ["Sl", "No"])
    spv_col = src_cols.get("SPV")

    src_data = {}
    current_context = {
        "InterIntra": None,
        "Scheme": None,
        "SPV": None,
    }

    for _, row in df_src.iterrows():
        is_parent = False
        if sn_col:
            sn_val = row.get(sn_col)
            if sn_val and str(sn_val).strip() and str(sn_val).strip().lower() != "nan":
                is_parent = True

        raw_scope = row.get(scope_col)
        clean_scope = es_clean_text(raw_scope)

        if is_parent:
            inter_intra, scheme = es_extract_scheme_details(str(raw_scope) if raw_scope is not None else "")
            current_context["InterIntra"] = inter_intra
            current_context["Scheme"] = scheme
            if spv_col:
                spv_val = row.get(spv_col)
                if spv_val and str(spv_val).strip():
                    current_context["SPV"] = spv_val
            continue

        if not clean_scope or len(clean_scope) < 3:
            continue

        enriched = row.to_dict()
        enriched["InterIntra"] = current_context["InterIntra"]
        enriched["Scheme"] = current_context["Scheme"]

        if spv_col:
            child_spv = row.get(spv_col)
            if child_spv is None or pd.isna(child_spv) or not str(child_spv).strip():
                enriched[spv_col] = current_context["SPV"]

        enriched["ElementCode"] = es_generate_unique_code(clean_scope, source_label=source_label)
        entry_key = es_primary_scope_identity(clean_scope, source_label=source_label)
        if not entry_key:
            continue

        existing = src_data.get(entry_key)
        if existing is None:
            src_data[entry_key] = enriched
        else:
            for key, value in enriched.items():
                if key == scope_col:
                    continue
                existing_value = existing.get(key)
                if (
                    (existing_value is None or existing_value == "" or pd.isna(existing_value))
                    and value not in (None, "")
                    and not pd.isna(value)
                ):
                    existing[key] = value

    src_cols["ElementCode"] = "ElementCode"
    print(f"  {source_label} source records prepared: {len(src_data)}")
    return src_data, src_cols


def es_rule_value(src_row, src_cols, rule, source_label="TBCB"):
    """Resolve one mapped Element Status value from a source row."""
    if rule.startswith("CALC_"):
        calc_key = rule.split("_", 1)[1]
        if calc_key == "FOUND":
            num_col = src_cols.get("Found")
            den_col = src_cols.get("Locs")
        elif calc_key == "ERECT":
            num_col = src_cols.get("Erect")
            den_col = src_cols.get("Locs")
        elif calc_key == "STRING":
            num_col = src_cols.get("String")
            den_col = src_cols.get("Length")
        else:
            return None

        if not num_col or not den_col:
            return None

        numerator = es_to_float(src_row.get(num_col))
        denominator = es_to_float(src_row.get(den_col))
        if denominator > 0:
            return round(numerator / denominator, 2)
        return None

    if rule == "InterIntra":
        return es_normalize_state_labels(src_row.get("InterIntra"))
    if rule == "Scheme":
        return es_normalize_state_labels(src_row.get("Scheme"))
    if rule == "AwardedTo":
        src_col_name = src_cols.get(rule)
        return es_normalize_awarded_to(src_row.get(src_col_name)) if src_col_name else None

    src_col_name = src_cols.get(rule)
    if src_col_name:
        return src_row.get(src_col_name)
    if rule == "Mode":
        return source_label
    return None


def es_normalize_code(value):
    """Normalize element code token for matching."""
    if value is None or pd.isna(value):
        return None
    text = str(value).strip().upper()
    return text if text else None


def es_source_scope_and_code(src_row, src_cols):
    """Extract raw/normalized scope and code from one source row."""
    scope_col = src_cols.get("Scope")
    code_col = src_cols.get("ElementCode")

    scope_raw = src_row.get(scope_col) if scope_col else None
    match_keys = es_scope_match_keys(scope_raw)
    scope_key = match_keys[0] if match_keys else None

    code_raw = src_row.get(code_col) if code_col else None
    code_key = es_normalize_code(code_raw)
    return scope_raw, scope_key, code_key, match_keys
