import pandas as pd

df = pd.read_csv('extraction_output/Transformation_Capacity_extracted_data.csv')

print("="*80)
print(f"FINAL VERIFICATION - {len(df)} total rows")
print("="*80)

# Row 1: Jam Khambhaliya
row1 = df[df['s_no'] == 1].iloc[0]
print(f"\nRow 1 (Jam Khambhaliya PS):")
print(f"  {row1['voltage_level_kv']} kV | Existing: {row1['existing_mva']}")
if row1['voltage_level_kv'] == 220 and row1['existing_mva'] == 2000:
    print("  ✅ CORRECT!")
else:
    print("  ❌ INCORRECT")

# Row 29: Bikaner
bikaner = df[df['s_no'] == 29]
print(f"\nRow 29 (Bikaner S/s) - {len(bikaner)} rows:")
for _, row in bikaner.iterrows():
    print(f"  {row['voltage_level_kv']} kV | E:{row['existing_mva']} UI:{row['under_implementation_mva']} P:{row['planned_mva']}")

if len(bikaner) == 2:
    r400 = bikaner[bikaner['voltage_level_kv']==400].iloc[0]
    r220 = bikaner[bikaner['voltage_level_kv']==220].iloc[0]
    if (r400['existing_mva']==1500 and r400['under_implementation_mva']==3000 and r400['planned_mva']==1500 and
        pd.isna(r220['existing_mva']) and r220['under_implementation_mva']==1000 and r220['planned_mva']==500):
        print("  ✅ CORRECT!")
    else:
        print("  ❌ INCORRECT")
else:
    print("  ❌ Should be 2 rows")

print("\n" + "="*80)
