from __future__ import annotations

import re


def remove_leading_zeros(app_id):
    """Remove leading zeros from application ID."""
    if app_id is None:
        return None
    return str(app_id).lstrip("0") or "0"


def is_lta_application_id(app_id):
    """Check if application ID starts with 04 (LTA ID)."""
    if app_id is None:
        return False
    return str(app_id).startswith("04")


def normalize_id_token(token):
    """Normalize ID by stripping leading zeros and non-digits."""
    if not token:
        return None
    digits = re.sub(r"\D", "", str(token))
    if len(digits) < 7:
        return None
    return remove_leading_zeros(digits)
