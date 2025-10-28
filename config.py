# This file contains the master configuration for the entire pipeline.
# It defines all data sources and how they map to the sheets and prompts.

# Hugging Face Transformers model configuration (direct GPU inference)
HF_MODEL = "google/gemma-3-4b-it"  # Gemma 3 4B instruction-tuned model

# Legacy Ollama settings (kept for reference, not used)
# OLLAMA_MODEL = "gemma3:4b"
# OLLAMA_URL = "http://localhost:11434"

# Part 1: Define all data source URLs
# This dictionary maps a unique source ID (SNx) to its URL.
DATA_SOURCES = {
    "SN1": "https://ctuil.in/ists-consultation-meeting",
    "SN2": "https://ctuil.in/ists-joint-coordination-meeting",
    "SN3": "https://www.ctuil.in/regenerators",
    "SN4": "https://www.ctuil.in/reallocation_meetings",
    "SN5": "https://www.ctuil.in/bidding-calendar",
    "SN6": "https://cea.nic.in/transmission-reports/?lang=en",
    "SN7": "https://www.ctuil.in/uploads/assets/175040253742List%20of%20applicant%20due%20for%20complaince%20June%20to%20Aug%2725.pdf",
    "SN8": "https://www.ctuil.in/connectivityannexures",
    "SN9": "https://www.ctuil.in/renewable-energy",
    "SN10a": "https://cea.nic.in/psp___a_i/transmission-system-for-integration-of-over-500-gw-non-fossil-capacity-by-2030/?lang=en",
    "SN10b": "https://cea.nic.in/comm-trans/national-committee-on-transmission/?lang=en",
    "SN10c_RECPDCL": "https://www.recpdcl.in/rectpcltender",
    "SN10c_PFCCL_Tender": "https://www.pfcclindia.com/tender-new.php",
    "SN10c_PFCCL_Notice": "https://www.pfcclindia.com/notice.php?AM1",
    "SN10d": "https://cea.nic.in/transmission-reports/?lang=en",
    "SN11": "https://ctuil.in/substation-bulk-consumers",
    "SN12": "https://cea.nic.in/reports/monthly/transmission_construction/",
}

# Part 2: Import the prompts for each sheet
# We keep the large prompt strings in a separate file for clarity.
from prompts import (
    PROMPT_DATA_TO_BE_CAPTURED,
    PROMPT_RE_POTENTIAL,
    PROMPT_MARGIN,
    PROMPT_TRANSFORMATION_CAPACITY,
    PROMPT_ELEMENT_STATUS
)

# Part 3: Define the configuration for each Excel sheet
# This is the "brain" that connects sources and prompts to their target sheets.
SHEET_CONFIG = {
    "Data to be captured": {
        "sources": ["SN1", "SN2", "SN3", "SN4", "SN7", "SN8", "SN9", "SN11"],
        "prompt": PROMPT_DATA_TO_BE_CAPTURED
    },
    "RE Potential": {
        "sources": ["SN9", "SN10a"],
        "prompt": PROMPT_RE_POTENTIAL
    },
    "Margin": {
        "sources": ["SN9"],
        "prompt": PROMPT_MARGIN
    },
    "Transformation Capacity": {
        "sources": ["SN9"],
        "prompt": PROMPT_TRANSFORMATION_CAPACITY
    },
    "Element Status": {
        "sources": ["SN10b", "SN10c_RECPDCL", "SN10c_PFCCL_Tender", "SN10c_PFCCL_Notice", "SN10d"],
        "prompt": PROMPT_ELEMENT_STATUS
    }
}
