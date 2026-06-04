"""
Direct parser tests — no Flask, no PaddleOCR.

Feeds hardcoded raw OCR text into parser.py and checks extracted fields.

Usage:
  python backend/test_parser.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parser import parse_pan_text, validate_pan_fields

# ── Colour helpers (plain fallback if terminal doesn't support ANSI) ──────────
GREEN = "\033[32m"
RED   = "\033[31m"
CYAN  = "\033[36m"
BOLD  = "\033[1m"
RESET = "\033[0m"


def _pass(msg="PASS"):  return f"{GREEN}{BOLD}{msg}{RESET}"
def _fail(msg="FAIL"):  return f"{RED}{BOLD}{msg}{RESET}"
def _head(msg):         return f"{CYAN}{BOLD}{msg}{RESET}"


# ── Test cases ────────────────────────────────────────────────────────────────

TEST_CASES = [
    {
        "id": 1,
        "description": "Clean unlabeled PAN-style OCR",
        "raw_text": """\
INCOME TAX DEPARTMENT
GOVT. OF INDIA
RAHUL SHARMA
AMIT SHARMA
12/04/1999
ABCDE1234F""",
        "expected": {
            "name":              "RAHUL SHARMA",
            "father_name":       "AMIT SHARMA",
            "date_of_birth":     "12/04/1999",
            "pan_number":        "ABCDE1234F",
            "extraction_status": "complete",
        },
    },
    {
        "id": 2,
        "description": "Labeled PAN-style OCR",
        "raw_text": """\
INCOME TAX DEPARTMENT
GOVT. OF INDIA
Name: RAHUL SHARMA
Father Name: AMIT SHARMA
Date of Birth: 12/04/1999
PAN: ABCDE1234F""",
        "expected": {
            "name":              "RAHUL SHARMA",
            "father_name":       "AMIT SHARMA",
            "date_of_birth":     "12/04/1999",
            "pan_number":        "ABCDE1234F",
            "extraction_status": "complete",
        },
    },
    {
        "id": 3,
        "description": "Noisy real-like OCR with Hindi script and mixed headers",
        "raw_text": """\
आयकर विभाग
भारत सरकार
INCOME TAX DEPARTMENT
GOVT. OF INDIA
RAHUL GUPTA
SURESH GUPTA
23/11/1974
ABCDE1234F
Permanent Account Number
Signature""",
        "expected": {
            "name":              "RAHUL GUPTA",
            "father_name":       "SURESH GUPTA",
            "date_of_birth":     "23/11/1974",
            "pan_number":        "ABCDE1234F",
            "extraction_status": "complete",
        },
    },
    {
        "id": 4,
        "description": "PAN number with internal OCR space (ABC DE1234F)",
        "raw_text": """\
INCOME TAX DEPARTMENT
GOVT. OF INDIA
SAMPLE NAME
SAMPLE FATHER
01/01/1990
ABC DE1234F""",
        "expected": {
            # Only check PAN normalisation; name/father/dob are placeholder text
            "pan_number": "ABCDE1234F",
        },
    },
    {
        "id": 5,
        "description": "Bad OCR — name lines missing, only PAN and DOB present",
        "raw_text": """\
INCOME TAX DEPARTMENT
GOVT. OF INDIA
23/11/1974
ABCDE1234F""",
        "expected": {
            "name":              "Unavailable",
            "father_name":       "Unavailable",
            "date_of_birth":     "23/11/1974",
            "pan_number":        "ABCDE1234F",
            # spec: partial OR low_quality — both are accepted
            "extraction_status": ["partial", "low_quality"],
        },
    },
]


# ── Runner ────────────────────────────────────────────────────────────────────

def run_tests() -> None:
    passed = 0
    failed = 0

    for tc in TEST_CASES:
        print()
        print(_head(f"{'='*60}"))
        print(_head(f"Test {tc['id']}: {tc['description']}"))
        print(f"{'─'*60}")

        fields     = parse_pan_text(tc["raw_text"])
        validation = validate_pan_fields(fields)

        print("Extracted fields:")
        print(f"  name          : {fields['name']}")
        print(f"  father_name   : {fields['father_name']}")
        print(f"  date_of_birth : {fields['date_of_birth']}")
        print(f"  pan_number    : {fields['pan_number']}")

        print()
        print("Validation summary:")
        print(f"  extraction_status         : {validation['extraction_status']}")
        print(f"  fields_found              : {validation['fields_found']}/{validation['total_required_fields']}")
        print(f"  pan_format_valid          : {validation['pan_format_valid']}")
        print(f"  dob_format_valid          : {validation['dob_format_valid']}")
        print(f"  name_quality_valid        : {validation['name_quality_valid']}")
        print(f"  father_name_quality_valid : {validation['father_name_quality_valid']}")

        # Check expected values
        mismatches = []
        expected = tc["expected"]

        for key, exp_val in expected.items():
            if key == "extraction_status":
                actual = validation["extraction_status"]
            else:
                actual = fields.get(key)

            # Accept a list of valid values
            accepted = exp_val if isinstance(exp_val, list) else [exp_val]

            if actual not in accepted:
                mismatches.append(
                    f"  {key}: expected {exp_val!r}, got {actual!r}"
                )

        print()
        if not mismatches:
            print(_pass(f"  ✓ PASS — all checked fields match"))
            passed += 1
        else:
            print(_fail(f"  ✗ FAIL"))
            for m in mismatches:
                print(f"{RED}{m}{RESET}")
            failed += 1

    print()
    print(_head("=" * 60))
    print(f"Results: {_pass(f'{passed} passed')}  {_fail(f'{failed} failed')}  (total {len(TEST_CASES)})")
    print(_head("=" * 60))

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
