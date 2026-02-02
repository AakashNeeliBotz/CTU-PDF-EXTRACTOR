"""
Deep analysis of potential duplicates in Sr.No. 65-75 and 35-40
Compare full row data to find true duplicates
"""
import pandas as pd
from openpyxl import load_workbook
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

excel_path = r"c:\Users\Sree Charan\Desktop\fold2\CTU-PDF-EXTRACTOR\Connectivity_Application_Data_TEST_ALL_SHEETS38 (2).xlsx"

# Load with headers at row 2
df = pd.read_excel(excel_path, sheet_name="Data to be captured", header=1)

print("="*120)
print("DEEP ANALYSIS OF POTENTIAL DUPLICATES")
print("="*120)

# Key columns to compare
srno_col = 'Sr.no.'
substation_col = 'Substation'
developer_col = 'Name of Developers'
app_id_col = 'GNA/ST II Application ID'

# Clean function
def clean_str(val):
    if pd.isna(val):
        return ''
    return str(val).strip().lower().replace('\n', ' ').replace('\r', ' ')

# ============================================================================
# ANALYZE Sr.No. 54-75 range
# ============================================================================
print("\n" + "="*120)
print("ANALYSIS OF Sr.No. 54-75 RANGE")
print("="*120)

# Get rows in range 54-75
mask = (df[srno_col] >= 54) & (df[srno_col] <= 75)
rows_54_75 = df[mask].copy()

print(f"\nTotal rows in Sr.No. 54-75: {len(rows_54_75)}")
print("\nDetailed listing:")
print("-"*120)

for idx, row in rows_54_75.iterrows():
    srno = row[srno_col]
    substation = clean_str(row[substation_col])
    developer = clean_str(row[developer_col])[:40]
    app_id = row[app_id_col] if pd.notna(row[app_id_col]) else 'N/A'
    excel_row = idx + 3  # header at row 2, data starts at row 3
    print(f"Excel Row {excel_row:3d} | Sr.No. {int(srno):3d} | {substation:25s} | {developer:40s} | AppID: {app_id}")

# ============================================================================
# FIND DUPLICATES by comparing content
# ============================================================================
print("\n" + "="*120)
print("FINDING TRUE DUPLICATES (Same Substation + Developer + AppID)")
print("="*120)

# Create a comparison key
df['compare_key'] = df.apply(lambda r: (
    clean_str(r[substation_col]),
    clean_str(r[developer_col]),
    str(r[app_id_col]).strip() if pd.notna(r[app_id_col]) else ''
), axis=1)

# Find duplicates
duplicates = df[df.duplicated(subset='compare_key', keep=False)].copy()
duplicates = duplicates.sort_values('compare_key')

print(f"\nFound {len(duplicates)} rows that are potential duplicates:")
print("-"*120)

if len(duplicates) > 0:
    current_key = None
    for idx, row in duplicates.iterrows():
        if row['compare_key'] != current_key:
            current_key = row['compare_key']
            print(f"\n--- Duplicate Group ---")
        
        srno = row[srno_col]
        substation = clean_str(row[substation_col])
        developer = clean_str(row[developer_col])[:40]
        app_id = row[app_id_col] if pd.notna(row[app_id_col]) else 'N/A'
        excel_row = idx + 3
        print(f"  Excel Row {excel_row:3d} | Sr.No. {int(srno):3d} | {substation:25s} | {developer:40s} | {app_id}")

# ============================================================================
# Specifically compare Sr.No. 54-64 with 65-75
# ============================================================================
print("\n" + "="*120)
print("COMPARING Sr.No. 54-64 with Sr.No. 65-75")
print("="*120)

rows_54_64 = df[(df[srno_col] >= 54) & (df[srno_col] <= 64)].reset_index(drop=True)
rows_65_75 = df[(df[srno_col] >= 65) & (df[srno_col] <= 75)].reset_index(drop=True)

print(f"\nRows in 54-64: {len(rows_54_64)}")
print(f"Rows in 65-75: {len(rows_65_75)}")

matches = []
for i in range(min(len(rows_54_64), len(rows_65_75))):
    row1 = rows_54_64.iloc[i]
    row2 = rows_65_75.iloc[i]
    
    sub1 = clean_str(row1[substation_col])
    sub2 = clean_str(row2[substation_col])
    dev1 = clean_str(row1[developer_col])
    dev2 = clean_str(row2[developer_col])
    app1 = str(row1[app_id_col]).strip() if pd.notna(row1[app_id_col]) else ''
    app2 = str(row2[app_id_col]).strip() if pd.notna(row2[app_id_col]) else ''
    
    # Check if they match
    sub_match = sub1 == sub2
    dev_match = dev1 == dev2 or dev1 in dev2 or dev2 in dev1
    app_match = app1 == app2
    
    srno1 = int(row1[srno_col])
    srno2 = int(row2[srno_col])
    
    print(f"\nSr.No. {srno1} vs Sr.No. {srno2}:")
    print(f"  Substation: '{sub1}' vs '{sub2}' - {'MATCH' if sub_match else 'DIFF'}")
    print(f"  Developer:  '{dev1[:30]}' vs '{dev2[:30]}' - {'MATCH' if dev_match else 'DIFF'}")
    print(f"  App ID:     '{app1}' vs '{app2}' - {'MATCH' if app_match else 'DIFF'}")
    
    if sub_match and dev_match:
        matches.append((srno1, srno2))
        print(f"  >>> DUPLICATE PAIR FOUND!")

print(f"\n\nTotal duplicate pairs found: {len(matches)}")
if matches:
    print("Pairs:")
    for m in matches:
        print(f"  Sr.No. {m[0]} = Sr.No. {m[1]}")
