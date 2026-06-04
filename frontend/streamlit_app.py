"""
OCR Document Extractor v2 — Streamlit frontend

Calls the Flask backend at http://localhost:5001/api/extract-document
and displays the structured extraction results.

Run:
    Terminal 1:  python backend/app.py
    Terminal 2:  streamlit run frontend/streamlit_app.py
"""

import io

import pandas as pd
import requests
import streamlit as st

# ── Config ─────────────────────────────────────────────────────────────────────

FLASK_URL = "http://localhost:5001"
EXTRACT_ENDPOINT = f"{FLASK_URL}/api/extract-document"
HEALTH_ENDPOINT  = f"{FLASK_URL}/api/health"
ALLOWED_TYPES    = ["pdf", "png", "jpg", "jpeg"]
REQUEST_TIMEOUT  = 120   # seconds — OCR can be slow on first run

# ── Page setup ─────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="OCR Document Extractor v2",
    page_icon="📄",
    layout="centered",
)

st.title("📄 OCR Document Extractor v2")
st.caption(
    "Upload a PAN-style document to extract structured fields using PaddleOCR + regex parsing. "
    "Supports PDF, PNG, JPG, and JPEG."
)
st.divider()


# ── Helper: status badge ───────────────────────────────────────────────────────

def _status_banner(status: str, fields_found: int, total: int, confidence: float) -> None:
    """Show a colour-coded banner for extraction_status."""
    label = status.upper()
    summary = f"**{fields_found}/{total}** fields found · avg OCR confidence **{confidence:.1%}**"

    if status == "complete":
        st.success(f"✅  Extraction status: **{label}** — {summary}")
    elif status == "partial":
        st.warning(f"⚠️  Extraction status: **{label}** — {summary}")
    else:
        st.error(f"❌  Extraction status: **{label}** — {summary}")


def _bool_icon(val: bool) -> str:
    return "✅  Yes" if val else "❌  No"


# ── Helper: check Flask is up ──────────────────────────────────────────────────

def _check_backend() -> bool:
    try:
        r = requests.get(HEALTH_ENDPOINT, timeout=3)
        return r.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


# ── Upload section ─────────────────────────────────────────────────────────────

uploaded_file = st.file_uploader(
    "**Upload a document**",
    type=ALLOWED_TYPES,
    help="Accepts PDF, PNG, JPG, JPEG. Designed for PAN-card-style documents.",
)

if uploaded_file is not None:
    size_kb = len(uploaded_file.getvalue()) / 1024
    st.info(f"📎  **{uploaded_file.name}** · {size_kb:.1f} KB · `{uploaded_file.type}`")

st.divider()

# ── Extract button ─────────────────────────────────────────────────────────────

extract_clicked = st.button(
    "🔍  Extract Information",
    disabled=(uploaded_file is None),
    type="primary",
    use_container_width=True,
)

# ── Processing & results ───────────────────────────────────────────────────────

if extract_clicked and uploaded_file is not None:

    # 1. Quick backend health check before sending the file
    if not _check_backend():
        st.error(
            "**Cannot reach the Flask backend.**\n\n"
            "Make sure it is running:\n"
            "```\nsource venv/bin/activate\npython backend/app.py\n```"
        )
        st.stop()

    # 2. Send file to Flask
    with st.spinner("Running PaddleOCR and parsing fields… (first run may take ~30 s to load models)"):
        try:
            response = requests.post(
                EXTRACT_ENDPOINT,
                files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)},
                timeout=REQUEST_TIMEOUT,
            )
        except requests.exceptions.ConnectionError:
            st.error(
                "**Connection lost during upload.**\n\n"
                "The Flask server stopped responding. Restart it and try again."
            )
            st.stop()
        except requests.exceptions.Timeout:
            st.error(
                f"**Request timed out after {REQUEST_TIMEOUT} s.**\n\n"
                "The OCR process is taking too long. Check the Flask terminal for errors."
            )
            st.stop()

    # 3. Handle API-level errors
    if response.status_code != 200:
        st.error(f"**API error {response.status_code}**")
        try:
            st.json(response.json())
        except Exception:
            st.code(response.text)
        st.stop()

    data = response.json()

    if data.get("status") != "success":
        st.error(f"**Extraction failed:** {data.get('message', 'Unknown error')}")
        st.stop()

    # ── Unpack response ────────────────────────────────────────────────────────
    fields     = data["extracted_fields"]
    validation = data["validation_summary"]
    ocr_lines  = data["ocr_lines"]
    raw_text   = data["raw_text"]
    avg_conf   = data["average_confidence"]
    saved      = data["saved_paths"]

    # ── Status banner ──────────────────────────────────────────────────────────
    st.subheader("Results")
    _status_banner(
        validation["extraction_status"],
        validation["fields_found"],
        validation["total_required_fields"],
        avg_conf,
    )

    st.divider()

    # ── Extracted fields ───────────────────────────────────────────────────────
    st.subheader("📋  Extracted Fields")

    fields_display = {
        "Field":  ["Document Type", "Name", "Father / Guardian Name", "Date of Birth", "PAN Number"],
        "Value":  [
            fields.get("document_type",  "—"),
            fields.get("name",           "—"),
            fields.get("father_name",    "—"),
            fields.get("date_of_birth",  "—"),
            fields.get("pan_number",     "—"),
        ],
    }
    st.dataframe(
        pd.DataFrame(fields_display),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # ── Validation summary ─────────────────────────────────────────────────────
    st.subheader("🔎  Validation Summary")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Extraction Status",  validation["extraction_status"].upper())
    col2.metric("Fields Found",       f"{validation['fields_found']} / {validation['total_required_fields']}")
    col3.metric("Avg OCR Confidence", f"{avg_conf:.1%}")
    col4.metric("OCR Lines",          len(ocr_lines))

    st.write("")

    # Boolean checks
    bool_rows = {
        "Check":  [
            "PAN format valid",
            "DOB format valid",
            "Name quality valid",
            "Father name quality valid",
        ],
        "Result": [
            _bool_icon(validation["pan_format_valid"]),
            _bool_icon(validation["dob_format_valid"]),
            _bool_icon(validation["name_quality_valid"]),
            _bool_icon(validation["father_name_quality_valid"]),
        ],
    }
    st.dataframe(
        pd.DataFrame(bool_rows),
        use_container_width=True,
        hide_index=True,
    )

    # Per-field status
    with st.expander("Field-level status", expanded=False):
        fs = validation["field_status"]
        st.dataframe(
            pd.DataFrame({
                "Field":  list(fs.keys()),
                "Status": [v.upper() for v in fs.values()],
            }),
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    # ── OCR lines table ────────────────────────────────────────────────────────
    with st.expander("🔤  OCR Lines (text · confidence · bounding box)", expanded=True):
        ocr_df = pd.DataFrame([
            {
                "text":       line["text"],
                "confidence": f"{line['confidence']:.4f}",
                "box":        str(line["box"]),
            }
            for line in ocr_lines
        ])
        st.dataframe(ocr_df, use_container_width=True, hide_index=True)

    # ── Raw OCR text ───────────────────────────────────────────────────────────
    with st.expander("📝  Raw OCR Text", expanded=False):
        st.code(raw_text, language=None)

    st.divider()

    # ── CSV download + preview ─────────────────────────────────────────────────
    st.subheader("⬇️  Download Results")

    csv_fields = {k: [v] for k, v in fields.items()}
    csv_df     = pd.DataFrame(csv_fields)

    st.dataframe(csv_df, use_container_width=True, hide_index=True)

    csv_bytes = csv_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥  Download CSV",
        data=csv_bytes,
        file_name=f"{uploaded_file.name.rsplit('.', 1)[0]}_extracted.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.divider()

    # ── Saved paths ────────────────────────────────────────────────────────────
    with st.expander("🗂️  Saved Output Paths", expanded=False):
        path_rows = []
        labels = {
            "uploaded_file":    "Uploaded file",
            "converted_image":  "Converted image (PDF only)",
            "raw_text":         "Raw OCR text (.txt)",
            "json_output":      "Extracted fields (.json)",
            "csv_output":       "Extracted fields (.csv)",
        }
        for key, label in labels.items():
            val = saved.get(key)
            path_rows.append({"Output": label, "Path": val or "—"})
        st.dataframe(
            pd.DataFrame(path_rows),
            use_container_width=True,
            hide_index=True,
        )
