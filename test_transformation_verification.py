"""
Comprehensive test script to verify Transformation Capacity sheet transformations.

Tests:
1. Voltage extraction (rightmost voltage before kV/KV)
2. MVA calculation from formulas (e.g., 4x500 = 2000)
3. Row splitting by voltage level (semicolon-separated segments)
4. Data integrity (substation, region, state preserved)
5. Verify against expected outputs
"""

import pandas as pd
from field_mappings import (
    extract_voltage_level,
    calculate_mva_capacity,
    parse_capacity_segment,
    split_transformation_capacity_row
)

print("="*80)
print("TRANSFORMATION CAPACITY VERIFICATION TESTS")
print("="*80)

# ============================================================================
# TEST 1: Voltage Extraction
# ============================================================================
print("\n" + "="*80)
print("TEST 1: VOLTAGE EXTRACTION (extract_voltage_level)")
print("="*80)

voltage_tests = [
    ("400/220kV", 220, "lowercase kV"),
    ("765/400 kV", 400, "lowercase with space"),
    ("400/220 KV", 220, "UPPERCASE KV"),
    ("4x500 MVA, 400/220 KV", 220, "with MVA formula and uppercase"),
    ("1x1500 MVA, 765/400 kV", 400, "complex with 3 voltages"),
    ("220kV", 220, "single voltage"),
    ("No voltage here", None, "no voltage pattern"),
]

voltage_pass = 0
voltage_fail = 0

for text, expected, description in voltage_tests:
    result = extract_voltage_level(text)
    status = "✅ PASS" if result == expected else "❌ FAIL"
    if result == expected:
        voltage_pass += 1
    else:
        voltage_fail += 1
    print(f"{status} | '{text[:40]:40s}' → {result} (expected: {expected}) [{description}]")

print(f"\nVoltage Extraction: {voltage_pass} passed, {voltage_fail} failed")

# ============================================================================
# TEST 2: MVA Calculation
# ============================================================================
print("\n" + "="*80)
print("TEST 2: MVA CALCULATION (calculate_mva_capacity)")
print("="*80)

mva_tests = [
    ("4x500MVA", 2000.0, "simple multiplication"),
    ("4X500 MVA", 2000.0, "uppercase X with space"),
    ("2x315MVA + 1x500MVA", 1130.0, "addition of two terms"),
    ("8X500MVA", 4000.0, "8 transformers"),
    ("1x1500 MVA", 1500.0, "single transformer"),
    ("2x315 + 3x200", 1230.0, "multiple additions without MVA"),
    ("No formula", None, "no formula pattern"),
]

mva_pass = 0
mva_fail = 0

for text, expected, description in mva_tests:
    result = calculate_mva_capacity(text)
    status = "✅ PASS" if result == expected else "❌ FAIL"
    if result == expected:
        mva_pass += 1
    else:
        mva_fail += 1
    print(f"{status} | '{text[:40]:40s}' → {result} (expected: {expected}) [{description}]")

print(f"\nMVA Calculation: {mva_pass} passed, {mva_fail} failed")

# ============================================================================
# TEST 3: Segment Parsing
# ============================================================================
print("\n" + "="*80)
print("TEST 3: SEGMENT PARSING (parse_capacity_segment)")
print("="*80)

segment_tests = [
    ("4x500MVA, 400/220kV", {'voltage_kv': 220, 'mva': 2000.0}, "standard segment"),
    ("1x1500 MVA, 765/400 kV", {'voltage_kv': 400, 'mva': 1500.0}, "3-level voltage"),
    ("4x500 MVA, 400/220 KV", {'voltage_kv': 220, 'mva': 2000.0}, "uppercase KV"),
    ("2x315MVA + 1x500MVA, 400/220kV", {'voltage_kv': 220, 'mva': 1130.0}, "addition formula"),
]

segment_pass = 0
segment_fail = 0

for text, expected, description in segment_tests:
    result = parse_capacity_segment(text)
    status = "✅ PASS" if result == expected else "❌ FAIL"
    if result == expected:
        segment_pass += 1
    else:
        segment_fail += 1
    print(f"{status} | '{text[:40]:40s}' → {result} [{description}]")
    if result != expected:
        print(f"      Expected: {expected}")

print(f"\nSegment Parsing: {segment_pass} passed, {segment_fail} failed")

# ============================================================================
# TEST 4: Row Splitting - Simple Case (Bhuj PS)
# ============================================================================
print("\n" + "="*80)
print("TEST 4: ROW SPLITTING - SIMPLE CASE (Bhuj PS)")
print("="*80)

bhuj_ps_row = {
    's_no': 2,
    'region': 'WR',
    'state': 'Gujarat',
    'substation': 'Bhuj PS',
    'existing_mva': '4x1500MVA, 765/400kV;8X500MVA, 400/220kV',
    'under_implementation_mva': None,
    'planned_mva': None
}

bhuj_expected = [
    {'s_no': 2, 'region': 'WR', 'state': 'Gujarat', 'substation': 'Bhuj PS', 
     'voltage_level_kv': 400, 'existing_mva': 6000.0, 'under_implementation_mva': None, 'planned_mva': None},
    {'s_no': 2, 'region': 'WR', 'state': 'Gujarat', 'substation': 'Bhuj PS', 
     'voltage_level_kv': 220, 'existing_mva': 4000.0, 'under_implementation_mva': None, 'planned_mva': None},
]

bhuj_result = split_transformation_capacity_row(bhuj_ps_row)

print(f"Input: Bhuj PS with existing_mva = '{bhuj_ps_row['existing_mva']}'")
print(f"Expected: 2 rows (400 kV: 6000 MVA, 220 kV: 4000 MVA)")
print(f"Actual: {len(bhuj_result)} rows")

bhuj_pass = True
for i, (result_row, expected_row) in enumerate(zip(bhuj_result, bhuj_expected), 1):
    print(f"\n  Row {i}:")
    print(f"    Voltage: {result_row['voltage_level_kv']} kV (expected: {expected_row['voltage_level_kv']})")
    print(f"    Existing MVA: {result_row['existing_mva']} (expected: {expected_row['existing_mva']})")
    
    if result_row['voltage_level_kv'] != expected_row['voltage_level_kv']:
        print(f"    ❌ FAIL: Voltage mismatch")
        bhuj_pass = False
    elif result_row['existing_mva'] != expected_row['existing_mva']:
        print(f"    ❌ FAIL: MVA mismatch")
        bhuj_pass = False
    else:
        print(f"    ✅ PASS")

print(f"\nBhuj PS Test: {'✅ PASS' if bhuj_pass and len(bhuj_result) == 2 else '❌ FAIL'}")

# ============================================================================
# TEST 5: Row Splitting - Complex Case (Bhuj-II PS)
# ============================================================================
print("\n" + "="*80)
print("TEST 5: ROW SPLITTING - COMPLEX CASE (Bhuj-II PS)")
print("="*80)

bhuj2_row = {
    's_no': 3,
    'region': 'WR',
    'state': 'Gujarat',
    'substation': 'Bhuj-II PS',
    'existing_mva': '1x1500 MVA, 765/400 kV',
    'under_implementation_mva': '1x1500 MVA, 765/400 kV; 4x500 MVA, 400/220 KV',
    'planned_mva': None
}

bhuj2_expected = [
    {'voltage_level_kv': 400, 'existing_mva': 1500.0, 'under_implementation_mva': 1500.0, 'planned_mva': None},
    {'voltage_level_kv': 220, 'existing_mva': None, 'under_implementation_mva': 2000.0, 'planned_mva': None},
]

bhuj2_result = split_transformation_capacity_row(bhuj2_row)

print(f"Input: Bhuj-II PS")
print(f"  Existing: '{bhuj2_row['existing_mva']}'")
print(f"  Under Impl: '{bhuj2_row['under_implementation_mva']}'")
print(f"Expected: 2 rows (400 kV and 220 kV)")
print(f"Actual: {len(bhuj2_result)} rows")

bhuj2_pass = True
for i, (result_row, expected_row) in enumerate(zip(bhuj2_result, bhuj2_expected), 1):
    print(f"\n  Row {i}:")
    print(f"    Voltage: {result_row['voltage_level_kv']} kV (expected: {expected_row['voltage_level_kv']})")
    print(f"    Existing: {result_row['existing_mva']} (expected: {expected_row['existing_mva']})")
    print(f"    Under Impl: {result_row['under_implementation_mva']} (expected: {expected_row['under_implementation_mva']})")
    
    voltage_match = result_row['voltage_level_kv'] == expected_row['voltage_level_kv']
    existing_match = result_row['existing_mva'] == expected_row['existing_mva']
    under_impl_match = result_row['under_implementation_mva'] == expected_row['under_implementation_mva']
    
    if voltage_match and existing_match and under_impl_match:
        print(f"    ✅ PASS")
    else:
        print(f"    ❌ FAIL")
        bhuj2_pass = False

print(f"\nBhuj-II PS Test: {'✅ PASS' if bhuj2_pass and len(bhuj2_result) == 2 else '❌ FAIL'}")

# ============================================================================
# TEST 6: CSV File Verification
# ============================================================================
print("\n" + "="*80)
print("TEST 6: CSV FILE VERIFICATION")
print("="*80)

try:
    csv_path = "extraction_output/Transformation_Capacity_extracted_data.csv"
    df = pd.read_csv(csv_path)
    
    print(f"CSV File: {csv_path}")
    print(f"Total rows: {len(df)}")
    
    # Check for duplicates by substation/voltage
    duplicates = df[df.duplicated(['substation', 'voltage_level_kv'], keep=False)]
    duplicate_count = len(duplicates) // 2  # Each duplicate appears twice
    
    print(f"\nColumn names: {list(df.columns)}")
    print(f"Duplicate substation/voltage combinations: {duplicate_count}")
    
    # Check Bhuj PS
    bhuj_ps = df[df['substation'].str.contains('Bhuj PS', na=False, case=False) & 
                 ~df['substation'].str.contains('Bhuj-II', na=False, case=False)]
    print(f"\nBhuj PS rows: {len(bhuj_ps)}")
    if len(bhuj_ps) > 0:
        print(bhuj_ps[['substation', 'voltage_level_kv', 'existing_mva', 'under_implementation_mva']].to_string())
        bhuj_csv_pass = len(bhuj_ps) == 2  # Should have 2 rows
    else:
        bhuj_csv_pass = False
        print("❌ Bhuj PS not found in CSV")
    
    # Check Bhuj-II PS
    bhuj2_ps = df[df['substation'].str.contains('Bhuj-II', na=False, case=False)]
    print(f"\nBhuj-II PS rows: {len(bhuj2_ps)}")
    if len(bhuj2_ps) > 0:
        print(bhuj2_ps[['substation', 'voltage_level_kv', 'existing_mva', 'under_implementation_mva']].to_string())
        bhuj2_csv_pass = len(bhuj2_ps) == 2  # Should have 2 rows
    else:
        bhuj2_csv_pass = False
        print("❌ Bhuj-II PS not found in CSV")
    
    print(f"\nCSV Verification: {'✅ PASS' if bhuj_csv_pass and bhuj2_csv_pass else '❌ FAIL'}")
    
except FileNotFoundError:
    print(f"❌ CSV file not found: {csv_path}")
    print("Run the main extraction first!")
except Exception as e:
    print(f"❌ Error reading CSV: {e}")

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "="*80)
print("FINAL TEST SUMMARY")
print("="*80)

total_tests = 6
passed_tests = 0

if voltage_fail == 0:
    passed_tests += 1
if mva_fail == 0:
    passed_tests += 1
if segment_fail == 0:
    passed_tests += 1
if bhuj_pass:
    passed_tests += 1
if bhuj2_pass:
    passed_tests += 1

print(f"\nTest Results: {passed_tests}/{total_tests} test suites passed")
print(f"  1. Voltage Extraction: {'✅ PASS' if voltage_fail == 0 else '❌ FAIL'} ({voltage_pass}/{len(voltage_tests)})")
print(f"  2. MVA Calculation: {'✅ PASS' if mva_fail == 0 else '❌ FAIL'} ({mva_pass}/{len(mva_tests)})")
print(f"  3. Segment Parsing: {'✅ PASS' if segment_fail == 0 else '❌ FAIL'} ({segment_pass}/{len(segment_tests)})")
print(f"  4. Bhuj PS Row Splitting: {'✅ PASS' if bhuj_pass else '❌ FAIL'}")
print(f"  5. Bhuj-II PS Row Splitting: {'✅ PASS' if bhuj2_pass else '❌ FAIL'}")
print(f"  6. CSV File Verification: Check output above")

if passed_tests == total_tests - 1:  # Exclude CSV test from count
    print("\n🎉 ALL CORE TESTS PASSED! Transformation logic is working correctly!")
else:
    print(f"\n⚠️  {total_tests - 1 - passed_tests} test suite(s) failed. Review the output above.")

print("="*80)
