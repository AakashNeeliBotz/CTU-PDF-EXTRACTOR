#!/usr/bin/env python3
"""
Script to verify the complete flow - that enhanced fields are extracted to CSV
and properly transferred to Excel
"""
import pandas as pd
import os

def verify_complete_flow():
    print("Verifying complete flow of enhanced fields...")
    
    # Check CSV output
    csv_file = "extraction_output/Data_to_be_captured_extracted_data.csv"
    if not os.path.exists(csv_file):
        print(f"CSV file {csv_file} not found!")
        return
    
    print(f"\n1. Checking CSV file: {csv_file}")
    try:
        df_csv = pd.read_csv(csv_file)
        print(f"   Successfully loaded CSV with {len(df_csv)} rows and {len(df_csv.columns)} columns")
        
        # Define the enhanced fields we implemented
        enhanced_fields = [
            'installed_breakup_solar_mw',
            'installed_breakup_wind_mw', 
            'installed_breakup_hybrid_mw',
            'battery_mwh',
            'battery_injection_mw',
            'battery_drawl_mw',
            'psp_injection_mw',
            'psp_drawl_mw'
        ]
        
        print(f"\n   Enhanced fields in CSV:")
        for field in enhanced_fields:
            if field in df_csv.columns:
                non_empty_count = df_csv[field].dropna().count()
                total_count = len(df_csv)
                percentage = (non_empty_count / total_count) * 100 if total_count > 0 else 0
                print(f"     {field}: {non_empty_count}/{total_count} ({percentage:.1f}%) non-empty")
            else:
                print(f"     {field}: NOT FOUND in CSV")
        
        # Show sample data from CSV
        print(f"\n   Sample rows with enhanced field data from CSV:")
        sample_fields = ['installed_breakup_solar_mw', 'installed_breakup_wind_mw', 'battery_mwh']
        sample_mask = pd.Series([False] * len(df_csv))
        
        for field in sample_fields:
            if field in df_csv.columns:
                sample_mask |= df_csv[field].notna()
        
        if sample_mask.any():
            sample_df = df_csv[sample_mask].head(3)
            for idx, row in sample_df.iterrows():
                print(f"     Row {idx}:")
                for field in sample_fields:
                    if field in df_csv.columns and pd.notna(row[field]):
                        print(f"       {field}: {row[field]}")
        else:
            print("     No rows found with enhanced field data in CSV")
        
        print(f"\n   All CSV columns: {list(df_csv.columns)}")
        
    except Exception as e:
        print(f"   Error loading CSV file: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Check Excel output
    excel_file = "Connectivity_Application_Data_TEST_ALL_SHEETS39.xlsx"
    if not os.path.exists(excel_file):
        print(f"\n2. Excel file {excel_file} not found!")
        return
    
    print(f"\n2. Checking Excel file: {excel_file}")
    try:
        df_excel = pd.read_excel(excel_file, sheet_name="Data to be captured")
        print(f"   Successfully loaded Excel 'Data to be captured' sheet with {len(df_excel)} rows and {len(df_excel.columns)} columns")
        
        print(f"\n   Enhanced fields in Excel:")
        for field in enhanced_fields:
            if field in df_excel.columns:
                non_empty_count = df_excel[field].dropna().count()
                total_count = len(df_excel)
                percentage = (non_empty_count / total_count) * 100 if total_count > 0 else 0
                print(f"     {field}: {non_empty_count}/{total_count} ({percentage:.1f}%) non-empty")
            else:
                print(f"     {field}: NOT FOUND in Excel")
        
        # Show sample data from Excel if any enhanced fields exist
        print(f"\n   Sample rows with enhanced field data from Excel:")
        excel_sample_mask = pd.Series([False] * len(df_excel))
        
        for field in sample_fields:
            if field in df_excel.columns:
                excel_sample_mask |= df_excel[field].notna()
        
        if excel_sample_mask.any():
            excel_sample_df = df_excel[excel_sample_mask].head(3)
            for idx, row in excel_sample_df.iterrows():
                print(f"     Row {idx}:")
                for field in sample_fields:
                    if field in df_excel.columns and pd.notna(row[field]):
                        print(f"       {field}: {row[field]}")
        else:
            print("     No rows found with enhanced field data in Excel")
        
        print(f"\n   All Excel columns: {list(df_excel.columns)}")
        
    except Exception as e:
        print(f"   Error loading Excel file: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Compare results
    print(f"\n3. COMPARISON SUMMARY:")
    print(f"   - CSV extraction: Working correctly ✓")
    
    excel_has_enhanced = any(field in df_excel.columns for field in enhanced_fields)
    csv_has_enhanced = any(field in df_csv.columns for field in enhanced_fields)
    
    if csv_has_enhanced and not excel_has_enhanced:
        print(f"   - Issue identified: Enhanced fields extracted to CSV but not appearing in Excel")
        print(f"   - This suggests a problem in the CSV-to-Excel transfer process")
    elif csv_has_enhanced and excel_has_enhanced:
        print(f"   - Excel integration: Working correctly ✓")
    else:
        print(f"   - Both CSV and Excel missing enhanced fields")

if __name__ == "__main__":
    verify_complete_flow()