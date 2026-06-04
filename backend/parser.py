import re
from typing import Optional, List

# ── Noise sets ─────────────────────────────────────────────────────────────────

# Full lines (compared after .upper().strip()) that are never person names
_HEADER_EXACT = {
    "INCOME TAX DEPARTMENT",
    "INCOME TAX DEPT",
    "GOVT OF INDIA",
    "GOVT. OF INDIA",
    "GOVERNMENT OF INDIA",
    "PERMANENT ACCOUNT NUMBER",
    "PERMANENT ACCOUNT",
    "SIGNATURE",
    "SAMPLE",
    "PAN",
    "DATE OF BIRTH",
    "DATE OF BIRTH:",
}

# Single tokens that alone are never a person name
_NOISE_TOKENS = {
    "income", "tax", "department", "dept", "govt", "government",
    "india", "permanent", "account", "number", "signature", "photo",
    "pan", "identification", "card", "authority", "birth", "date",
    "of", "the", "and", "for", "name", "father", "sample",
}


# ── Line-level filters ─────────────────────────────────────────────────────────

def _is_header_line(line: str) -> bool:
    return line.upper().strip() in _HEADER_EXACT


def _has_non_ascii(line: str) -> bool:
    """Catches Devanagari, Arabic, and other non-Latin scripts."""
    return any(ord(c) > 127 for c in line)


def _has_digits(line: str) -> bool:
    return bool(re.search(r"\d", line))


def _has_too_many_symbols(line: str) -> bool:
    allowed = {" ", ".", "-", "'"}
    return sum(1 for c in line if not c.isalnum() and c not in allowed) > 2


def _looks_like_name(line: str) -> bool:
    """
    Returns True when a raw OCR line could plausibly be a person's name:
      - 2–60 chars, no digits, no non-ASCII
      - Not a boilerplate/header line
      - Every token is alphabetic (dots/hyphens allowed for initials)
      - Not a single noise keyword
    """
    line = line.strip()
    if len(line) < 2 or len(line) > 60:
        return False
    if _has_digits(line):
        return False
    if _has_non_ascii(line):
        return False
    if _is_header_line(line):
        return False
    if _has_too_many_symbols(line):
        return False

    tokens = line.split()
    if not tokens:
        return False
    # Every token must be purely alphabetic (dots/hyphens/apostrophes allowed)
    if not all(re.fullmatch(r"[A-Za-z.'\-]+", t) for t in tokens):
        return False
    # Reject a single-word noise token
    if len(tokens) == 1 and tokens[0].lower() in _NOISE_TOKENS:
        return False

    return True


def _name_quality_valid(name: str) -> bool:
    """Quality gate used during validation (not during extraction)."""
    if name in (None, "", "Unavailable"):
        return False
    if _has_digits(name) or _has_non_ascii(name):
        return False
    if _is_header_line(name):
        return False
    return len(name.strip()) >= 2


# ── PAN extraction with space-normalization ────────────────────────────────────

def _extract_pan(text: str) -> Optional[str]:
    """
    Find a PAN number in text, tolerating a single OCR-induced space.

    Handles:
      - "ABCDE1234F"   — clean match
      - "ABC DE1234F"  — split after 3rd char
      - "ABCDE 1234F"  — split after 5th char
      - "ABCDE1234 F"  — split before last char
    """
    # 1. Direct match
    m = re.search(r"[A-Z]{5}[0-9]{4}[A-Z]", text)
    if m:
        return m.group(0)

    # 2. Single internal space: find all [UPPERCASE/digit runs separated by one space]
    #    and check if collapsing the space yields a valid PAN.
    for m in re.finditer(r"\b([A-Z]{1,5})\s([A-Z0-9]{1,8}[A-Z])\b", text):
        candidate = m.group(1) + m.group(2)
        if re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]", candidate):
            return candidate

    return None


# ── Main extraction ────────────────────────────────────────────────────────────

def parse_pan_text(raw_text: str) -> dict:
    """
    Extract structured PAN card fields from OCR text.

    Extraction order:
      Step 1 — Regex anchors: PAN number (with space normalisation) and DOB.
      Step 2 — Label-based extraction (labeled PAN cards):
                 looks for "Name:", "Father Name:", etc.
      Step 3 — Positional fallback (unlabeled PAN cards):
                 after removing noise/header/digit lines, takes the first
                 two surviving name-like lines.
    """
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    joined = " ".join(lines)

    # ── Step 1: anchors ────────────────────────────────────────────────────────
    pan_number = _extract_pan(joined)

    dob_match = re.search(r"\b\d{2}[/\-]\d{2}[/\-]\d{4}\b", joined)
    date_of_birth = dob_match.group(0) if dob_match else None

    name: Optional[str] = None
    father_name: Optional[str] = None

    # ── Step 2: label-based ────────────────────────────────────────────────────
    # Handles: "Name: VALUE", "Father Name: VALUE", "Father's Name: VALUE"
    for line in lines:
        lower = line.lower()

        # Name: ... (but not Father Name:)
        if name is None:
            m = re.match(r"^name\s*:\s*(.+)$", line, re.IGNORECASE)
            if m:
                candidate = m.group(1).strip()
                if _looks_like_name(candidate):
                    name = candidate

        # Father Name: ... / Father's Name: ... / Father: ...
        if father_name is None:
            m = re.match(r"^father\b.{0,15}:\s*(.+)$", line, re.IGNORECASE)
            if m:
                candidate = m.group(1).strip()
                if _looks_like_name(candidate):
                    father_name = candidate

    # ── Step 3: positional fallback ───────────────────────────────────────────
    # Only runs for whichever fields are still missing.
    if name is None or father_name is None:
        already = {(name or "").upper(), (father_name or "").upper()}
        candidates: List[str] = [
            line for line in lines
            if _looks_like_name(line) and line.upper() not in already
        ]

        if name is None and candidates:
            name = candidates.pop(0)

        if father_name is None and candidates:
            father_name = candidates[0]

    return {
        "document_type": "PAN Card",
        "name":          name          or "Unavailable",
        "father_name":   father_name   or "Unavailable",
        "date_of_birth": date_of_birth or "Unavailable",
        "pan_number":    pan_number    or "Unavailable",
    }


# ── Validation ─────────────────────────────────────────────────────────────────

def validate_pan_fields(fields: dict) -> dict:
    """
    Validate extracted PAN card fields.

    extraction_status rules:
      complete    — all 4 fields valid (PAN regex, DOB regex, name quality, father quality)
      partial     — at least one anchor (PAN or DOB) AND at least one name field valid
      low_quality — anything else (e.g. anchors found but no names, or nothing at all)
    """
    pan    = fields.get("pan_number",  "")
    dob    = fields.get("date_of_birth", "")
    name   = fields.get("name",        "")
    father = fields.get("father_name", "")

    pan_valid    = bool(re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]",  pan))
    dob_valid    = bool(re.fullmatch(r"\d{2}[/\-]\d{2}[/\-]\d{4}", dob))
    name_valid   = _name_quality_valid(name)
    father_valid = _name_quality_valid(father)

    field_status = {
        "name":          "found" if name_valid   else "missing",
        "father_name":   "found" if father_valid else "missing",
        "date_of_birth": "found" if dob_valid    else "missing",
        "pan_number":    "found" if pan_valid    else "missing",
    }

    fields_found = sum(1 for s in field_status.values() if s == "found")

    has_anchor = pan_valid or dob_valid
    has_name   = name_valid or father_valid

    if pan_valid and dob_valid and name_valid and father_valid:
        status = "complete"
    elif has_anchor and has_name:
        status = "partial"
    else:
        status = "low_quality"

    return {
        "extraction_status":          status,
        "fields_found":               fields_found,
        "total_required_fields":      4,
        "field_status":               field_status,
        "pan_format_valid":           pan_valid,
        "dob_format_valid":           dob_valid,
        "name_quality_valid":         name_valid,
        "father_name_quality_valid":  father_valid,
    }
