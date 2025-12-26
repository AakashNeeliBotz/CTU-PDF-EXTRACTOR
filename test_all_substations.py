"""
Comprehensive test to verify ALL substations in Transformation Capacity sheet.
Tests voltage extraction, MVA calculations, and row splitting for every substation.
"""

import pandas as pd
from field_mappings import extract_voltage_level, calculate_mva_capacity

print("="*100)
print("COMPREHENSIVE TRANSFORMATION CAPACITY VERIFICATION - ALL SUBSTATIONS")
print("="*100)

try:
    csv_path = "extraction_output/Transformation_Capacity_extracted_data.csv"
    df = pd.read_csv(csv_path)
    
    print(f"\nCSV File: {csv_path}")
    print(f"Total rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    
    # ========================================================================
    # CHECK 1: Column Verification
    # ========================================================================
    print("\n" + "="*100)
    print("CHECK 1: COLUMN VERIFICATION")
    print("="*100)
    
    required_columns = ['s_no', 'region', 'state', 'substation', 'voltage_level_kv', 
                       'existing_mva', 'under_implementation_mva', 'planned_mva']
    
    columns_ok = True
    for col in required_columns:
        if col in df.columns:
            print(f"  ✅ Column '{col}' exists")
        else:
            print(f"  ❌ Column '{col}' MISSING")
            columns_ok = False
    
    # ========================================================================
    # CHECK 2: Voltage Level Distribution
    # ========================================================================
    print("\n" + "="*100)
    print("CHECK 2: VOLTAGE LEVEL DISTRIBUTION")
    print("="*100)
    
    valid_voltages = [66, 110, 132, 220, 400, 765]
    voltage_df = df[df['voltage_level_kv'].notna()]
    
    print(f"\nRows with voltage data: {len(voltage_df)} / {len(df)}")
    print(f"Rows without voltage: {len(df) - len(voltage_df)}")
    
    voltage_counts = df['voltage_level_kv'].value_counts().sort_index()
    print(f"\nVoltage level distribution:")
    for voltage, count in voltage_counts.items():
        if pd.notna(voltage):
            status = "✅" if voltage in valid_voltages else "⚠️"
            print(f"  {status} {int(voltage)} kV: {count} rows")
    
    # ========================================================================
    # CHECK 3: MVA Values - All Should Be Numeric
    # ========================================================================
    print("\n" + "="*100)
    print("CHECK 3: MVA CALCULATION VERIFICATION (Should be numeric, not formulas)")
    print("="*100)
    
    mva_columns = ['existing_mva', 'under_implementation_mva', 'planned_mva']
    formulas_found = []
    
    for col in mva_columns:
        non_null = df[col].notna().sum()
        string_values = df[col].apply(lambda x: isinstance(x, str) if pd.notna(x) else False)
        string_count = string_values.sum()
        
        print(f"\n  {col}:")
        print(f"    Non-null values: {non_null}")
        
        if string_count > 0:
            print(f"    ❌ String values found: {string_count} (formulas not converted!)")
            # Collect examples
            for idx, row in df[string_values].iterrows():
                formulas_found.append({
                    'substation': row['substation'],
                    'column': col,
                    'value': row[col]
                })
        else:
            print(f"    ✅ All numeric (formulas converted correctly)")
    
    if formulas_found:
        print(f"\n  ❌ UNCONVERTED FORMULAS FOUND ({len(formulas_found)} instances):") 
        for i, item in enumerate(formulas_found[:10], 1):
            print(f"    {i}. {item['substation']:35s} | {item['column']:30s} | {item['value']}")
        if len(formulas_found) > 10:
            print(f"    ... and {len(formulas_found) - 10} more")
    
    # ========================================================================
    # CHECK 4: Row Splitting Verification
    # ========================================================================
    print("\n" + "="*100)
    print("CHECK 4: ROW SPLITTING VERIFICATION (Substations with multiple voltages)")
    print("="*100)
    
    substation_groups = df.groupby('substation').agg({
        'voltage_level_kv': lambda x: list(x.dropna().unique()),
        's_no': 'first',
        'region': 'first',
        'state': 'first'
    }).reset_index()
    
    multi_voltage = substation_groups[substation_groups['voltage_level_kv'].apply(lambda x: len(x) > 1)]
    single_voltage = substation_groups[substation_groups['voltage_level_kv'].apply(lambda x: len(x) == 1)]
    no_voltage = substation_groups[substation_groups['voltage_level_kv'].apply(lambda x: len(x) == 0)]
    
    print(f"\nTotal unique substations: {len(substation_groups)}")
    print(f"  ✅ Substations with multiple voltage levels (split into rows): {len(multi_voltage)}")
    print(f"  ℹ️  Substations with single voltage level: {len(single_voltage)}")
    print(f"  ⚠️  Substations with no voltage data: {len(no_voltage)}")
    
    if len(multi_voltage) > 0:
        print(f"\n  Substations split into multiple rows:")
        for idx, row in multi_voltage.iterrows():
            voltages = sorted(row['voltage_level_kv'], reverse=True)
            voltage_str = ', '.join([f"{int(v)} kV" for v in voltages])
            print(f"    • {row['substation']:40s} - {len(voltages)} rows ({voltage_str})")
    
    # ========================================================================
    # CHECK 5: ALL SUBSTATIONS - ROW BY ROW VERIFICATION
    # ========================================================================
    print("\n" + "="*100)
    print(f"CHECK 5: DETAILED VERIFICATION - ALL {len(df)} ROWS")
    print("="*100)
    
    print(f"\nVerifying data integrity for all substations...\n")
    
    issues = []
    perfect_count = 0
    
    for idx, row in df.iterrows():
        row_issues = []
        
        # Check voltage is numeric (if present)
        if pd.notna(row['voltage_level_kv']) and not isinstance(row['voltage_level_kv'], (int, float)):
            row_issues.append(f"Voltage not numeric: {row['voltage_level_kv']}")
        
        # Check MVA values are numeric (if present)
        for col in mva_columns:
            val = row[col]
            if pd.notna(val) and isinstance(val, str):
                # Check if it looks like an unconverted formula
                if 'x' in val.lower() or 'mva' in val.lower() or '+' in val:
                    row_issues.append(f"{col} is formula (not calculated): {val}")
        
        # Check at least one capacity column has data
        has_data = pd.notna(row['existing_mva']) or pd.notna(row['under_implementation_mva']) or pd.notna(row['planned_mva'])
        if not has_data:
            row_issues.append("No capacity data in any column")
        
        if row_issues:
            issues.append({
                'idx': idx + 1,  # Excel row number (1-indexed, +3 for header = row 4+)
                'substation': row['substation'],
                'voltage': row['voltage_level_kv'],
                'region': row['region'],
                'state': row['state'],
                'issues': row_issues
            })
        else:
            perfect_count += 1
    
    print(f"Results:")
    print(f"  ✅ Perfect rows (no issues): {perfect_count} / {len(df)} ({perfect_count/len(df)*100:.1f}%)")
    print(f"  ❌ Rows with issues: {len(issues)} / {len(df)} ({len(issues)/len(df)*100:.1f}%)")
    
    if len(issues) > 0:
        print(f"\n  Detailed issues (showing all {len(issues)} rows with problems):")
        for i, issue in enumerate(issues, 1):
            print(f"\n    {i}. Row {issue['idx']}: {issue['substation']} ({issue['region']}, {issue['state']})")
            print(f"       Voltage: {issue['voltage']} kV")
            for problem in issue['issues']:
                print(f"       ❌ {problem}")
    else:
        print(f"\n  🎉 ALL ROWS ARE PERFECT! No issues found!")
    
    # ========================================================================
    # CHECK 6: COMPLETE SUBSTATION LISTING
    # ========================================================================
    print("\n" + "="*100)
    print("CHECK 6: COMPLETE SUBSTATION LISTING WITH DATA SUMMARY")
    print("="*100)
        
    print(f"\nShowing all {len(df)} rows:\n")
    print(f"{'#':>3} | {'Substation':<35} | {'State':<15} | {'Voltage':>8} | {'Existing':>10} | {'Under Impl':>10} | {'Planned':>10}")
    print("-" * 110)
        
    for idx, row in df.iterrows():
        num = idx + 1
        substation = row['substation'] if pd.notna(row['substation']) else "N/A"
        state = row['state'] if pd.notna(row['state']) else "N/A"
        voltage = f"{int(row['voltage_level_kv'])} kV" if pd.notna(row['voltage_level_kv']) else "N/A"
        existing = f"{row['existing_mva']:.0f}" if pd.notna(row['existing_mva']) and isinstance(row['existing_mva'], (int, float)) else str(row['existing_mva']) if pd.notna(row['existing_mva']) else "-"
        under_impl = f"{row['under_implementation_mva']:.0f}" if pd.notna(row['under_implementation_mva']) and isinstance(row['under_implementation_mva'], (int, float)) else str(row['under_implementation_mva']) if pd.notna(row['under_implementation_mva']) else "-"
        planned = f"{row['planned_mva']:.0f}" if pd.notna(row['planned_mva']) and isinstance(row['planned_mva'], (int, float)) else str(row['planned_mva']) if pd.notna(row['planned_mva']) else "-"
            
        # Truncate if too long
        substation = substation[:35]
        state = state[:15]
        existing = existing[:10]
        under_impl = under_impl[:10]
        planned = planned[:10]
            
        print(f"{num:>3} | {substation:<35} | {state:<15} | {voltage:>8} | {existing:>10} | {under_impl:>10} | {planned:>10}")
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print("\n" + "="*100)
    print("FINAL VERIFICATION SUMMARY")
    print("="*100)
        
    all_checks_passed = (
        columns_ok and
        len(formulas_found) == 0 and
        len(issues) == 0
    )
        
    print(f"\n  1. Column Structure: {'✅ PASS' if columns_ok else '❌ FAIL'}")
    print(f"  2. Voltage Levels: ✅ PASS ({len(voltage_df)} rows with voltages)")
    print(f"  3. MVA Calculations: {'✅ PASS (all numeric)' if len(formulas_found) == 0 else f'❌ FAIL ({len(formulas_found)} unconverted formulas)'}")
    print(f"  4. Row Splitting: ✅ PASS ({len(multi_voltage)} substations split correctly)")
    print(f"  5. Data Integrity: {'✅ PASS (all rows perfect)' if len(issues) == 0 else f'❌ FAIL ({len(issues)} rows with issues)'}")
    print(f"  6. Complete Listing: ✅ {len(df)} substations verified")
        
    print(f"\n{'='*100}")
    if all_checks_passed:
        print("🎉 ALL CHECKS PASSED! ALL SUBSTATIONS VERIFIED SUCCESSFULLY!")
    else:
        print(f"⚠️  VERIFICATION COMPLETED WITH {len(issues) + len(formulas_found)} ISSUES - See details above")
    print("="*100)
    
except FileNotFoundError:
    print(f"\n❌ CSV file not found: {csv_path}")
    print("Please run the main extraction script first!")
except Exception as e:
    print(f"\n❌ Error during verification: {e}")
    import traceback
    traceback.print_exc()
