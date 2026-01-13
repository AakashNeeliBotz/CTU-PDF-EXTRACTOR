"""
Unified Pipeline Script
=======================
This script processes both TBCB and Minutes of Meeting PDFs
and generates the final updated Excel file.

Usage:
    python run_pipeline.py
"""

import os
import shutil
import subprocess
import sys

# Configuration
TBCB_PDF = "Report_TBCB_UC.pdf"
MINUTES_PDF = "172838877090Minutes of meeting 34th CMETS NR Meeting held on 20-9-24.pdf"
INTERMEDIATE_EXCEL = "Output_Report_TBCB_UC.xlsx"
TARGET_EXCEL = "Connectivity Application Data 1.xlsx"
OUTPUT_EXCEL = "Connectivity Application Data 1_Updated.xlsx"

def print_header(text):
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)

def check_files():
    """Check if required input files exist."""
    print_header("STEP 0: Checking Input Files")
    
    files = [TBCB_PDF, MINUTES_PDF, TARGET_EXCEL]
    missing = []
    
    for f in files:
        if os.path.exists(f):
            print(f"  ✓ Found: {f}")
        else:
            print(f"  ✗ Missing: {f}")
            missing.append(f)
    
    if missing:
        print("\nError: Missing required files. Please ensure all files are present.")
        return False
    return True

def step1_extract_tbcb():
    """Extract TBCB PDF to intermediate Excel."""
    print_header("STEP 1: Extracting TBCB PDF to Intermediate Excel")
    
    from modules.extractor import PDFExtractor
    
    extractor = PDFExtractor()
    extractor.run(TBCB_PDF, INTERMEDIATE_EXCEL)
    
    if os.path.exists(INTERMEDIATE_EXCEL):
        print(f"  ✓ Created: {INTERMEDIATE_EXCEL}")
        return True
    else:
        print(f"  ✗ Failed to create: {INTERMEDIATE_EXCEL}")
        return False

def step2_populate_tbcb():
    """Populate TBCB data to main Excel with Mode = TBCB."""
    print_header("STEP 2: Populating TBCB Data to Main Excel")
    
    # Import and run populate_excel_v2 main function
    import populate_excel_v2
    populate_excel_v2.main()
    
    print("  ✓ TBCB data populated with Mode = 'TBCB'")
    return True

def step3_append_annexures():
    """Append Annexures from Minutes of Meeting PDF."""
    print_header("STEP 3: Appending Annexures from Minutes of Meeting")
    
    # Import and run annexure_pipeline main function
    import annexure_pipeline
    annexure_pipeline.main()
    
    if os.path.exists(OUTPUT_EXCEL):
        print(f"  ✓ Created: {OUTPUT_EXCEL}")
        return True
    else:
        print(f"  ✗ Failed to create: {OUTPUT_EXCEL}")
        return False

def step4_verify():
    """Verify the final output."""
    print_header("STEP 4: Verification")
    
    import pandas as pd
    
    df = pd.read_excel(OUTPUT_EXCEL, sheet_name='Element Status', header=1)
    
    # Find Mode column
    mode_cols = [c for c in df.columns if 'Mode' in str(c)]
    mode_col = mode_cols[0] if mode_cols else None
    
    total_rows = len(df)
    tbcb_rows = (df[mode_col] == 'TBCB').sum() if mode_col else 0
    
    # Check for Annexure content
    tx_col = [c for c in df.columns if 'Transmission Scope' in str(c)]
    annexure_rows = 0
    if tx_col:
        annexure_rows = df[tx_col[0]].astype(str).str.contains('Annexure-', na=False).sum()
    
    print(f"  Total Rows: {total_rows}")
    print(f"  TBCB Rows (Mode = 'TBCB'): {tbcb_rows}")
    print(f"  Annexure Rows: {annexure_rows}")
    
    return True

def main():
    print("\n" + "=" * 60)
    print("         UNIFIED PDF PROCESSING PIPELINE")
    print("=" * 60)
    print(f"\nInput PDFs:")
    print(f"  1. TBCB: {TBCB_PDF}")
    print(f"  2. Minutes: {MINUTES_PDF}")
    print(f"\nOutput: {OUTPUT_EXCEL}")
    
    # Run all steps
    if not check_files():
        return
    
    if not step1_extract_tbcb():
        return
    
    if not step2_populate_tbcb():
        return
    
    if not step3_append_annexures():
        return
    
    step4_verify()
    
    print_header("PIPELINE COMPLETED SUCCESSFULLY")
    print(f"\nOutput file: {OUTPUT_EXCEL}")
    print("\nPlease review the file to verify the results.")

if __name__ == "__main__":
    main()
