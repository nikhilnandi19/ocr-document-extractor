"""
Standalone pipeline test — no Flask required.

Usage:
  # from project root, after activating venv:
  python backend/test_ocr.py
  python backend/test_ocr.py samples/dummy_pan.pdf
  python backend/test_ocr.py path/to/any_image.png
"""

import json
import os
import sys

# Allow imports from this directory when script is run from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ocr_engine import convert_pdf_to_image, extract_text
from parser import parse_pan_text, validate_pan_fields

_DEFAULT_SAMPLE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "samples", "dummy_pan.png"
)


def run_test(input_path: str) -> None:
    print(f"\n{'='*60}")
    print(f"Input: {input_path}")
    print("=" * 60)

    ext = input_path.rsplit(".", 1)[-1].lower()
    image_path = input_path

    if ext == "pdf":
        tmp_image = input_path.replace(".pdf", "_converted.png")
        print(f"Converting PDF to image → {tmp_image}")
        convert_pdf_to_image(input_path, tmp_image)
        image_path = tmp_image

    print("\nRunning PaddleOCR...")
    ocr_result = extract_text(image_path)

    print(f"\nOCR lines detected: {ocr_result['word_count']}")
    print(f"Average confidence: {ocr_result['average_confidence']}")
    print(f"Low-confidence lines (<0.70): {ocr_result['low_confidence_word_count']}")

    print("\n── Raw OCR text ──")
    print(ocr_result["raw_text"])

    print("\n── OCR lines (text + confidence) ──")
    for line in ocr_result["ocr_lines"]:
        print(f"  [{line['confidence']:.2f}] {line['text']}")

    extracted = parse_pan_text(ocr_result["raw_text"])
    validation = validate_pan_fields(extracted)

    print("\n── Extracted fields ──")
    print(json.dumps(extracted, indent=2))

    print("\n── Validation summary ──")
    print(json.dumps(validation, indent=2))

    status = validation["extraction_status"]
    print(f"\nResult: {status.upper()}")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else _DEFAULT_SAMPLE

    if not os.path.exists(target):
        print(f"File not found: {target}")
        print("Generate a sample first:")
        print("  python samples/create_dummy_pan.py")
        sys.exit(1)

    run_test(target)
