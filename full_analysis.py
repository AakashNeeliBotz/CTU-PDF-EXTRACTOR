"""
Comprehensive analysis and correction script for the Data to be captured sheet
"""
import pandas as pd
from openpyxl import load_workbook
import re

# Load the Excel file
excel_path = r"c:\Users\Sree Charan\Desktop\fold2\CTU-PDF-EXTRACTOR\Connectivity_Application_Data_TEST_ALL_SHEETS38 (2).xlsx"

# Load with headers at row 2 (0-indexed: header=1)
df = pd.read_excel(excel_path, sheet_name="Data to be captured", header=1)

print("="*100)
print("FULL ANALYSIS OF DATA TO BE CAPTURED SHEET")
print("="*100)

# Column references
srno_col = 'Sr.no.'
substation_col = 'Substation'
cmets_gna_col = 'CMETS GNA Approved'
app_id_col = 'GNA/ST II Application ID'
mode_col = None
app_quantum_col = None
coords_col = 'Coordinates'

# Find Mode and Application Quantum columns
for col in df.columns:
    col_str = str(col).lower()
    if 'mode' in col_str or 'criteria' in col_str:
        mode_col = col
        print(f"Mode column found: {col}")
    if 'quantum' in col_str and 'st ii' in col_str.lower():
        app_quantum_col = col
        print(f"Application Quantum column found: {col}")

print("\n" + "="*100)
print("1. DUPLICATE CHECK - Rows 65-75 by Sr.No.")
print("="*100)
mask_65_75 = df[srno_col].isin(range(65, 76))
rows_65_75 = df[mask_65_75].copy()
print(f"\nRows with Sr.No. 65-75 found: {len(rows_65_75)}")
if len(rows_65_75) > 0:
    print("\nSr.No. values found:")
    for idx, row in rows_65_75.iterrows():
        print(f"  DataFrame idx {idx} (Excel row {idx+3}): Sr.No. = {row[srno_col]}, Substation = {row[substation_col]}")

# Check for duplicates
duplicates_65_75 = rows_65_75[rows_65_75.duplicated(subset=[srno_col], keep=False)]
if len(duplicates_65_75) > 0:
    print(f"\n*** DUPLICATES FOUND in 65-75: ***")
    for idx, row in duplicates_65_75.iterrows():
        print(f"  Excel row {idx+3}: Sr.No. = {row[srno_col]}")

print("\n" + "="*100)
print("1b. DUPLICATE CHECK - Rows 35-40 by Sr.No.")
print("="*100)
mask_35_40 = df[srno_col].isin(range(35, 41))
rows_35_40 = df[mask_35_40].copy()
print(f"\nRows with Sr.No. 35-40 found: {len(rows_35_40)}")
if len(rows_35_40) > 0:
    print("\nSr.No. values found:")
    for idx, row in rows_35_40.iterrows():
        print(f"  DataFrame idx {idx} (Excel row {idx+3}): Sr.No. = {row[srno_col]}, Substation = {row[substation_col]}")

duplicates_35_40 = rows_35_40[rows_35_40.duplicated(subset=[srno_col], keep=False)]
if len(duplicates_35_40) > 0:
    print(f"\n*** DUPLICATES FOUND in 35-40: ***")
    for idx, row in duplicates_35_40.iterrows():
        print(f"  Excel row {idx+3}: Sr.No. = {row[srno_col]}")

print("\n" + "="*100)
print("2. ROWS 194 and 195 (Excel rows)")
print("="*100)
# Excel row 194 = header(2) + data_index(192) = data at index 192
# Excel row 195 = header(2) + data_index(193) = data at index 193
for target_excel_row in [194, 195]:
    data_idx = target_excel_row - 3  # header is row 2, data starts row 3
    if data_idx < len(df) and data_idx >= 0:
        print(f"\nExcel row {target_excel_row} (data index {data_idx}):")
        row = df.iloc[data_idx]
        for col in [srno_col, 'Region', 'State', substation_col, 'Name of Developers', app_id_col]:
            if col in df.columns:
                val = row[col]
                if pd.notna(val):
                    print(f"  {col}: {val}")
    else:
        print(f"\nExcel row {target_excel_row} does not exist in data")

print("\n" + "="*100)
print("3. SUBSTATION Column - Checking for ID values (301, 302, 303, etc.)")
print("="*100)
id_pattern = re.compile(r'^(\d{3})$')
found_ids = []
for idx, val in df[substation_col].items():
    if pd.notna(val):
        val_str = str(val).strip()
        if id_pattern.match(val_str):
            excel_row = idx + 3
            srno = df.iloc[idx][srno_col] if pd.notna(df.iloc[idx][srno_col]) else 'N/A'
            app_id = df.iloc[idx][app_id_col] if pd.notna(df.iloc[idx][app_id_col]) else 'N/A'
            print(f"  Excel row {excel_row}, Sr.No. {srno}: Substation = '{val_str}' (looks like ID), Current AppID = {app_id}")
            found_ids.append((idx, val_str))

if not found_ids:
    print("  No ID-like values (301, 302, 303) found in Substation column")

print("\n" + "="*100)
print("4. Sr.No. 15 - Application Quantum and Mode check")
print("="*100)
row_15_mask = df[srno_col] == 15
row_15 = df[row_15_mask]
if len(row_15) > 0:
    idx = row_15.index[0]
    print(f"Sr.No. 15 found at Excel row {idx + 3}")
    for col in df.columns:
        val = row_15.iloc[0][col]
        if pd.notna(val):
            print(f"  {col}: {val}")
    
    if app_quantum_col:
        quantum_val = row_15.iloc[0][app_quantum_col]
        print(f"\n  *** Application Quantum value: {quantum_val}")
    
    if mode_col:
        mode_val = row_15.iloc[0][mode_col]
        print(f"  *** Mode value: {mode_val}")
    else:
        print("  *** Mode column not found in headers")
else:
    print("Sr.No. 15 not found!")

print("\n" + "="*100)
print("5. 765/400/220kV Bhuj - Coordinates check")
print("="*100)
bhuj_mask = df[substation_col].astype(str).str.contains('Bhuj', case=False, na=False)
bhuj_rows = df[bhuj_mask]
if len(bhuj_rows) > 0:
    for idx, row in bhuj_rows.iterrows():
        print(f"\nExcel row {idx+3}:")
        print(f"  Sr.No.: {row[srno_col]}")
        print(f"  Substation: {row[substation_col]}")
        print(f"  Coordinates: {row[coords_col]}")
else:
    print("No rows found with 'Bhuj' in Substation")

print("\n" + "="*100)
print("6. Sr.No. 58 - Substation check")
print("="*100)
row_58_mask = df[srno_col] == 58
row_58 = df[row_58_mask]
if len(row_58) > 0:
    idx = row_58.index[0]
    print(f"Sr.No. 58 found at Excel row {idx + 3}")
    print(f"  Substation: {row_58.iloc[0][substation_col]}")
    print(f"  GNA/ST II Application ID: {row_58.iloc[0][app_id_col]}")
    print(f"  CMETS GNA Approved: {row_58.iloc[0][cmets_gna_col]}")
else:
    print("Sr.No. 58 not found!")

print("\n" + "="*100)
print("7. CMETS GNA Approved - Rows with both 33 AND 34")
print("="*100)
rows_with_both = []
for idx, val in df[cmets_gna_col].items():
    if pd.notna(val):
        val_str = str(val)
        if '33' in val_str and '34' in val_str:
            srno = df.iloc[idx][srno_col] if pd.notna(df.iloc[idx][srno_col]) else 'N/A'
            app_id = df.iloc[idx][app_id_col] if pd.notna(df.iloc[idx][app_id_col]) else 'N/A'
            print(f"  Excel row {idx+3}, Sr.No. {srno}: CMETS GNA Approved = '{val}', AppID = {app_id}")
            rows_with_both.append((idx, val, app_id))

if not rows_with_both:
    print("  No rows found with both 33 and 34 in CMETS GNA Approved")

print("\n" + "="*100)
print("SUMMARY")
print("="*100)
print(f"Total data rows: {len(df)}")
print(f"Duplicates found in 65-75: {len(duplicates_65_75)}")
print(f"Duplicates found in 35-40: {len(duplicates_35_40)}")
print(f"ID-like values in Substation: {len(found_ids)}")
print(f"Rows with both 33 and 34 in CMETS: {len(rows_with_both)}")
