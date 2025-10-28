"""
Quick test to verify Camelot table extraction works.
"""

import os
from pathlib import Path

# Test imports
print("="*60)
print("TESTING CAMELOT SETUP")
print("="*60)

print("\n[*] Testing imports...")

try:
    import camelot
    print("✅ Camelot imported successfully")
    print(f"   Version: {camelot.__version__ if hasattr(camelot, '__version__') else 'unknown'}")
except ImportError as e:
    print(f"❌ Camelot import failed: {e}")
    print("   Install with: pip install camelot-py[base]")
    exit(1)

try:
    import pandas as pd
    print("✅ Pandas imported successfully")
except ImportError:
    print("❌ Pandas import failed")
    exit(1)

# Test Camelot extraction
print("\n[*] Looking for test PDF...")

test_pdf = None
pdf_dirs = ["downloaded_pdfs/SN3", "downloaded_pdfs/SN1", "downloaded_pdfs"]

for pdf_dir in pdf_dirs:
    if os.path.exists(pdf_dir):
        for file in os.listdir(pdf_dir):
            if file.lower().endswith('.pdf'):
                test_pdf = os.path.join(pdf_dir, file)
                break
    if test_pdf:
        break

if not test_pdf:
    print("❌ No PDF found for testing")
    print("   Place a PDF in downloaded_pdfs/ directory")
    exit(1)

print(f"✅ Found test PDF: {os.path.basename(test_pdf)}")

# Try table extraction
print("\n[*] Testing Camelot table extraction...")
print(f"   File: {test_pdf}")

try:
    # Try lattice first
    print("\n   Attempting 'lattice' flavor...")
    try:
        tables = camelot.read_pdf(test_pdf, pages='1', flavor='lattice')
        print(f"   ✅ Lattice: Found {len(tables)} table(s)")
        
        if len(tables) > 0:
            print(f"\n   First table preview:")
            print(f"   Shape: {tables[0].df.shape}")
            print(f"   Accuracy: {tables[0].accuracy:.2f}%")
            print(f"\n{tables[0].df.head()}")
            
    except Exception as e:
        if 'ghostscript' in str(e).lower():
            print(f"   ⚠️  Lattice failed: Ghostscript not installed")
            print("   Falling back to 'stream' flavor...")
        else:
            print(f"   ⚠️  Lattice failed: {e}")
        
        # Try stream
        print("\n   Attempting 'stream' flavor...")
        tables = camelot.read_pdf(test_pdf, pages='1', flavor='stream')
        print(f"   ✅ Stream: Found {len(tables)} table(s)")
        
        if len(tables) > 0:
            print(f"\n   First table preview:")
            print(f"   Shape: {tables[0].df.shape}")
            print(f"\n{tables[0].df.head()}")

except Exception as e:
    print(f"❌ Camelot extraction failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)

if len(tables) > 0:
    print("\n✅ Camelot is working!")
    print(f"   Extracted {len(tables)} table(s) from first page")
    
    # Save all tables to CSV files
    print("\n[*] Saving tables to CSV files for inspection...")
    output_dir = "camelot_output"
    os.makedirs(output_dir, exist_ok=True)
    
    for i, table in enumerate(tables, 1):
        csv_filename = f"{output_dir}/table_{i}_page1.csv"
        table.df.to_csv(csv_filename, index=False)
        print(f"   ✅ Saved: {csv_filename}")
        print(f"      Shape: {table.df.shape[0]} rows × {table.df.shape[1]} columns")
        print(f"      Accuracy: {table.accuracy:.2f}%")
    
    # Also save combined data from all pages
    print("\n[*] Extracting ALL pages (not just page 1)...")
    try:
        # Extract from all pages
        all_tables = camelot.read_pdf(test_pdf, pages='all', flavor='lattice')
        print(f"   ✅ Found {len(all_tables)} table(s) across all pages")
        
        # Save each table
        for i, table in enumerate(all_tables, 1):
            page_num = table.page if hasattr(table, 'page') else 'unknown'
            csv_filename = f"{output_dir}/table_{i}_page{page_num}.csv"
            table.df.to_csv(csv_filename, index=False)
            print(f"   ✅ Saved: {csv_filename}")
            print(f"      Page: {page_num}, Shape: {table.df.shape[0]} rows × {table.df.shape[1]} columns")
        
        # Combine all tables into one CSV
        if len(all_tables) > 0:
            print("\n[*] Combining all tables into single CSV...")
            combined_dfs = []
            
            for idx, table in enumerate(all_tables):
                df = table.df.copy()
                
                # Use first row as header if it looks like a header
                if not df.empty and len(df) > 1:
                    # Check if first row has text (likely headers)
                    first_row = df.iloc[0]
                    if first_row.astype(str).str.len().mean() > 0:
                        # Set first row as column names
                        df.columns = df.iloc[0].astype(str)
                        df = df[1:].reset_index(drop=True)
                
                if not df.empty:
                    combined_dfs.append(df)
            
            if combined_dfs:
                # Concatenate with ignore_index and reset columns
                combined_df = pd.concat(combined_dfs, ignore_index=True, sort=False)
                
                # Remove completely empty rows/columns
                combined_df = combined_df.dropna(how='all').dropna(axis=1, how='all')
                
                combined_filename = f"{output_dir}/all_tables_combined.csv"
                combined_df.to_csv(combined_filename, index=False)
                print(f"   ✅ Saved combined: {combined_filename}")
                print(f"      Total records: {len(combined_df)} rows")
                print(f"      Total columns: {len(combined_df.columns)}")
                
                # Show first few rows
                print("\n   Preview of combined data (first 5 rows):")
                pd.set_option('display.max_columns', None)
                pd.set_option('display.width', None)
                print(combined_df.head(5).to_string())
                
    except Exception as e:
        print(f"   ⚠️  Error during extraction: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("📊 CSV FILES SAVED")
    print("="*60)
    print(f"\nCheck the '{output_dir}/' directory for:")
    print("  - Individual table CSVs (table_X_pageY.csv)")
    print("  - Combined data (all_tables_combined.csv)")
    print("\nNext steps:")
    print("   1. Open the CSV files in Excel to verify data")
    print("   2. Check if all records are captured")
    print("   3. Compare with original PDF")
    print("   4. If data looks good, run: python test_main_skip_download.py")
else:
    print("\n⚠️  No tables found in test PDF")
    print("   This PDF may not have table structures")
    print("   Try with a different PDF that has clear tables")
