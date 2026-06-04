# OCR Document Extractor v2

Local backend OCR pipeline.

**Stack**: Python · Flask · PaddleOCR · PyMuPDF · OpenCV

**No Tesseract. No React. No Vite. No deployment.**

---

## What it does

```
PDF or image upload
      ↓
  PyMuPDF (PDF → image, first page only)
      ↓
  PaddleOCR (raw text + confidence + bounding boxes)
      ↓
  Regex + line-based parser
      ↓
  Structured JSON  (name, father_name, DOB, PAN number)
```

---

## Folder structure

```
ocr-document-extractor-v2/
├── backend/
│   ├── app.py          Flask API server
│   ├── ocr_engine.py   PaddleOCR pipeline
│   ├── parser.py       Regex + line-based field extractor
│   ├── test_ocr.py     Standalone pipeline test (no Flask)
│   ├── uploads/        Uploaded files (gitignored)
│   └── outputs/        Saved JSON / CSV / text (gitignored)
├── samples/
│   └── create_dummy_pan.py   Generates test PNG + PDF
├── requirements.txt
└── README.md
```

---

## Setup

```bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
#    Note: PaddleOCR downloads ~100 MB of model weights on first run
pip install -r requirements.txt

# 3. Generate sample files
python samples/create_dummy_pan.py
```

---

## Running the server

```bash
cd backend
python app.py
# → http://localhost:5001
```

---

## API

### Health check

```bash
curl http://localhost:5001/api/health
```

```json
{
  "status": "ok",
  "service": "OCR Document Extractor API v2"
}
```

### Extract document

```bash
# PNG or JPG
curl -X POST http://localhost:5001/api/extract-document \
     -F "file=@samples/dummy_pan.png"

# PDF
curl -X POST http://localhost:5001/api/extract-document \
     -F "file=@samples/dummy_pan.pdf"
```

**Response shape:**

```json
{
  "status": "success",
  "filename": "dummy_pan.png",
  "raw_text": "...",
  "ocr_lines": [
    { "text": "RAHUL SHARMA", "confidence": 0.98, "box": [[x1,y1],...] }
  ],
  "extracted_fields": {
    "document_type": "PAN Card",
    "name": "RAHUL SHARMA",
    "father_name": "AMIT SHARMA",
    "date_of_birth": "12/04/1999",
    "pan_number": "ABCDE1234F"
  },
  "validation_summary": {
    "extraction_status": "complete",
    "fields_found": 4,
    "total_required_fields": 4,
    "field_status": { ... },
    "pan_format_valid": true,
    "dob_format_valid": true,
    "name_quality_valid": true,
    "father_name_quality_valid": true
  },
  "average_confidence": 0.95,
  "saved_paths": {
    "uploaded_file": "...",
    "converted_image": "...",
    "raw_text": "...",
    "json_output": "...",
    "csv_output": "..."
  }
}
```

---

## Standalone test (no Flask)

```bash
# Test the OCR + parser pipeline directly
python backend/test_ocr.py samples/dummy_pan.png
python backend/test_ocr.py samples/dummy_pan.pdf
```

---

## Parser rules

- **PAN number**: regex `[A-Z]{5}[0-9]{4}[A-Z]`
- **DOB**: regex `DD/MM/YYYY` or `DD-MM-YYYY`
- **Name / Father name**: line-based positional extraction
  - Discards: header lines, Hindi script, digits, PAN numbers, dates, symbols
  - First surviving clean line → `name`
  - Second surviving clean line → `father_name`
- **Validation**: `complete` only if all 4 fields found *and* pass format/quality checks
