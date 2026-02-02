"""
Verify the changes made to the Excel file
"""
import pandas as pd
from openpyxl import load_workbook
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

excel_path = r"c:\Users\Sree Charan\Desktop\fold2\CTU-PDF-EXTRACTOR\Connectivity_Application_Data_TEST_ALL_SHEETS38 (2).xlsx"

# Load with headers at row 2
df = pd.read_excel(excel_path, sheet_name="Data to be captured", header=1)

print("="*100)
print("VERIFICATION OF CHANGES")
print("="*100)

# 1. Check if rows 194, 195 (old Excel rows, now adjusted) are gone
print("\n1. Checking rows around old 192-193 Sr.No....")
srno_col = 'Sr.no.'
mask_190_195 = df[srno_col].isin(range(190, 196))
rows = df[mask_190_195]
print(f"Rows with Sr.No. 190-195:")
for idx, row in rows.iterrows():
    print(f"  Sr.No. {row[srno_col]}: {row.get('Name of Developers', 'N/A')}")

# 2. Check Sr.No. 15 Application Quantum
print("\n2. Sr.No. 15 - Application Quantum (MW)(ST II):")
sr15_mask = df[srno_col] == 15
sr15 = df[sr15_mask]
if len(sr15) > 0:
    quantum_col = 'Application Quantum (MW)(ST II)'
    if quantum_col in df.columns:
        print(f"  Value: {sr15.iloc[0][quantum_col]}")
    
    # Also check Mode
    mode_col = 'Mode(Criteria for applying)'
    if mode_col in df.columns:
        print(f"  Mode: {sr15.iloc[0][mode_col]}")

# 3. Check Sr.No. 58
print("\n3. Sr.No. 58 data:")
sr58_mask = df[srno_col] == 58
sr58 = df[sr58_mask]
if len(sr58) > 0:
    print(f"  Substation: {sr58.iloc[0]['Substation']}")
    print(f"  GNA/ST II Application ID: {sr58.iloc[0]['GNA/ST II Application ID']}")
    print(f"  CMETS GNA Approved: {sr58.iloc[0]['CMETS GNA Approved']}")

# 4. Count total rows
print(f"\n4. Total data rows: {len(df)}")

# 5. Check for rows with CMETS = "33, 34"
cmets_col = 'CMETS GNA Approved'
count_both = 0
for val in df[cmets_col]:
    if pd.notna(val):
        val_str = str(val)
        if '33' in val_str and '34' in val_str:
            count_both += 1
print(f"\n5. Rows with both 33 and 34 in CMETS GNA Approved: {count_both}")
