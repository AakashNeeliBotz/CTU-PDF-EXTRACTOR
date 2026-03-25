from __future__ import annotations

import re

from cmets_extractor.domain.common.ids import normalize_id_token
from cmets_extractor.domain.common.numbers import parse_numeric_value, to_int_if_whole
from cmets_extractor.domain.common.text import clean_text


def extract_34th_status_from_text(text):
    """
    Extract status (Granted / Withdrawn / Applied) from inline deliberation text
    in the 34th CMETS PDF tables.
    """
    if not text:
        return None
    text_lower = text.lower()

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
        r"application\s+is\s+to\s+be\s+again\s+discussed\s+in\s+the\s+next\s+cmets",
        r"again\s+discussed\s+in\s+the\s+next\s+cmets",
        r"details?\s+of\s+connectivity\s+shall\s+be\s+discussed\s+in\s+the\s+next\s+cmets",
        r"request\s+for\s+connectivity\s+at\s+\d+\s*kV\s+is\s+to\s+be\s+reviewed",
    ]
    for pattern in defer_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return "Applied"

    withdrawn_patterns = [
        r"has\s+withdrawn\s+the\s+above\s+application",
        r"withdrawn\s+the\s+above\s+application",
        r"decided\s+to\s+close\s+the\s+above\s+application",
        r"shall\s+withdraw\s+their\s+application",
        r"confirmed\s+their\s+decision\s+to\s+withdraw",
        r"application\s+shall\s+be\s+closed",
        r"has\s+withdrawn\s+the\s+above",
        r"has\s+withdrawn\s+their\s+application",
        r"decision\s+to\s+withdraw\s+the\s+above\s+application",
        r"application\s+shall\s+be\s+closed\s+as\s+per\s+GNA",
        r"the\s+above\s+application\s+shall\s+be\s+closed",
        r"close\s+the\s+above\s+application\s+in\s+line\s+with",
        r"decided\s+to\s+close\s+the\s+above(?:\s+\w+){0,3}\s+application",
        r"decided\s+to\s+close.*?in\s+line\s+with\s+37\.10",
    ]
    for pattern in withdrawn_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return "Withdrawn"

    granted_patterns = [
        r"agreed\s+to\s+transition\s+connectivity",
        r"agreed\s*to\s*grant",
        r"agreedto\s+grant",
        r"it\s+was\s+agreed\s+to\s+grant",
        r"decided\s+to\s+grant",
        r"it\s+was\s+decided\s+to\s+grant",
        r"start\s+date\s+of\s+connectivity\s+under\s+gna\s+shall\s+be",
        r"it\s+was\s+agreed\s+to\s+transition",
        r"being\s+taken\s+up\s+for\s+discussion\s*(?:&|and)\s*grant",
        r"taken\s+up\s+for\s+discussion\s*(?:&|and)\s*grant",
        r"proposed\s+to\s+grant\s+connectivity\s+to",
        r"proposed\s+to\s+grant\s+connectivity\s+(?:of|through|for|at)",
        r"proposed\s+to\s+grant\s+addition\s+of\s+generation\s+capacity",
    ]
    for pattern in granted_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return "Granted"

    return "Applied"


def has_explicit_applied_signal(text):
    """Detect explicit defer/review wording that should keep status as Applied."""
    if not text:
        return False
    patterns = [
        r"decided\s+to\s+defer\s+the\s+above\s+application",
        r"decided\s+to\s+defer\s+the\s+above",
        r"it\s+was\s+decided\s+to\s+defer",
        r"application.*?may\s+be\s+taken\s+up.*?at\s+later\s+stage",
        r"shall\s+be\s+considered\s+in\s+next\s+cmets",
        r"may\s+be\s+considered\s+for\s+discussion\s+in\s+next\s+cmets",
        r"shall\s+be\s+considered\s+for\s+discussion.*?next\s+cmets",
        r"considered\s+for\s+discussion.*?next\s+cmets",
        r"(?:it\s+was\s+)?decided\s+to\s+take\s+up\s+the\s+above\s+application.*?for\s+discussion.*?next\s+cmets",
        r"take\s+up\s+the\s+above\s+application.*?for\s+discussion.*?next\s+cmets",
        r"again\s+for\s+discussion\s+in\s+the\s+next\s+cmets",
        r"application\s+is\s+to\s+be\s+again\s+discussed\s+in\s+the\s+next\s+cmets",
        r"again\s+discussed\s+in\s+the\s+next\s+cmets",
        r"details?\s+of\s+connectivity\s+shall\s+be\s+discussed\s+in\s+the\s+next\s+cmets",
        r"request.*?\bis\s+to\s+be\s+reviewed\b",
        r"\bis\s+to\s+be\s+reviewed\b",
        r"at\s+later\s+stage",
    ]
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def is_inline_app_reference(full_text, start_pos, token):
    """Return True when token is part of an inline 'App. No. <id>' reference."""
    if not full_text or start_pos is None or not token:
        return False
    prefix = full_text[max(0, start_pos - 80) : start_pos]
    if not re.search(r"(?:app|appl)\.?\s*no\.?\s*$", prefix, re.IGNORECASE):
        return False
    if start_pos < 40:
        return False
    if re.search(r"(?:^|[.;:])\s*(?:app|appl)\.?\s*no\.?\s*$", prefix, re.IGNORECASE):
        return False
    return True


def extract_best_app_context_from_full_text(app_id, full_text, window_after=9000):
    """
    Pull the best exact-app context block from full PDF text.
    This is more reliable than applicant-name inference for hybrid rows when
    deliberation_dict only captures table rows.
    """
    if not app_id or not full_text:
        return ""

    app_token = normalize_id_token(app_id)
    if not app_token:
        return ""

    normalized = re.sub(r"\s+", " ", full_text)
    best = ("", -1)

    for match in re.finditer(r"\b0*" + re.escape(app_token) + r"\b", normalized):
        if is_inline_app_reference(normalized, match.start(), app_token):
            continue

        anchor_window_start = max(0, match.start() - 80)
        anchor_window = normalized[anchor_window_start : match.end() + 40]
        row_anchor = None
        for candidate in re.finditer(
            r"\b\d{1,3}\.?\s*0*" + re.escape(app_token) + r"\s*(?:\(|\b)",
            anchor_window,
            re.IGNORECASE,
        ):
            row_anchor = candidate
        if row_anchor:
            start = anchor_window_start + row_anchor.start()
        else:
            start = max(0, match.start() - 120)

        tail = normalized[match.end() :]
        next_row = re.search(r"\b\d{1,3}\.?\s*22\d{8}\b", tail)
        if next_row:
            end = match.end() + next_row.start()
        else:
            end = min(len(normalized), match.end() + window_after)
        window = normalized[start:end]
        wl = window.lower()
        score = 0
        if row_anchor:
            score += 10
        if re.search(
            r"^\s*\d{1,3}\.?\s*0*" + re.escape(app_token) + r"\s*(?:\(|\b)",
            window,
            re.IGNORECASE,
        ):
            score += 8
        elif re.search(r"^\s*0*" + re.escape(app_token) + r"\s*(?:\(|\b)", window, re.IGNORECASE):
            score += 2
        if is_reference_only_context(window):
            score -= 6
        if is_indirect_app_context(window, app_token):
            score -= 8
        if re.search(r"withdraw|decided\s+to\s+close|close\s+the\s+above\s+application", wl):
            score += 8
        if re.search(
            r"decided\s+to\s+defer|taken\s+up\s+for\s+grant\s+at\s+later\s+stage|considered\s+for\s+discussion.*next\s+cmets",
            wl,
        ):
            score += 6
        if re.search(r"agreed\s*to\s*grant|shall\s+be\s+issued|in-principle\s+intimation", wl):
            score += 5
        if re.search(r"proposed\s+to\s+grant", wl):
            score += 2
        if "start date of additional generation capacity" in wl:
            score += 1
        score += min(len(window), 5000) / 5000.0
        if score > best[1]:
            best = (window, score)

    return best[0]


def scope_text_to_app(text, app_id, window_after=5000):
    """
    Trim one mixed deliberation block to the local context of a target app-id.
    Helps prevent cross-row bleed in shared table/discussion text.
    """
    if not text:
        return text
    token = normalize_id_token(app_id)
    normalized = re.sub(r"\s+", " ", str(text))
    if not token:
        return normalized

    direct_anchor = re.search(
        r"(?:^|\b)\d{1,3}\.?\s*0*" + re.escape(token) + r"(?:\s*\(|\b)",
        normalized,
        re.IGNORECASE,
    )
    anchor_match = direct_anchor
    if not anchor_match:
        anchor_match = re.search(
            r"(?:app|appl)\.?\s*no\.?\s*0*" + re.escape(token) + r"\b",
            normalized,
            re.IGNORECASE,
        )
    if not anchor_match:
        anchor_match = re.search(
            r"(?:^|\b)0*" + re.escape(token) + r"(?:\s*\(|\b)",
            normalized,
            re.IGNORECASE,
        )
    if not anchor_match:
        return normalized

    if direct_anchor:
        start = anchor_match.start()
    else:
        start = max(0, anchor_match.start() - 30)

    tail = normalized[start:]
    row_pattern = re.compile(r"\b\d{1,3}\.?\s*22\d{8}\b", re.IGNORECASE)
    next_row_match = None
    for match in row_pattern.finditer(tail):
        if match.start() < 20:
            continue
        next_row_match = match
        break

    if next_row_match:
        end = start + next_row_match.start()
    else:
        end = min(len(normalized), start + int(window_after))

    scoped = normalized[start:end].strip()
    if scoped and len(scoped) >= 40:
        return scoped
    return normalized


def extract_duration_hours_from_text(text):
    """Extract explicit battery-duration hours such as 'four (4) hours' or '4 hours'."""
    if not text:
        return None

    normalized = re.sub(r"\s+", " ", str(text)).strip()
    patterns = [
        r"duration\s+of\s+(?:[A-Za-z]+\s*)?\(?(\d+(?:\.\d+)?)\)?\s*hours",
        r"for\s+(?:duration\s+of\s+)?(?:[A-Za-z]+\s*)?\(?(\d+(?:\.\d+)?)\)?\s*hours",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized, re.IGNORECASE)
        if match:
            return parse_numeric_value(match.group(1))
    return None


def extract_preface_context_from_full_text(app_id, full_text, lookback=2800, lookahead=600):
    """Capture shared discussion text immediately preceding one app row."""
    if not app_id or not full_text:
        return ""

    token = normalize_id_token(app_id)
    if not token:
        return ""

    normalized = re.sub(r"\s+", " ", str(full_text))
    pattern = re.compile(
        r"\b\d{1,3}\.?\s*0*" + re.escape(token) + r"(?:\s*\(|\b)",
        re.IGNORECASE,
    )
    best = ("", -1)

    for match in pattern.finditer(normalized):
        start = max(0, match.start() - int(lookback))
        end = min(len(normalized), match.end() + int(lookahead))
        chunk = normalized[start:end]
        score = 0
        if extract_duration_hours_from_text(chunk) is not None:
            score += 10
        if re.search(r"\bapp\.?\s*no\.?\s*0*" + re.escape(token) + r"\b", chunk, re.IGNORECASE):
            score += 2
        if clean_text(chunk):
            score += 1
        if score > best[1]:
            best = (chunk, score)

    return best[0]


def is_reference_only_context(text):
    """Identify contexts that only reference a previously-discussed application."""
    if not text:
        return False
    patterns = [
        r"as\s+decided\s+during\s+the\s+discussion\s+of\s+(?:the\s+)?previous\s+application",
        r"during\s+the\s+discussion\s+of\s+(?:the\s+)?previous\s+application",
        r"discussion\s+of\s+(?:the\s+)?previous\s+application",
        r"previous\s+application.*?it\s+was\s+decided",
    ]
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def is_indirect_app_context(text, app_id):
    """Detect contexts where the app id is only mentioned as an inline reference."""
    if not text or not app_id:
        return False
    token = normalize_id_token(app_id)
    if not token:
        return False
    has_row_anchor = re.search(r"\b\d{1,3}\.?\s*0*" + re.escape(token) + r"\b", text)
    has_direct_anchor = re.search(
        r"^\s*0*" + re.escape(token) + r"(?:\s*\(|\b)",
        text,
        re.IGNORECASE,
    )
    has_leading_app_ref = re.search(
        r"^\s*(?:app|appl)\.?\s*no\.?\s*0*" + re.escape(token) + r"\b",
        text,
        re.IGNORECASE,
    )
    has_app_ref = re.search(r"App\.?\s*No\.?\s*0*" + re.escape(token) + r"\b", text, re.IGNORECASE)
    return bool(has_app_ref and not has_row_anchor and not has_direct_anchor and not has_leading_app_ref)


def has_direct_hybrid_app_anchor(text, app_id):
    """Return True when the context starts with a direct row anchor for this app."""
    if not text or not app_id:
        return False
    token = normalize_id_token(app_id)
    if not token:
        return False
    return bool(
        re.search(
            r"^\s*(?:\d{1,3}\.?\s*)?0*" + re.escape(token) + r"(?:\s*\(|\b)",
            text,
            re.IGNORECASE,
        )
    )


def get_hybrid_app_anchor_offset(text, app_id):
    """Get the position of the direct app anchor inside one hybrid context."""
    if not text or not app_id:
        return None
    token = normalize_id_token(app_id)
    if not token:
        return None
    match = re.search(
        r"(?:^|\b)(?:\d{1,3}\.?\s*)?0*" + re.escape(token) + r"(?:\s*\(|\b)",
        text,
        re.IGNORECASE,
    )
    return match.start() if match else None


def extract_ordered_hybrid_status(text):
    """Resolve status from the last direct decision signal in one context."""
    if not text:
        return None

    proposal_grant_patterns = [
        r"proposed\s+to\s+grant\s+connectivity\s+to",
        r"proposed\s+to\s+grant\s+connectivity\s+at",
        r"proposed\s+to\s+grant\s+connectivity\s+(?:of|through|for)",
        r"proposed\s+to\s+grant\s+addition\s+of\s+generation\s+capacity",
    ]
    strong_grant_patterns = [
        r"agreed\s+to\s+transition\s+connectivity",
        r"agreed\s*to\s*grant",
        r"agreedto\s+grant",
        r"it\s+was\s+agreed\s+to\s+grant",
        r"decided\s+to\s+grant",
        r"it\s+was\s+decided\s+to\s+grant",
        r"start\s+date\s+of\s+connectivity\s+under\s+gna\s+shall\s+be",
        r"connectivity\s+of\s+\d+(?:\.\d+)?\s*mw\s+shall\s+be\s+granted\s+to",
        r"connectivity\s+to\s+.*?\s+shall\s+be\s+granted",
    ]

    patterns = [
        (
            "Applied",
            [
                r"decided\s+to\s+defer\s+the\s+above\s+application",
                r"decided\s+to\s+defer\s+the\s+above",
                r"it\s+was\s+decided\s+to\s+defer",
                r"application.*?may\s+be\s+taken\s+up.*?at\s+later\s+stage",
                r"shall\s+be\s+considered\s+for\s+discussion.*?next\s+cmets",
                r"considered\s+for\s+discussion.*?next\s+cmets",
                r"(?:it\s+was\s+)?decided\s+to\s+take\s+up\s+the\s+above\s+application.*?for\s+discussion.*?next\s+cmets",
                r"take\s+up\s+the\s+above\s+application.*?for\s+discussion.*?next\s+cmets",
                r"again\s+for\s+discussion\s+in\s+the\s+next\s+cmets",
                r"application\s+is\s+to\s+be\s+again\s+discussed\s+in\s+the\s+next\s+cmets",
                r"again\s+discussed\s+in\s+the\s+next\s+cmets",
                r"details?\s+of\s+connectivity\s+shall\s+be\s+discussed\s+in\s+the\s+next\s+cmets",
                r"request.*?\bis\s+to\s+be\s+reviewed\b",
                r"\bis\s+to\s+be\s+reviewed\b",
            ],
        ),
        (
            "Withdrawn",
            [
                r"has\s+withdrawn\s+the\s+above\s+application",
                r"withdrawn\s+the\s+above\s+application",
                r"decided\s+to\s+close\s+the\s+above\s+application",
                r"decided\s+to\s+close\s+the\s+above(?:\s+\w+){0,3}\s+application",
                r"shall\s+withdraw\s+their\s+application",
                r"confirmed\s+their\s+decision\s+to\s+withdraw",
                r"decision\s+to\s+withdraw\s+the\s+above\s+application",
                r"application\s+shall\s+be\s+closed",
                r"close\s+the\s+above\s+application\s+in\s+line\s+with",
            ],
        ),
        ("Granted", [*strong_grant_patterns, *proposal_grant_patterns]),
    ]

    latest = None
    for status, status_patterns in patterns:
        for pattern in status_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                candidate = (match.end(), status)
                if latest is None or candidate[0] > latest[0]:
                    latest = candidate

    if latest:
        if latest[1] == "Granted":
            has_proposal_only_grant = any(
                re.search(pattern, text, re.IGNORECASE) for pattern in proposal_grant_patterns
            ) and not any(re.search(pattern, text, re.IGNORECASE) for pattern in strong_grant_patterns)
            if has_proposal_only_grant and re.search(
                r"(?:the\s+same\s+was\s+noted|noted\s+the\s+same)",
                text,
                re.IGNORECASE,
            ) and not re.search(
                r"(?:agreed\s+for\s+the\s+same|noted\s+and\s+agreed)",
                text,
                re.IGNORECASE,
            ):
                return "Applied"
        return latest[1]
    return extract_34th_status_from_text(text)


def has_reg52_grant_followthrough(text):
    """Detect Reg. 5.2 follow-through language that usually appears after grant."""
    if not text:
        return False
    patterns = [
        r"shall\s+be\s+responsible\s+for\s+compliance\s+with\s+the\s+Grid\s+Code",
        r"shall\s+submit\s+the\s+technical\s+connection\s+data",
        r"additional\s+generation\s+capacity\s+as\s+[\"“”']?Lead\s+generator",
        r"in\s+terms\s+of\s+clause\s+\(y\)\(ii\)\s+of\s+Regulation\s+2\.1",
    ]
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def score_hybrid_context(text, app_id=None, prefer_exact=False):
    """Score hybrid-context candidates so richer direct contexts win over references."""
    if not text:
        return float("-inf")
    status = extract_ordered_hybrid_status(text)
    direct_anchor = has_direct_hybrid_app_anchor(text, app_id)
    reference_only = not direct_anchor and (
        is_reference_only_context(text) or is_indirect_app_context(text, app_id)
    )
    lowered = text.lower()
    score = 0.0
    if prefer_exact:
        score += 4.0
    if reference_only:
        score -= 8.0
    else:
        score += 6.0
    anchor_offset = get_hybrid_app_anchor_offset(text, app_id)
    if anchor_offset is not None:
        if anchor_offset <= 80:
            score += 7.0
        elif anchor_offset <= 220:
            score += 3.0
        else:
            score -= 6.0
        if re.search(r"\b\d{1,3}\.?\s*22\d{8}\b", text[:anchor_offset], re.IGNORECASE):
            score -= 7.0
    elif app_id:
        score -= 5.0
    if status == "Granted":
        score += 5.0
    elif status == "Withdrawn":
        score += 4.0
    elif has_explicit_applied_signal(text):
        score += 2.0
    if has_reg52_grant_followthrough(text):
        score += 2.0
    if re.search(r"start\s+date\s+of\s+(?:connectivity|additional\s+generation\s+capacity)", lowered):
        score += 2.0
    if re.search(
        r"(?:dedicated|common)\s+transmission\s+system|transmission\s+system\s+under\s+applicant\s+scope",
        lowered,
    ):
        score += 2.0
    score += min(len(text), 5000) / 1000.0
    return score


def has_shared_hybrid_decision_context(text, app_id=None):
    """Detect a merged deliberation block covering multiple app IDs with grant details."""
    if not text:
        return False

    normalized = clean_text(text)
    if not normalized:
        return False

    ids = {
        normalize_id_token(token)
        for token in re.findall(r"\b0*(22\d{8,})\b", normalized)
        if normalize_id_token(token)
    }
    token = normalize_id_token(app_id)
    if token and token not in ids:
        return False
    if len(ids) < 2:
        return False

    grant_patterns = [
        r"proposed\s+to\s+grant\s+connectivity\s+at",
        r"proposed\s+to\s+grant\s+connectivity\s+to",
        r"connectivity\s+of\s+\d+(?:\.\d+)?\s*mw\s+shall\s+be\s+granted\s+to",
        r"start\s+date\s+of\s+connectivity\s+under\s+gna\s+shall\s+be",
    ]
    detail_patterns = [
        r"associated\s+transmission\s+system",
        r"transmission\s+system\s+under\s+applicant\s+scope",
        r"details\s+of\s+transmission\s+system\s+for\s+connectivity\s+under\s+gna",
        r"common\s+pooling\s+station",
    ]
    return any(re.search(pattern, normalized, re.IGNORECASE) for pattern in grant_patterns) and any(
        re.search(pattern, normalized, re.IGNORECASE) for pattern in detail_patterns
    )


def promote_shared_hybrid_context(app_id, exact_text=None, inferred_text=None):
    """Prefer an inferred merged block when the direct exact context is only a short table row."""
    exact_clean = clean_text(exact_text)
    if not has_shared_hybrid_decision_context(inferred_text, app_id=app_id):
        return exact_text
    if exact_clean and (
        has_explicit_applied_signal(exact_clean)
        or extract_ordered_hybrid_status(exact_clean) == "Applied"
    ):
        return exact_text
    if exact_clean and len(exact_clean) >= 500 and has_shared_hybrid_decision_context(
        exact_clean,
        app_id=app_id,
    ):
        return exact_text
    if exact_clean and len(exact_clean) >= 500 and extract_ordered_hybrid_status(exact_clean) in {
        "Granted",
        "Withdrawn",
    }:
        return exact_text
    return inferred_text or exact_text


def choose_hybrid_field_context(app_id, exact_text=None, delib_text=None, inferred_text=None):
    """Choose the strongest context among exact/deliberation/inferred windows."""
    exact_text = promote_shared_hybrid_context(
        app_id,
        exact_text=exact_text,
        inferred_text=inferred_text,
    )
    candidates = [
        ("exact", exact_text, True),
        ("delib", delib_text, False),
        ("inferred", inferred_text, False),
    ]
    best_text = ""
    best_score = float("-inf")
    for _, text, prefer_exact in candidates:
        if not text:
            continue
        score = score_hybrid_context(text, app_id=app_id, prefer_exact=prefer_exact)
        if score > best_score:
            best_score = score
            best_text = text
    if (
        exact_text
        and has_direct_hybrid_app_anchor(exact_text, app_id)
        and not is_reference_only_context(exact_text)
        and not is_indirect_app_context(exact_text, app_id)
    ):
        exact_score = score_hybrid_context(exact_text, app_id=app_id, prefer_exact=True)
        if exact_score >= best_score - 2.0:
            return exact_text
    return best_text


def resolve_hybrid_status(base_status, exact_text=None, delib_text=None, inferred_text=None, app_id=None):
    """Resolve hybrid-row status using exact app context before broader fallbacks."""
    exact_text = promote_shared_hybrid_context(
        app_id,
        exact_text=exact_text,
        inferred_text=inferred_text,
    )
    exact_status = extract_ordered_hybrid_status(exact_text) if exact_text else None
    delib_status = extract_ordered_hybrid_status(delib_text) if delib_text else None
    context_status = extract_ordered_hybrid_status(inferred_text) if inferred_text else None
    direct_exact_anchor = has_direct_hybrid_app_anchor(exact_text, app_id)
    exact_reference_only = bool(
        exact_text
        and not direct_exact_anchor
        and (is_reference_only_context(exact_text) or is_indirect_app_context(exact_text, app_id))
    )

    if exact_status == "Withdrawn":
        return "Withdrawn"

    if exact_status in {"Granted", "Applied"} and direct_exact_anchor and not exact_reference_only:
        return exact_status

    if exact_status == "Applied" and has_explicit_applied_signal(exact_text) and not exact_reference_only:
        return "Applied"

    status = base_status
    if exact_status == "Granted" and status in (None, "Applied"):
        status = "Granted"

    if delib_status in {"Granted", "Withdrawn"} and status in (None, "Applied"):
        status = delib_status
    elif context_status in {"Granted", "Withdrawn"} and (
        status is None or (status == "Applied" and exact_reference_only)
    ):
        status = context_status

    if not status:
        status = exact_status or delib_status or context_status or "Applied"

    return status


def resolve_35th_hybrid_status(current_status, *texts):
    """Apply 35th-specific decision phrases without changing global status logic."""
    merged = " ".join(clean_text(text) for text in texts if clean_text(text))
    if not merged:
        return current_status

    lowered = merged.lower()
    withdrawn_patterns = [
        r"decision\s+to\s+withdraw\s+the\s+above\s+application",
        r"confirmed\s+their\s+decision\s+to\s+withdraw",
        r"has\s+withdrawn\s+their\s+application",
        r"decided\s+to\s+close\s+the\s+above\s+application",
        r"the\s+above\s+application\s+shall\s+be\s+closed",
    ]
    applied_patterns = [
        r"application\s+is\s+to\s+be\s+again\s+discussed\s+in\s+the\s+next\s+cmets",
        r"again\s+discussed\s+in\s+the\s+next\s+cmets",
        r"again\s+for\s+discussion\s+in\s+the\s+next\s+cmets",
        r"shall\s+be\s+considered\s+for\s+discussion.*?next\s+cmets",
        r"decided\s+to\s+defer\s+the\s+above\s+application",
    ]
    granted_patterns = [
        r"agreed\s*to\s*grant",
        r"it\s+was\s+agreed\s+to\s+grant",
        r"proposed\s+to\s+grant\s+connectivity",
        r"proposed\s+to\s+grant\s+addition\s+of\s+generation\s+capacity",
        r"connectivity\s+of\s+\d+(?:\.\d+)?\s*mw\s+shall\s+be\s+granted",
    ]

    has_withdrawn = any(re.search(pattern, lowered, re.IGNORECASE) for pattern in withdrawn_patterns)
    has_applied = any(re.search(pattern, lowered, re.IGNORECASE) for pattern in applied_patterns)
    has_granted = any(re.search(pattern, lowered, re.IGNORECASE) for pattern in granted_patterns)

    if has_applied:
        return "Applied"
    if has_withdrawn:
        return "Withdrawn"
    if has_granted:
        return "Granted"
    return current_status


def _infer_hybrid_context_from_name(app_name, app_quantum, substation_hint, normalized_full_text, app_id=None):
    """
    Infer deliberation context when app-id based segmentation is sparse.
    Uses applicant-name windows scored by decision/date signals.
    """
    if not normalized_full_text or not app_name:
        return ""

    name = clean_text(app_name)
    if not name or len(name) < 6:
        return ""

    app_token = normalize_id_token(app_id)

    sub_token = None
    if substation_hint:
        token_parts = re.findall(r"[A-Za-z0-9\-]+", str(substation_hint))
        if token_parts:
            sub_token = token_parts[0]

    q_token = None
    if app_quantum is not None:
        q_token = str(to_int_if_whole(app_quantum))

    best = ("", -1)
    name_matches = list(re.finditer(re.escape(name), normalized_full_text, re.IGNORECASE))

    if app_token:
        for app_match in re.finditer(r"\b" + re.escape(app_token) + r"\b", normalized_full_text):
            start = max(0, app_match.start() - 350)
            end = min(len(normalized_full_text), app_match.end() + 2600)
            window = normalized_full_text[start:end]
            wl = window.lower()
            score = 0
            if re.search(re.escape(name), window, re.IGNORECASE):
                score += 3
            if re.search(
                r"agreed\s*to\s*grant|agreedto\s+grant|proposed\s+to\s+grant|considered\s+for\s+grant|decided\s+to\s+close|has\s+withdrawn",
                wl,
            ):
                score += 3
            if "start date of connectivity under gna" in wl or "start date of additional generation capacity" in wl:
                score += 2
            if sub_token and re.search(r"\b" + re.escape(sub_token) + r"\b", window, re.IGNORECASE):
                score += 1
            if q_token and re.search(r"\b" + re.escape(q_token) + r"\b", window):
                score += 1
            if score > best[1]:
                best = (window, score)

    for name_match in name_matches:
        start = max(0, name_match.start() - 600)
        end = min(len(normalized_full_text), name_match.end() + 2200)
        window = normalized_full_text[start:end]
        wl = window.lower()

        score = 0
        if re.search(
            r"agreed\s*to\s*grant|agreedto\s+grant|proposed\s+to\s+grant|considered\s+for\s+grant|decided\s+to\s+close|has\s+withdrawn",
            wl,
        ):
            score += 3
        if "start date of connectivity under gna" in wl or "start date of additional generation capacity" in wl:
            score += 2
        if sub_token and re.search(r"\b" + re.escape(sub_token) + r"\b", window, re.IGNORECASE):
            score += 1
        if q_token and re.search(r"\b" + re.escape(q_token) + r"\b", window):
            score += 1
        if app_token:
            if re.search(r"\b" + re.escape(app_token) + r"\b", window):
                score += 3
            else:
                score -= 2

        if score > best[1]:
            best = (window, score)

    return best[0] if best[1] >= 4 else ""


__all__ = [
    "_infer_hybrid_context_from_name",
    "choose_hybrid_field_context",
    "extract_34th_status_from_text",
    "extract_best_app_context_from_full_text",
    "extract_duration_hours_from_text",
    "extract_ordered_hybrid_status",
    "extract_preface_context_from_full_text",
    "get_hybrid_app_anchor_offset",
    "has_direct_hybrid_app_anchor",
    "has_explicit_applied_signal",
    "has_reg52_grant_followthrough",
    "has_shared_hybrid_decision_context",
    "is_indirect_app_context",
    "is_inline_app_reference",
    "is_reference_only_context",
    "promote_shared_hybrid_context",
    "resolve_35th_hybrid_status",
    "resolve_hybrid_status",
    "scope_text_to_app",
    "score_hybrid_context",
]
