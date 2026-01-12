PRAGMA foreign_keys=OFF;
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS images (
    file_hash VARCHAR(64) PRIMARY KEY,
    extracted_text TEXT,
    upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tesseract_config VARCHAR(255),

    UNIQUE (file_hash, tesseract_config) ON CONFLICT REPLACE
)