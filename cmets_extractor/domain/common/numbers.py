from __future__ import annotations

import pandas as pd
import re


def convert_to_numeric(value):
    """Convert values to numeric types when possible."""
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        if not value.strip():
            return None
        try:
            if "." not in value and "e" not in value.lower():
                return int(value)
            return float(value)
        except (ValueError, TypeError):
            return value
    return value


def parse_numeric_value(value):
    """Parse numeric string to int/float."""
    if value is None:
        return None
    text = str(value).replace(",", "").strip()
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if not match:
        return None
    num_text = match.group(1)
    num = float(num_text)
    if num.is_integer():
        return int(num)
    return num


def to_int_if_whole(value):
    """Convert float values like 50.0 to int 50 for cleaner Excel output."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        num = float(value)
        if num.is_integer():
            return int(num)
        return num
    return value
