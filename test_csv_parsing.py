"""
Quick test to verify CSV parsing in llm_data_extractor.py
"""

from llm_data_extractor import _parse_csv_to_records, _strip_code_fences

# Test 1: Simple CSV
print("=" * 60)
print("Test 1: Simple CSV")
print("=" * 60)

csv_text_1 = """sr_no,region,state,substation,name_of_developers,application_quantum_mw
1,WR,Gujarat,Khavda,Adani Green Energy,500
2,WR,Rajasthan,Bikaner,ReNew Power,300
3,SR,Karnataka,Pavagada,Azure Power,250"""

records_1 = _parse_csv_to_records(csv_text_1)
print(f"Parsed {len(records_1)} records:")
for r in records_1:
    print(f"  {r}")

# Test 2: CSV with markdown fences
print("\n" + "=" * 60)
print("Test 2: CSV with markdown code fences")
print("=" * 60)

csv_text_2 = """```csv
sr_no,region,state,substation,name_of_developers,application_quantum_mw
1,WR,Gujarat,Khavda,Adani Green Energy,500
2,WR,Rajasthan,Bikaner,ReNew Power,300
```"""

records_2 = _parse_csv_to_records(csv_text_2)
print(f"Parsed {len(records_2)} records:")
for r in records_2:
    print(f"  {r}")

# Test 3: CSV with empty values
print("\n" + "=" * 60)
print("Test 3: CSV with empty values")
print("=" * 60)

csv_text_3 = """sr_no,region,state,substation,name_of_developers,application_quantum_mw,remarks
1,WR,Gujarat,Khavda,Adani Green Energy,500,
2,WR,Rajasthan,,ReNew Power,300,Pending approval
3,SR,Karnataka,Pavagada,Azure Power,,Under construction"""

records_3 = _parse_csv_to_records(csv_text_3)
print(f"Parsed {len(records_3)} records:")
for r in records_3:
    print(f"  {r}")

# Test 4: CSV with quoted fields containing commas
print("\n" + "=" * 60)
print("Test 4: CSV with quoted fields containing commas")
print("=" * 60)

csv_text_4 = """sr_no,region,state,name_of_developers,remarks
1,WR,Gujarat,"Adani Green Energy Ltd, India",Active
2,WR,Rajasthan,"ReNew Power Pvt. Ltd., Mumbai","Pending, awaiting approval"
3,SR,Karnataka,Azure Power,None"""

records_4 = _parse_csv_to_records(csv_text_4)
print(f"Parsed {len(records_4)} records:")
for r in records_4:
    print(f"  {r}")

print("\n" + "=" * 60)
print("✅ All CSV parsing tests complete!")
print("=" * 60)
