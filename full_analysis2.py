"""
Comprehensive analysis - fixed encoding issue
"""
import pandas as pd
from openpyxl import load_workbook
import re
import sys

# Fix encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Load the Excel file
excel_path = r"c:\Users\Sree Charan\Desktop\fold2\CTU-PDF-EXTRACTOR\Connectivity_Application_Data_TEST_ALL_SHEETS38 (2).xlsx"

# Load with headers at row 2 (0-indexed: header=1)
df = pd.read_excel(excel_path, sheet_name="Data to be captured", header=1)

# Column references
srno_col = 'Sr.no.'
substation_col = 'Substation'
cmets_gna_col = 'CMETS GNA Approved'
app_id_col = 'GNA/ST II Application ID'
mode_col = 'Mode(Criteria for applying)'
app_quantum_col = 'Application Quantum (MW)(ST II)'
coords_col = 'Coordinates'

print("="*100)
print("FINDING 765/400/220kV Bhuj specifically")
print("="*100)

for idx, row in df.iterrows():
    substation_val = str(row[substation_col]) if pd.notna(row[substation_col]) else ''
    if '765' in substation_val and 'Bhuj' in substation_val:
        print(f"\nExcel row {idx+3}:")
        print(f"  Sr.No.: {row[srno_col]}")
        print(f"  Substation: {substation_val}")
        coords_val = str(row[coords_col]).encode('ascii', 'replace').decode()
        print(f"  Coordinates: {coords_val}")
        print(f"  App ID: {row[app_id_col]}")

print("\n" + "="*100)
print("Sr.No. 58 - Full details")
print("="*100)
row_58_mask = df[srno_col] == 58
row_58 = df[row_58_mask]
if len(row_58) > 0:
    idx = row_58.index[0]
    print(f"Sr.No. 58 found at Excel row {idx + 3}")
    for col in df.columns[:20]:
        val = row_58.iloc[0][col]
        if pd.notna(val):
            val_str = str(val).encode('ascii', 'replace').decode()
            print(f"  {col}: {val_str}")
else:
    print("Sr.No. 58 not found!")

print("\n" + "="*100)
print("CMETS GNA Approved - Rows with both 33 AND 34")
print("="*100)
for idx, val in df[cmets_gna_col].items():
    if pd.notna(val):
        val_str = str(val)
        if '33' in val_str and '34' in val_str:
            srno = df.iloc[idx][srno_col] if pd.notna(df.iloc[idx][srno_col]) else 'N/A'
            app_id = df.iloc[idx][app_id_col] if pd.notna(df.iloc[idx][app_id_col]) else 'N/A'
            print(f"  Excel row {idx+3}, Sr.No. {srno}: CMETS = '{val}', AppID = {app_id}")

print("\n" + "="*100)
print("Looking for more ID-like values in Substation (checking various patterns)")
print("="*100)
for idx, val in df[substation_col].items():
    if pd.notna(val):
        val_str = str(val).strip()
        # Check for patterns like 301, 302, etc. but also embedded in text
        if re.search(r'\b30[1-9]\b', val_str) or re.search(r'^\d{3}$', val_str):
            excel_row = idx + 3
            srno = df.iloc[idx][srno_col] if pd.notna(df.iloc[idx][srno_col]) else 'N/A'
            print(f"  Excel row {excel_row}, Sr.No. {srno}: Substation = '{val_str}'")
