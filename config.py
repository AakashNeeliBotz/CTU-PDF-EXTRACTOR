# This file contains the master configuration for the entire pipeline.
# It defines all data sources and how they map to the sheets.

# LLM/Transformers configuration removed - using Camelot/PyMuPDF table extraction only

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
    "SN9": "https://@www.ctuil.in/renewable-energy",
    "SN10a": "https://cea.nic.in/psp___a_i/transmission-system-for-integration-of-over-500-gw-non-fossil-capacity-by-2030/?lang=en",
    "SN10b": "https://cea.nic.in/comm-trans/national-committee-on-transmission/?lang=en",
    "SN10c_RECPDCL": "https://www.recpdcl.in/rectpcltender",
    "SN10c_PFCCL_Tender": "https://www.pfcclindia.com/tender-new.php",
    "SN10c_PFCCL_Notice": "https://www.pfcclindia.com/notice.php?AM1",
    "SN10d": "https://cea.nic.in/transmission-reports/?lang=en",
    "SN11": "https://ctuil.in/substation-bulk-consumers",
    "SN12": "https://cea.nic.in/reports/monthly/transmission_construction/",
}

# Prompts removed - not using LLM extraction

# Part 2: Define the configuration for each Excel sheet
# This defines which sources map to which sheets (prompts removed - using Camelot extraction)
SHEET_CONFIG = {
    "Data to be captured": {
        "sources": ["SN1", "SN3", "SN2", "SN4", "SN7", "SN8", "SN9", "SN11"],  # SN1 added first, processes before SN3
    },
    "RE Potential": {
        "sources": ["SN9", "SN10a"],
    },
    "Margin": {
        "sources": ["SN9"],
    },
    "Transformation Capacity": {
        "sources": ["SN9"],
    },
    "Non RE proposed RE Integration": {
        "sources": ["SN9"],
    },
    "Element Status": {
        "sources": ["SN_TBCB", "SN1"],  # Matches Report_TBCB_UC.pdf and now SN1 Annexures
    }
}
