"""
Script to explore the Excel file structure - headers and columns
"""
import pandas as pd
from openpyxl import load_workbook

excel_path = r"c:\Users\Sree Charan\Desktop\fold2\CTU-PDF-EXTRACTOR\Connectivity_Application_Data_TEST_ALL_SHEETS38 (2).xlsx"

def explore_data_to_capture():
    """Explore the 'Data to be captured' sheet"""
    print("=" * 80)
    print("EXPLORING: 'Data to be captured' sheet")
    print("=" * 80)
    
    # Read without headers to see raw structure
    df = pd.read_excel(excel_path, sheet_name='Data to be captured', header=None)
    
    print(f"\nTotal rows: {len(df)}")
    print(f"Total columns: {len(df.columns)}")
    
    # Show first 10 rows to understand header structure
    print("\n--- First 10 rows (raw) ---")
    for i in range(min(10, len(df))):
        row_vals = [str(v)[:30] for v in df.iloc[i].tolist() if pd.notna(v) and str(v).strip()]
        print(f"Row {i}: {row_vals[:10]}...")  # First 10 non-empty values
    
    # Find specific columns of interest
    target_cols = [
        "GNA/ST II Application ID",
        "CTS Element Unique Code",
        "DTL Element Unique Code", 
        "ATS Element Code Unique"
    ]
    
    print("\n--- Searching for target columns ---")
    found = {}
    for i in range(min(20, len(df))):  # Search first 20 rows for headers
        for j, val in enumerate(df.iloc[i].tolist()):
            if pd.notna(val):
                val_str = str(val).strip()
                for target in target_cols:
                    if target.lower() in val_str.lower() or val_str.lower() in target.lower():
                        if target not in found:
                            found[target] = (i, j, val_str)
                            print(f"Found '{target}' at Row {i}, Col {j}: '{val_str}'")
    
    return found

def explore_element_status():
    """Explore the 'Element Status' sheet"""
    print("\n" + "=" * 80)
    print("EXPLORING: 'Element Status' sheet")
    print("=" * 80)
    
    # Read without headers to see raw structure
    df = pd.read_excel(excel_path, sheet_name='Element Status', header=None)
    
    print(f"\nTotal rows: {len(df)}")
    print(f"Total columns: {len(df.columns)}")
    
    # Show first 10 rows
    print("\n--- First 10 rows (raw) ---")
    for i in range(min(10, len(df))):
        row_vals = [str(v)[:50] for v in df.iloc[i].tolist() if pd.notna(v) and str(v).strip()]
        print(f"Row {i}: {row_vals}")
    
    # Find Element Code and Element Description columns
    print("\n--- Searching for Element Code and Description columns ---")
    for i in range(min(10, len(df))):
        for j, val in enumerate(df.iloc[i].tolist()):
            if pd.notna(val):
                val_str = str(val).strip().lower()
                if 'element' in val_str or 'code' in val_str or 'description' in val_str:
                    print(f"Row {i}, Col {j}: '{df.iloc[i, j]}'")

def find_all_headers():
    """Find all headers in Data to be captured sheet"""
    print("\n" + "=" * 80)
    print("ALL HEADERS IN 'Data to be captured'")
    print("=" * 80)
    
    df = pd.read_excel(excel_path, sheet_name='Data to be captured', header=None)
    
    # Find the header row (usually has the most non-empty cells with string values)
    header_row = None
    for i in range(min(15, len(df))):
        non_empty = sum(1 for v in df.iloc[i].tolist() if pd.notna(v) and str(v).strip())
        if non_empty > 10:  # Likely a header row
            print(f"\nPotential header row {i} ({non_empty} non-empty cells):")
            headers = [(j, str(v).strip()) for j, v in enumerate(df.iloc[i].tolist()) if pd.notna(v) and str(v).strip()]
            for j, h in headers:
                print(f"  Col {j}: {h}")
            if header_row is None:
                header_row = i
    
    return header_row

if __name__ == "__main__":
    explore_data_to_capture()
    explore_element_status()
    find_all_headers()
