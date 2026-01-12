from __future__ import annotations

import sqlite3
from uuid import uuid4

import cv2
import numpy as np
import pytesseract
from flask import Flask, jsonify, render_template, request

print("[STARTUP] Initializing Flask app...")

app = Flask(__name__)

print("[DB] Connecting to database...")
conn = sqlite3.connect("database.sqlite", check_same_thread=False)

print("[DB] Loading schema...")
with open("schema.sql") as f:
    conn.executescript(f.read())

conn.commit()
cursor = conn.cursor()
print("[DB] Database ready.")


class TessaractSettings:
    def __init__(self, psm: int = 6, oem: int = 3, lang: str = "eng"):
        self.psm = psm
        self.oem = oem
        self.lang = lang
        print(f"[TESSERACT] Initialized with psm={psm}, oem={oem}, lang={lang}")

    def get_config(self) -> str:
        config = f"--psm {self.psm} --oem {self.oem}"
        print(f"[TESSERACT] Using config: {config}")
        return config


settings = TessaractSettings()


def preprocess_image(image_bytes: bytes):
    print("[IMAGE] Preprocessing image...")
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)

    if image is None:
        print("[ERROR] Failed to decode image.")
        return None

    _, processed_image = cv2.threshold(
        image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU  # type: ignore
    )
    print("[IMAGE] Preprocessing complete.")
    return processed_image


def save_file(file_bytes: bytes) -> str:
    file_id = str(uuid4())
    print(f"[FILE] Saving file with ID: {file_id}")
    with open(f"uploads/{file_id}.png", "wb") as f:
        f.write(file_bytes)
    print("[FILE] File saved successfully.")
    return file_id


@app.route("/upload", methods=["POST"])
def upload():
    print("[API] /upload called")

    if "file" not in request.files:
        print("[ERROR] No file provided in request")
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    print(f"[UPLOAD] Received file: {file.filename}")

    file_bytes = file.read()
    print(f"[UPLOAD] File size: {len(file_bytes)} bytes")

    processed_image = preprocess_image(file_bytes)
    if processed_image is None:
        return jsonify({"error": "Invalid image"}), 400

    config_settings = settings.get_config()

    print("[OCR] Extracting text using Tesseract...")
    extracted_text = pytesseract.image_to_string(
        processed_image, lang=settings.lang, config=config_settings
    )
    print("[OCR] Text extraction complete.")

    file_id = save_file(file_bytes)

    statement = """
        INSERT INTO images (file_id, extracted_text, tesseract_config)
        VALUES (?, ?, ?)
    """
    print("[DB] Inserting record into database...")
    cursor.execute(statement, (file_id, extracted_text, config_settings))
    conn.commit()
    print("[DB] Insert committed.")

    return jsonify({"text": extracted_text})


@app.route("/fetch/<file_id>")
def get_image(file_id: str):
    print(f"[API] /fetch called for file_id={file_id}")

    cursor.execute("SELECT * FROM images WHERE file_id = ?", (file_id,))
    image = cursor.fetchone()

    if image:
        print("[DB] Record found.")
        return jsonify(
            {
                "file_id": image[0],
                "extracted_text": image[1],
                "tesseract_config": image[2],
            }
        )

    print("[DB] Record not found.")
    return jsonify({"error": "Image not found"}), 404


@app.route("/history")
def get_images():
    print("[API] /history called")

    cursor.execute(
        """
        SELECT file_id, extracted_text, tesseract_config
        FROM images
        ORDER BY upload_timestamp DESC
        LIMIT 10
        """
    )
    images = cursor.fetchall()
    print(f"[DB] Retrieved {len(images)} records.")

    return jsonify(
        [
            {
                "file_id": image[0],
                "extracted_text": image[1],
                "tesseract_config": image[2],
            }
            for image in images
        ]
    )


@app.put("/settings")
def update_settings():
    print("[API] /settings PUT called")

    data = request.json
    if data is None:
        print("[ERROR] No JSON body provided")
        return jsonify({"error": "No data provided"}), 400

    if "psm" in data:
        settings.psm = data["psm"]
        print(f"[SETTINGS] Updated psm to {settings.psm}")

    if "oem" in data:
        settings.oem = data["oem"]
        print(f"[SETTINGS] Updated oem to {settings.oem}")

    if "lang" in data:
        settings.lang = data["lang"]
        print(f"[SETTINGS] Updated lang to {settings.lang}")

    return jsonify({"message": "Settings updated successfully"})


@app.get("/settings")
def get_settings():
    print("[API] /settings GET called")
    return jsonify(
        {
            "psm": settings.psm,
            "oem": settings.oem,
            "lang": settings.lang,
        }
    )


@app.route("/")
def read_root():
    print("[API] / (root) called")
    return render_template("index.jinja.html")
