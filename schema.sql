PRAGMA foreign_keys=OFF;
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS images (
    file_id VARCHAR(36) PRIMARY KEY,
    extracted_text TEXT,
    upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tesseract_config VARCHAR(255),

    UNIQUE (file_id, tesseract_config) ON CONFLICT REPLACE
)