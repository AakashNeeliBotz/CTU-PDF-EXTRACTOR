import camelot
import pandas as pd
from field_mappings import normalize_header

pdf_path = "downloaded_pdfs/SN3/175747952599June 25_RE.pdf"

tables = camelot.read_pdf(pdf_path, flavor='lattice', pages='all')

print(f"Found {len(tables)} tables\n")

for i, table in enumerate(tables[:3]):  # Check first 3 tables
    df = table.df
    print(f"=== TABLE {i+1} ===")
    print(f"Shape: {df.shape}")
    print(f"\nFirst 5 rows (raw):")
    print(df.head())
    
    # Find header row
    header_row_idx = 0
    for idx in range(min(5, len(df))):
        row_text = ' '.join(df.iloc[idx].astype(str).str.lower())
        non_null_count = df.iloc[idx].notna().sum()
        print(f"\nRow {idx} text: {row_text[:100]}...")
        print(f"Non-null count: {non_null_count}")
        if non_null_count < 3:
            continue
        if any(indicator in row_text for indicator in [
            'sl. no', 'sl.no', 'serial', 's.no', 's no',
            'application', 'app id', 'applicant',
            'name of', 'developer', 'company',
            'region', 'state', 'substation',
            'capacity', 'quantum', 'mw',
            'date', 'expected', 'connectivity'
        ]):
            header_row_idx = idx
            print(f"***** HEADER ROW FOUND AT INDEX {idx} *****")
            break
    
    # Extract headers
    raw_headers = df.iloc[header_row_idx].astype(str).tolist()
    print(f"\nRaw headers from row {header_row_idx}: {raw_headers}")
    
    normalized_headers = [normalize_header(h) for h in raw_headers]
    print(f"Normalized headers: {normalized_headers}")
    
    print("\n" + "="*80 + "\n")
