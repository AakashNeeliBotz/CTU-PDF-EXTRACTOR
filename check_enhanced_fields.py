#!/usr/bin/env python3
"""
Script to check if the enhanced fields (solar, wind, hybrid, battery, etc.) 
have been populated in the output Excel file.
"""
import pandas as pd
import os

def check_enhanced_fields():
    # Check if output file exists
    output_file = "Connectivity_Application_Data_TEST_ALL_SHEETS39.xlsx"
    
    if not os.path.exists(output_file):
        print(f"Output file {output_file} not found!")
        return
    
    print(f"Checking enhanced fields in {output_file}")
    
    # Load the "Data to be captured" sheet
    try:
        df = pd.read_excel(output_file, sheet_name="Data to be captured")
        print(f"Successfully loaded 'Data to be captured' sheet with {len(df)} rows")
        
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
        
        print("\nEnhanced fields to check:", enhanced_fields)
        print("\nField population status:")
        
        for field in enhanced_fields:
            if field in df.columns:
                non_empty_count = df[field].dropna().count()
                total_count = len(df)
                percentage = (non_empty_count / total_count) * 100 if total_count > 0 else 0
                print(f"  {field}: {non_empty_count}/{total_count} ({percentage:.1f}%) non-empty")
            else:
                print(f"  {field}: NOT FOUND in sheet")
        
        # Show sample rows that have enhanced field data
        print(f"\nSample rows with enhanced field data:")
        sample_fields = ['installed_breakup_solar_mw', 'installed_breakup_wind_mw', 'battery_mwh']
        sample_mask = pd.Series([False] * len(df))
        
        for field in sample_fields:
            if field in df.columns:
                sample_mask |= df[field].notna()
        
        if sample_mask.any():
            sample_df = df[sample_mask].head(5)
            for idx, row in sample_df.iterrows():
                print(f"\n  Row {idx}:")
                for field in sample_fields:
                    if field in df.columns and pd.notna(row[field]):
                        print(f"    {field}: {row[field]}")
        else:
            print("  No rows found with enhanced field data")
        
        # Show column names to verify all expected fields exist
        print(f"\nAll columns in 'Data to be captured' sheet:")
        for i, col in enumerate(df.columns.tolist()):
            print(f"  {i+1:2d}. {col}")
            
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_enhanced_fields()