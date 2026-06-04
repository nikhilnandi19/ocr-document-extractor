import csv
import json
import os
import uuid

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from ocr_engine import convert_pdf_to_image, extract_text
from parser import parse_pan_text, validate_pan_fields

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "OCR Document Extractor API v2",
    })


@app.route("/api/image/<path:filename>", methods=["GET"])
def serve_image(filename: str):
    for folder in (OUTPUT_FOLDER, UPLOAD_FOLDER):
        full_path = os.path.join(folder, filename)
        if os.path.isfile(full_path):
            return send_from_directory(folder, filename)
    return jsonify({"error": "Image not found"}), 404


@app.route("/api/extract-document", methods=["POST"])
def extract_document():
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"status": "error", "message": "Empty filename"}), 400

    if not allowed_file(file.filename):
        return jsonify({
            "status": "error",
            "message": "Unsupported file type. Allowed: pdf, png, jpg, jpeg",
        }), 400

    filename = secure_filename(file.filename)
    ext = filename.rsplit(".", 1)[1].lower()
    uid = str(uuid.uuid4())

    uploaded_file_path = os.path.join(UPLOAD_FOLDER, f"{uid}_{filename}")
    file.save(uploaded_file_path)

    try:
        converted_image_path = None

        if ext == "pdf":
            converted_image_path = os.path.join(OUTPUT_FOLDER, f"{uid}_page1.png")
            image_path = convert_pdf_to_image(uploaded_file_path, converted_image_path)
        else:
            image_path = uploaded_file_path

        ocr_result = extract_text(image_path)

        extracted_fields = parse_pan_text(ocr_result["raw_text"])
        validation = validate_pan_fields(extracted_fields)

        # ── Save outputs ──────────────────────────────────────────────────────

        raw_text_path = os.path.join(OUTPUT_FOLDER, f"{uid}_raw.txt")
        with open(raw_text_path, "w", encoding="utf-8") as f:
            f.write(ocr_result["raw_text"])

        json_output_path = os.path.join(OUTPUT_FOLDER, f"{uid}_result.json")
        json_payload = {
            "filename": filename,
            "extracted_fields": extracted_fields,
            "validation_summary": validation,
        }
        with open(json_output_path, "w", encoding="utf-8") as f:
            json.dump(json_payload, f, indent=2)

        csv_output_path = os.path.join(OUTPUT_FOLDER, f"{uid}_result.csv")
        with open(csv_output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(extracted_fields.keys()))
            writer.writeheader()
            writer.writerow(extracted_fields)

        # ── Response ──────────────────────────────────────────────────────────

        return jsonify({
            "status": "success",
            "filename": filename,
            "raw_text": ocr_result["raw_text"],
            "ocr_lines": ocr_result["ocr_lines"],
            "extracted_fields": extracted_fields,
            "validation_summary": validation,
            "average_confidence": ocr_result["average_confidence"],
            "saved_paths": {
                "uploaded_file": uploaded_file_path,
                "converted_image": converted_image_path,
                "raw_text": raw_text_path,
                "json_output": json_output_path,
                "csv_output": csv_output_path,
            },
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)
