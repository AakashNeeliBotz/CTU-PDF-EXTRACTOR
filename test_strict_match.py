# test_strict_match.py - Test substation extraction patterns
from test_main_skip_download import extract_sn1_substation_from_text

def clear_cache():
    if hasattr(extract_sn1_substation_from_text, '_sn1_substation_cache'):
        delattr(extract_sn1_substation_from_text, '_sn1_substation_cache')

# Test text simulating real PDF scenarios
test_text = '''
It was agreed to grant 200 MW connectivity to M/s ACME Sunny Energy at Ramgarh-II PS.
Accordingly, it was agreed to grant 350 MW connectivity to M/s Amplus Centaur Solar Private Limited at 220 kV Sirohi(HVDC) PS.
it was proposed to grant connectivity of 150 MW to M/s Adani Renewable Energy Holding Eighteen Limited at 400 kV Bhadla-IV PS in sharing.
M/s Adani Renewable Energy Holding Four Limited (App No. 2200000811) was earlier granted connectivity of 765 MW at of Bhadla-IV PS through 400kV S/c line.
It was informed that M/s ACME Solar Holdings Limited vide mail dated 16.09.2024 has withdrawn the above application.
It was informed that M/s SAEL Industries Limited vide mail dated 17.09.2024 has withdrawn their application.
'''

print("=" * 70)
print("TEST: Substation Extraction - All Patterns")
print("=" * 70)

tests = [
    ("ACME Sunny Energy Pvt Ltd", "Ramgarh-II", "agreed to grant X MW connectivity to"),
    ("Amplus Centaur Solar Private Limited", "Sirohi", "agreed to grant with (HVDC)"),
    ("Adani Renewable Energy Holding Eighteen Limited", "Bhadla-IV", "proposed to grant connectivity of X MW to"),
    ("Adani Renewable Energy Holding Four Limited", "Bhadla-IV", "REVERSED: M/s Developer was earlier granted at"),
    ("ACME Solar Holdings Limited", "", "WITHDRAWN - should be empty"),
    ("SAEL Industries Limited", "", "WITHDRAWN - should be empty"),
]

passed = 0
for developer, expected, description in tests:
    clear_cache()
    result = extract_sn1_substation_from_text(test_text, developer)
    
    # Check if result matches expected (partial match for non-empty)
    if expected == "":
        is_pass = result == ""
    else:
        is_pass = expected in result
    
    status = "PASS" if is_pass else "FAIL"
    if is_pass:
        passed += 1
    
    print(f"\n{status}: {developer[:45]}...")
    print(f"  Pattern: {description}")
    print(f"  Expected contains: '{expected}'")
    print(f"  Got: '{result}'")

print("\n" + "=" * 70)
print(f"RESULTS: {passed}/{len(tests)} tests passed")
print("=" * 70)
