#!/usr/bin/env python3
"""
Verification script to check if the enhanced parsing functions are working correctly
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_main_skip_download import enhanced_parse_hybrid_capacity_breakup, parse_battery_values, parse_psp_capacity

def test_enhanced_functions():
    print("Testing enhanced parsing functions...")
    
    # Test cases for hybrid parsing
    test_cases_hybrid = [
        {
            "quantum": "360 (Solar-260, Wind-100)",
            "nature": "Generator (Solar & Wind)",
            "expected": {"solar_mw": "260", "wind_mw": "100", "hybrid_mw": "360"}
        },
        {
            "quantum": "180 (Solar-130 Wind-50)",
            "nature": "Hybrid Renewable",
            "expected": {"solar_mw": "130", "wind_mw": "50", "hybrid_mw": "180"}
        },
        {
            "quantum": "989 (Solar-675MW, Wind:314MW)",
            "nature": "RHGS Project",
            "expected": {"solar_mw": "675", "wind_mw": "314", "hybrid_mw": "989"}
        },
        {
            "quantum": "Connectivity:327 (Solar:200, Wind:127)",
            "nature": "Hybrid",
            "expected": {"solar_mw": "200", "wind_mw": "127", "hybrid_mw": "327"}
        }
    ]
    
    print("\nTesting Enhanced Hybrid Parsing:")
    for i, test_case in enumerate(test_cases_hybrid, 1):
        result = enhanced_parse_hybrid_capacity_breakup(test_case["quantum"], test_case["nature"])
        print(f"Test {i}: '{test_case['quantum']}' | '{test_case['nature']}'")
        print(f"  Expected: {test_case['expected']}")
        print(f"  Got:      {result}")
        success = all(result[k] == v for k, v in test_case['expected'].items() if v is not None)
        print(f"  Status: {'✓ PASS' if success else '✗ FAIL'}")
        print()
    
    # Test cases for battery parsing
    test_cases_battery = [
        {
            "quantum": "Connectivity:200 (Solar:200 ESS: 46)",
            "nature": "Generator (Solar) with ESS",
            "expected": {"battery_mwh": "46", "battery_injection_mw": None, "battery_drawl_mw": None}
        },
        {
            "quantum": "BESS:380 MWh)",
            "nature": "Standalone ESS",
            "expected": {"battery_mwh": "380", "battery_injection_mw": None, "battery_drawl_mw": None}
        },
        {
            "quantum": "BESS-100MWh",
            "nature": "Storage Project",
            "expected": {"battery_mwh": "100", "battery_injection_mw": None, "battery_drawl_mw": None}
        }
    ]
    
    print("Testing Battery Parsing:")
    for i, test_case in enumerate(test_cases_battery, 1):
        result = parse_battery_values(test_case["quantum"], test_case["nature"])
        print(f"Test {i}: '{test_case['quantum']}' | '{test_case['nature']}'")
        print(f"  Expected: {test_case['expected']}")
        print(f"  Got:      {result}")
        success = all(result.get(k) == v for k, v in test_case['expected'].items() if v is not None)
        # For None values, check that they're either None or not in result
        none_check = all(result.get(k) is None for k, v in test_case['expected'].items() if v is None)
        success = success and none_check
        print(f"  Status: {'✓ PASS' if (success and all(result.get(k) == v for k, v in test_case['expected'].items() if v is not None)) else '✗ FAIL'}")
        print()
    
    # Test cases for PSP parsing
    test_cases_psp = [
        {
            "quantum": "Connectivity:880 Max Injection: 800 Max Drawl:880",
            "nature": "Standalone ESS (Pumped Storage)",
            "expected": {"psp_mwh": None, "psp_injection_mw": "800", "psp_drawl_mw": "880"}
        }
    ]
    
    print("Testing PSP Parsing:")
    for i, test_case in enumerate(test_cases_psp, 1):
        result = parse_psp_capacity(test_case["quantum"], test_case["nature"])
        print(f"Test {i}: '{test_case['quantum']}' | '{test_case['nature']}'")
        print(f"  Expected: {test_case['expected']}")
        print(f"  Got:      {result}")
        # Note: psp_mwh is intentionally None per requirements
        success = (result['psp_injection_mw'] == test_case['expected']['psp_injection_mw'] and 
                   result['psp_drawl_mw'] == test_case['expected']['psp_drawl_mw'])
        print(f"  Status: {'✓ PASS' if success else '✗ FAIL'}")
        print()

if __name__ == "__main__":
    test_enhanced_functions()