"""
Creates sample PAN card images for testing.

Output:
  samples/dummy_pan.png  — raster image (used directly for image upload tests)
  samples/dummy_pan.pdf  — single-page PDF (used for PDF upload tests)

Usage:
  python samples/create_dummy_pan.py
"""

import os
import sys

import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont

SAMPLES_DIR = os.path.dirname(os.path.abspath(__file__))
PNG_PATH = os.path.join(SAMPLES_DIR, "dummy_pan.png")
PDF_PATH = os.path.join(SAMPLES_DIR, "dummy_pan.pdf")

# PAN card content matching the Phase 1 spec sample text
CARD_LINES = [
    ("INCOME TAX DEPARTMENT", "header"),
    ("GOVT. OF INDIA",        "header"),
    ("",                      "gap"),
    ("Permanent Account Number", "subheader"),
    ("",                      "gap"),
    ("RAHUL SHARMA",          "name"),
    ("AMIT SHARMA",           "name"),
    ("",                      "gap"),
    ("12/04/1999",            "value"),
    ("",                      "gap"),
    ("ABCDE1234F",            "pan"),
]

# Colour scheme
BG_COLOR     = (255, 250, 240)   # warm off-white
HEADER_COLOR = (30,  80,  160)   # navy blue
NAME_COLOR   = (10,  10,  10)    # near-black
VALUE_COLOR  = (60,  60,  60)    # dark grey
PAN_COLOR    = (150, 0,   0)     # deep red for PAN number

WIDTH, HEIGHT = 900, 550


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def create_png() -> None:
    img = Image.new("RGB", (WIDTH, HEIGHT), color=BG_COLOR)
    draw = ImageDraw.Draw(img)

    font_header   = _load_font(28)
    font_sub      = _load_font(20)
    font_name     = _load_font(30)
    font_value    = _load_font(26)
    font_pan      = _load_font(34)

    # Decorative top band
    draw.rectangle([(0, 0), (WIDTH, 60)], fill=HEADER_COLOR)
    draw.text((WIDTH // 2, 15), "INCOME TAX DEPARTMENT", font=font_header,
              fill="white", anchor="mt")

    # Body content
    y = 85
    for text, kind in CARD_LINES:
        if kind == "header":
            continue           # already rendered in the band
        if not text:
            y += 12
            continue

        if kind == "subheader":
            draw.text((60, y), text.upper(), font=font_sub, fill=HEADER_COLOR)
            y += 34
        elif kind == "name":
            draw.text((60, y), text, font=font_name, fill=NAME_COLOR)
            y += 44
        elif kind == "pan":
            draw.text((60, y), text, font=font_pan, fill=PAN_COLOR)
            y += 50
        else:
            draw.text((60, y), text, font=font_value, fill=VALUE_COLOR)
            y += 38

    # Decorative bottom band
    draw.rectangle([(0, HEIGHT - 30), (WIDTH, HEIGHT)], fill=HEADER_COLOR)

    img.save(PNG_PATH)
    print(f"Created: {PNG_PATH}")


def create_pdf() -> None:
    doc = fitz.open()
    page = doc.new_page(width=WIDTH, height=HEIGHT)
    rect = fitz.Rect(0, 0, WIDTH, HEIGHT)
    page.insert_image(rect, filename=PNG_PATH)
    doc.save(PDF_PATH)
    doc.close()
    print(f"Created: {PDF_PATH}")


if __name__ == "__main__":
    create_png()
    create_pdf()
    print("\nSample files ready. Test with:")
    print("  python backend/test_ocr.py samples/dummy_pan.png")
    print("  python backend/test_ocr.py samples/dummy_pan.pdf")
