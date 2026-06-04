from typing import Optional, List

import cv2
import fitz
import numpy as np
from paddleocr import PaddleOCR

_ocr_instance: Optional[PaddleOCR] = None


def _get_ocr() -> PaddleOCR:
    global _ocr_instance
    if _ocr_instance is None:
        # PaddleOCR 3.x: no use_angle_cls, no show_log
        _ocr_instance = PaddleOCR(lang="en")
    return _ocr_instance


# ── PDF conversion ─────────────────────────────────────────────────────────────

def convert_pdf_to_image(pdf_path: str, output_path: str, dpi: int = 200) -> str:
    """Convert the first page of a PDF to PNG using PyMuPDF."""
    doc = fitz.open(pdf_path)
    page = doc[0]
    scale = dpi / 72
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
    pix.save(output_path)
    doc.close()
    return output_path


# ── Image preprocessing ────────────────────────────────────────────────────────

def _ensure_min_size(image: np.ndarray, min_dim: int = 1000) -> np.ndarray:
    """Scale up images that are too small for reliable OCR."""
    h, w = image.shape[:2]
    if max(h, w) < min_dim:
        scale = min_dim / max(h, w)
        image = cv2.resize(image, None, fx=scale, fy=scale,
                           interpolation=cv2.INTER_CUBIC)
    return image


# ── Line merging ───────────────────────────────────────────────────────────────

def _y_mid(line: dict) -> float:
    ys = [p[1] for p in line["box"]]
    return (min(ys) + max(ys)) / 2.0


def _height(line: dict) -> float:
    ys = [p[1] for p in line["box"]]
    return float(max(ys) - min(ys))


def _merge_same_line_detections(ocr_lines: List[dict]) -> List[dict]:
    """
    Merge word-level detections that sit on the same horizontal text line.

    PaddleOCR sometimes emits one detection per word (instead of per line)
    when processing images rendered from PDFs at moderate DPI. This step
    groups detections whose y-midpoints are within a height-relative
    threshold, then joins them left-to-right.

    Merge condition:
        |y_mid(a) - y_mid(b)| < max(height(a), height(b)) * Y_RATIO

    With Y_RATIO = 0.6 the gap between same-line detections (~6 px) is
    well below the threshold (~50 px), while the gap between different
    lines (~140 px) stays well above it.
    """
    if not ocr_lines:
        return ocr_lines

    Y_RATIO = 0.6

    # Sort by y_mid so adjacent detections on the same line are contiguous
    sorted_lines = sorted(ocr_lines, key=lambda l: (_y_mid(l), min(p[0] for p in l["box"])))

    groups: List[List[dict]] = []
    current: List[dict] = [sorted_lines[0]]

    for line in sorted_lines[1:]:
        prev = current[-1]
        diff = abs(_y_mid(line) - _y_mid(prev))
        threshold = max(_height(line), _height(prev)) * Y_RATIO

        if diff <= threshold:
            current.append(line)
        else:
            groups.append(current)
            current = [line]

    groups.append(current)

    merged: List[dict] = []
    for group in groups:
        # Sort left-to-right within each line group
        group = sorted(group, key=lambda l: min(p[0] for p in l["box"]))

        text = " ".join(item["text"] for item in group)
        confidence = round(sum(item["confidence"] for item in group) / len(group), 4)

        # Merged bounding box: axis-aligned rectangle spanning all points
        all_pts = [p for item in group for p in item["box"]]
        xs = [p[0] for p in all_pts]
        ys = [p[1] for p in all_pts]
        merged_box = [
            [min(xs), min(ys)],
            [max(xs), min(ys)],
            [max(xs), max(ys)],
            [min(xs), max(ys)],
        ]

        merged.append({"text": text, "confidence": confidence, "box": merged_box})

    return merged


# ── Main OCR entry point ───────────────────────────────────────────────────────

def extract_text(image_path: str) -> dict:
    """
    Run PaddleOCR 3.x on an image file and return structured results.

    PaddleOCR 3.x result shape (OCRResult object, accessed like a dict):
        rec_texts  — list of recognised text strings
        rec_scores — list of confidence floats
        rec_polys  — list of numpy arrays, each shape (N, 2) = polygon vertices

    After raw extraction, same-line word detections are merged so that
    multi-word names always appear as a single OCR line.

    Returns:
        raw_text                  — lines joined by newline
        ocr_lines                 — list of {text, confidence, box}
        average_confidence
        word_count
        low_confidence_word_count
    """
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")

    image = _ensure_min_size(image)

    ocr = _get_ocr()
    results = ocr.predict(image)

    if not results:
        return {
            "raw_text": "",
            "ocr_lines": [],
            "average_confidence": 0.0,
            "word_count": 0,
            "low_confidence_word_count": 0,
        }

    res = results[0]
    texts  = res["rec_texts"]
    scores = res["rec_scores"]
    polys  = res["rec_polys"]

    raw_lines: List[dict] = []
    for text, score, poly in zip(texts, scores, polys):
        raw_lines.append({
            "text":       text,
            "confidence": round(float(score), 4),
            "box":        [[int(p[0]), int(p[1])] for p in poly],
        })

    # Merge word-level detections that share a horizontal line
    ocr_lines = _merge_same_line_detections(raw_lines)

    confidences = [line["confidence"] for line in ocr_lines]
    avg_confidence = round(sum(confidences) / len(confidences), 4) if confidences else 0.0
    low_conf_count = sum(1 for c in confidences if c < 0.70)

    return {
        "raw_text":                "\n".join(l["text"] for l in ocr_lines),
        "ocr_lines":               ocr_lines,
        "average_confidence":      avg_confidence,
        "word_count":              len(ocr_lines),
        "low_confidence_word_count": low_conf_count,
    }
