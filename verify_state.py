"""
Verify the current state and check if Sr.No. needs to be regenerated
"""
import pandas as pd
from openpyxl import load_workbook
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

excel_path = r"c:\Users\Sree Charan\Desktop\fold2\CTU-PDF-EXTRACTOR\Connectivity_Application_Data_TEST_ALL_SHEETS38 (2).xlsx"

df = pd.read_excel(excel_path, sheet_name="Data to be captured", header=1)

print("="*100)
print("CURRENT STATE VERIFICATION")
print("="*100)

srno_col = 'Sr.no.'

# Check for gaps in Sr.No.
print(f"\nTotal rows: {len(df)}")

# Get all Sr.No. values
srno_values = df[srno_col].dropna().astype(int).sort_values().tolist()
print(f"Sr.No. range: {min(srno_values)} to {max(srno_values)}")

# Find gaps
expected = set(range(1, max(srno_values) + 1))
actual = set(srno_values)
missing = expected - actual
duplicates = [x for x in srno_values if srno_values.count(x) > 1]

print(f"\nMissing Sr.No.: {sorted(missing)[:20]}..." if len(missing) > 20 else f"\nMissing Sr.No.: {sorted(missing)}")
print(f"Duplicate Sr.No.: {set(duplicates)}")

# Show rows 50-80 range
print("\n" + "="*100)
print("ROWS IN Sr.No. 50-80 RANGE (after deletion)")
print("="*100)

mask = (df[srno_col] >= 50) & (df[srno_col] <= 80)
rows = df[mask].copy()
print(f"\nTotal rows in 50-80 range: {len(rows)}")

for idx, row in rows.iterrows():
    srno = int(row[srno_col])
    substation = str(row['Substation'])[:25] if pd.notna(row['Substation']) else 'N/A'
    developer = str(row['Name of Developers'])[:30] if pd.notna(row['Name of Developers']) else 'N/A'
    app_id = row['GNA/ST II Application ID'] if pd.notna(row['GNA/ST II Application ID']) else 'N/A'
    print(f"  Sr.No. {srno:3d} | {substation:25s} | {developer:30s} | AppID: {app_id}")

# Show rows 30-45 range
print("\n" + "="*100)
print("ROWS IN Sr.No. 30-45 RANGE")
print("="*100)

mask = (df[srno_col] >= 30) & (df[srno_col] <= 45)
rows = df[mask].copy()
print(f"\nTotal rows in 30-45 range: {len(rows)}")

for idx, row in rows.iterrows():
    srno = int(row[srno_col])
    substation = str(row['Substation'])[:25] if pd.notna(row['Substation']) else 'N/A'
    developer = str(row['Name of Developers'])[:30] if pd.notna(row['Name of Developers']) else 'N/A'
    app_id = row['GNA/ST II Application ID'] if pd.notna(row['GNA/ST II Application ID']) else 'N/A'
    print(f"  Sr.No. {srno:3d} | {substation:25s} | {developer:30s} | AppID: {app_id}")
