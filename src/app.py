from __future__ import annotations

import os

import cv2
import numpy as np
import pytesseract
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)


def preprocess_image(image_bytes: bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    _, processed_image = cv2.threshold(
        image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU  # type: ignore
    )
    return processed_image


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    processed_image = preprocess_image(file.read())
    extracted_text = pytesseract.image_to_string(processed_image, config='--psm 6')

    print(extracted_text)

    return jsonify({"text": extracted_text})


@app.route("/")
def read_root():
    return render_template("index.jinja.html")
