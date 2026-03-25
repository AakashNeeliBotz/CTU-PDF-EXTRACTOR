from __future__ import annotations

import pandas as pd


def clean_text(value):
    if not value or pd.isna(value):
        return None
    return " ".join(str(value).split())


def dedupe_preserve_order(values):
    """De-duplicate list preserving original order."""
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
