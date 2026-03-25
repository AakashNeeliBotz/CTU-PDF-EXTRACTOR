from __future__ import annotations

from datetime import datetime
import re

from cmets_extractor.domain.common.text import clean_text


def parse_date(date_str):
    """Parse date string to datetime object for comparison."""
    if not date_str:
        return None
    date_str = date_str.strip()
    for fmt in ("%d.%m.%Y", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def normalize_output_date_text(date_str):
    """Normalize date text into workbook-friendly DD.MM.YYYY where possible."""
    if not date_str:
        return None
    text = clean_text(date_str)
    if not text:
        return None
    text = re.sub(r"\s*([./-])\s*", r"\1", text)
    match = re.fullmatch(r"(\d{2})-(\d{2})-(\d{4})", text)
    if match:
        return f"{match.group(1)}.{match.group(2)}.{match.group(3)}"
    match = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", text)
    if match:
        return f"{match.group(1)}.{match.group(2)}.{match.group(3)}"
    return text


def extract_scod_date_from_text(text):
    """Extract the last SCOD-like date mention from one free-form text block."""
    if not text:
        return None

    scod_date_patterns = [
        r"S[Cc]o[Dd]\s+(?:of\s+|for[^.]*?as\s+)?(\d{2}[\.\-]\d{2}[\.\-]\d{4})",
        r"provided\s+(?:SCoD|SCOD)[^.]*?\bfrom\s+(\d{2}[\.\-]\d{2}[\.\-]\d{4})",
        r"(?:tentative\s+)?start\s+date\s+of\s+(?:SCoD|SCOD)\s+(\d{2}[\.\-]\d{2}[\.\-]\d{4})",
        r"SCOD\s+for\s+additional\s+capacity\s+as\s+(\d{2}[\.\-]\d{2}[\.\-]\d{4})",
        r"consider\s+SCOD[^.]*?as\s+(\d{2}[\.\-]\d{2}[\.\-]\d{4})",
        r"agreed\s+to\s+grant[^.]*?(?:SCoD|SCOD)\s+of\s+(\d{2}[\.\-]\d{2}[\.\-]\d{4})",
        r"agreed\s+to\s+grant\s+the\s+same\s+with\s+(?:SCoD|SCOD)\s+of\s+(\d{2}[\.\-]\d{2}[\.\-]\d{4})",
        r"start\s+date\s+of\s+connectivity[^.]*?(\d{2}[\.\-]\d{2}[\.\-]\d{4})",
        r"S[Cc]o[Dd][^0-9]{0,25}\(?(\d{2}[\.\-]\d{2}[\.\-]\d{4})\)?",
    ]

    matches = []
    for pattern in scod_date_patterns:
        for match in re.finditer(pattern, str(text), re.IGNORECASE):
            date_str = match.group(1)
            if parse_date(date_str):
                matches.append((match.start(), date_str))

    if not matches:
        return None

    matches.sort(key=lambda item: item[0])
    return matches[-1][1]


def get_latest_date(dates_str):
    """From multiple dates like '01.11.2025, 01.01.2027', return the latest one."""
    if not dates_str:
        return dates_str

    date_pattern = r"\d{2}[\.\-/]\d{2}[\.\-/]\d{4}"
    matches = re.findall(date_pattern, str(dates_str))

    if not matches:
        return dates_str
    if len(matches) == 1:
        return matches[0]

    parsed_dates = []
    for date_str in matches:
        parsed = parse_date(date_str)
        if parsed:
            parsed_dates.append((parsed, date_str))

    if parsed_dates:
        parsed_dates.sort(key=lambda item: item[0], reverse=True)
        return parsed_dates[0][1]

    return matches[-1]
