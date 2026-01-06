"""
Configuration module for PDF table extraction
"""
import os
from loguru import logger

# File paths
PDFS_DIR = "pdfs"
OUTPUT_DIR = "extracted_tables"
LOG_FILE = "extraction.log"

# Default PDF path
DEFAULT_PDF_PATH = r"C:\AkashNeeli\pdfs\172838877090Minutes of meeting 34th CMETS NR Meeting held on 20-9-24.pdf"

# Camelot settings
CAMELOT_SETTINGS = {
    'pages': '11-end',
    'line_scale': 40  # Adjust this value based on table border thickness
}

# Output formats
OUTPUT_FORMATS = ['csv', 'excel', 'json']

# Configure logger
logger.remove()  # Remove default handler
logger.add(LOG_FILE, rotation="10 MB", level="INFO")
logger.add(lambda msg: print(msg, end=''))  # Also print to console

def create_output_directory():
    """Create directory for output files if it doesn't exist"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        logger.info(f"Created output directory: {OUTPUT_DIR}")