import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Upload directory
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Database file (for future use)
# DB_FILE = BASE_DIR / "data" / "excel_data.duckdb"

# Allowed file extensions
ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".csv"}

# Maximum file size (100MB)
MAX_FILE_SIZE = 100 * 1024 * 1024 