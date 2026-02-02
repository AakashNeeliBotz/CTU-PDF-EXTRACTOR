"""
Debug Element Status sheet structure to understand column layout
"""
import pandas as pd

EXCEL_PATH = r"c:\Users\Sree Charan\Desktop\fold2\CTU-PDF-EXTRACTOR\Connectivity_Application_Data_TEST_ALL_SHEETS38 (2).xlsx"

def analyze_element_status():
    df = pd.read_excel(EXCEL_PATH, sheet_name='Element Status', header=None)
    
    print("Element Status Sheet Analysis")
    print(f"Total rows: {len(df)}, Total columns: {len(df.columns)}")
    
    print("\n\nFirst 15 rows, first 10 columns:")
    for i in range(15):
        row_data = []
        for j in range(min(10, len(df.columns))):
            val = df.iloc[i, j]
            if pd.notna(val):
                row_data.append(f"[{j}]:{str(val)[:30]}")
        print(f"Row {i}: {', '.join(row_data)}")
    
    print("\n\nLooking for Element Codes (EL-XXXXX pattern):")
    el_codes = []
    for i in range(len(df)):
        for j in range(len(df.columns)):
            val = df.iloc[i, j]
            if pd.notna(val):
                val_str = str(val).strip()
                if val_str.startswith('EL-') and len(val_str) == 8:
                    # Found an Element Code
                    # Get the row data
                    row_vals = {k: str(df.iloc[i, k])[:40] for k in range(min(7, len(df.columns))) if pd.notna(df.iloc[i, k])}
                    el_codes.append({
                        'row': i,
                        'col': j,
                        'code': val_str,
                        'row_data': row_vals
                    })
    
    print(f"\nFound {len(el_codes)} Element Codes")
    print("\nFirst 10 Element Codes with their row data:")
    for item in el_codes[:10]:
        print(f"\n  {item['code']} (row {item['row']}, col {item['col']}):")
        for col, val in item['row_data'].items():
            print(f"    Col {col}: {val}")

if __name__ == "__main__":
    analyze_element_status()
