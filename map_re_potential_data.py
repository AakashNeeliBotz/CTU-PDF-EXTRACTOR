"""
Parse and map RE Potential data from SN10a PDF to RE Potential sheet format
"""
import camelot
import pandas as pd
import openpyxl
import re
import os

pdf_path = r'downloaded_pdfs\SN10a\CEA_Tx_Plan_for_500GW_Non_fossil_capacity_by_2030.pdf'
excel_path = 'Connectivity Application Data.xlsx'

print("="*80)
print("RE POTENTIAL DATA MAPPING - SN10a PDF")
print("="*80)

# Extract all tables from PDF
print("\nStep 1: Extracting tables from PDF...")
all_tables = camelot.read_pdf(pdf_path, pages='all', flavor='lattice', suppress_stdout=True)
print(f"✓ Extracted {len(all_tables)} tables")

# Data storage
re_potential_records = []

# Helper function to clean text
def clean_text(text):
    if pd.isna(text):
        return ''
    return str(text).strip().replace('\n', ' ').replace('\t', ' ')

# Helper function to extract numeric value
def extract_number(text):
    if pd.isna(text):
        return None
    text = str(text).strip()
    # Extract first number found
    match = re.search(r'(\d+\.?\d*)', text)
    if match:
        return float(match.group(1))
    return None

# Helper function to check if row contains pooling station data
def is_pooling_station_row(row_data):
    row_text = ' '.join([str(x).lower() for x in row_data])
    # Check for pooling station patterns
    ps_patterns = ['pooling', 'ps', 'substation', 's/s']
    has_ps = any(p in row_text for p in ps_patterns)
    has_capacity = any(char.isdigit() for char in row_text)
    return has_ps and has_capacity

# Process each table
print("\nStep 2: Processing tables and extracting data...")

current_state = None
current_region = None
current_district = None
transmission_scheme_text = None

for table_idx, table in enumerate(all_tables):
    df = table.df
    page = table.page
    
    # Skip very small tables
    if df.shape[0] < 2 or df.shape[1] < 2:
        continue
    
    # Get table text for pattern matching
    table_text_lower = ' '.join(df.astype(str).values.flatten()[:30]).lower()
    
    # Check table type
    is_summary_table = 'state' in table_text_lower and ('wind' in table_text_lower or 'solar' in table_text_lower)
    is_pooling_table = 'pooling' in table_text_lower and 'station' in table_text_lower
    is_zone_table = 'zone' in table_text_lower or 'district' in table_text_lower
    is_transmission_table = 'transmission' in table_text_lower and 'scheme' in table_text_lower
    
    # Pattern 1: State summary tables (like page 13-14)
    # Columns: Sl. No. | State | Wind (GW) | Solar (GW) | Total (GW) | Remarks
    if is_summary_table and df.shape[1] >= 4:
        for row_idx in range(len(df)):
            row = df.iloc[row_idx]
            row_text = clean_text(' '.join([str(x) for x in row]))
            
            # Check if this is a data row with state name
            states = ['rajasthan', 'andhra pradesh', 'karnataka', 'tamil nadu', 'telangana', 
                     'madhya pradesh', 'gujarat', 'maharashtra', 'chhattisgarh']
            
            if any(state in row_text.lower() for state in states):
                # Extract state name
                for state in states:
                    if state in row_text.lower():
                        current_state = state.title()
                        break
                
                # Try to extract Wind and Solar values
                wind_val = None
                solar_val = None
                total_val = None
                remarks = None
                
                # Look for numeric values in the row
                for i, cell in enumerate(row):
                    cell_text = clean_text(str(cell))
                    num = extract_number(cell_text)
                    
                    if num is not None:
                        # First number is likely Wind
                        if wind_val is None:
                            wind_val = num
                        # Second number is likely Solar
                        elif solar_val is None:
                            solar_val = num
                        # Third number is likely Total
                        elif total_val is None:
                            total_val = num
                
                # Last column might be remarks
                if len(row) > 4:
                    remarks = clean_text(row.iloc[-1])
                
                record = {
                    'page': page,
                    'source_table': table_idx,
                    'region': current_region,
                    'state': current_state,
                    'district': None,
                    'complex': None,
                    's_s': None,
                    'location_village_tehsil': None,
                    'solar': solar_val,
                    'wind': wind_val,
                    'hybrid': None,
                    'others_ctuil': None,
                    're_potential_gw': total_val,
                    'installed_capacity': None,
                    'uc_granted_capacity': None,
                    'transmission_scheme': None,
                    'complex_2': None,
                    'remarks': remarks if remarks and len(remarks) > 2 else None
                }
                re_potential_records.append(record)
    
    # Pattern 2: District/Zone tables with location details
    # Look for tables with district names and capacity values
    elif is_zone_table and df.shape[1] >= 2:
        for row_idx in range(len(df)):
            row = df.iloc[row_idx]
            row_text = clean_text(' '.join([str(x) for x in row]))
            
            # Common district/location names from the PDF
            locations = ['kurnool', 'anantapur', 'sanchor', 'sirohi', 'jalor', 'pali', 'ajmer', 
                        'bikaner', 'nagaur', 'nizamabad', 'medak', 'koppal', 'gadag']
            
            if any(loc in row_text.lower() for loc in locations):
                # Extract location/district name
                district_name = None
                for loc in locations:
                    if loc in row_text.lower():
                        district_name = loc.title()
                        break
                
                # Extract capacity values
                solar_val = None
                wind_val = None
                total_val = None
                
                for cell in row:
                    num = extract_number(cell)
                    if num is not None:
                        if solar_val is None:
                            solar_val = num
                        elif wind_val is None:
                            wind_val = num
                        elif total_val is None:
                            total_val = num
                
                record = {
                    'page': page,
                    'source_table': table_idx,
                    'region': current_region,
                    'state': current_state,
                    'district': district_name,
                    'complex': None,
                    's_s': None,
                    'location_village_tehsil': district_name,
                    'solar': solar_val,
                    'wind': wind_val,
                    'hybrid': None,
                    'others_ctuil': None,
                    're_potential_gw': total_val,
                    'installed_capacity': None,
                    'uc_granted_capacity': None,
                    'transmission_scheme': None,
                    'complex_2': None,
                    'remarks': None
                }
                re_potential_records.append(record)
    
    # Pattern 3: Pooling Station tables
    # Columns: Pooling Station | Wind (GW) | Solar (GW) | Total (GW) | BESS (GW) | ...
    elif is_pooling_table and df.shape[1] >= 4:
        for row_idx in range(len(df)):
            row = df.iloc[row_idx]
            first_col = clean_text(row.iloc[0]).lower()
            
            # Skip header rows
            if 'pooling' in first_col or 'station' in first_col:
                continue
            if 'wind' in first_col or 'solar' in first_col or 'gw' in first_col:
                continue
            
            # Check if this looks like a pooling station name
            ps_keywords = ['-ii', '-iii', '-iv', '-v', 'ps', 'substation']
            if any(kw in first_col for kw in ps_keywords) or (len(first_col) > 3 and first_col[0].isalpha()):
                pooling_station = clean_text(row.iloc[0])
                
                # Extract numeric values
                values = []
                for i in range(1, min(len(row), 10)):
                    num = extract_number(row.iloc[i])
                    if num is not None:
                        values.append(num)
                
                # Typical pattern: Wind, Solar, Total, BESS
                wind_val = values[0] if len(values) > 0 else None
                solar_val = values[1] if len(values) > 1 else None
                total_val = values[2] if len(values) > 2 else None
                bess_val = values[3] if len(values) > 3 else None
                
                record = {
                    'page': page,
                    'source_table': table_idx,
                    'region': current_region,
                    'state': current_state,
                    'district': None,
                    'complex': pooling_station,
                    's_s': pooling_station,
                    'location_village_tehsil': None,
                    'solar': solar_val,
                    'wind': wind_val,
                    'hybrid': None,
                    'others_ctuil': bess_val,  # BESS can go to Others
                    're_potential_gw': total_val,
                    'installed_capacity': None,
                    'uc_granted_capacity': None,
                    'transmission_scheme': None,
                    'complex_2': None,
                    'remarks': None
                }
                re_potential_records.append(record)
    
    # Update region context based on headings
    for row_idx in range(min(3, len(df))):
        row_text = clean_text(' '.join([str(x) for x in df.iloc[row_idx]])).lower()
        if 'northern region' in row_text:
            current_region = 'Northern'
        elif 'western region' in row_text:
            current_region = 'Western'
        elif 'southern region' in row_text:
            current_region = 'Southern'
        elif 'eastern region' in row_text:
            current_region = 'Eastern'

print(f"✓ Extracted {len(re_potential_records)} records from tables")

# Create DataFrame
df_output = pd.DataFrame(re_potential_records)

# Clean up and deduplicate
print("\nStep 3: Cleaning and deduplicating data...")
# Remove records with no meaningful data
df_output = df_output[
    (df_output['state'].notna()) | 
    (df_output['district'].notna()) | 
    (df_output['complex'].notna())
]

# Remove duplicate records based on key fields
key_fields = ['state', 'district', 'complex', 's_s', 'solar', 'wind', 're_potential_gw']
df_output = df_output.drop_duplicates(subset=key_fields, keep='first')

print(f"✓ {len(df_output)} unique records after cleaning")

# Save to CSV
output_csv = 'extraction_output/RE_Potential_SN10a_mapped.csv'
os.makedirs('extraction_output', exist_ok=True)
df_output.to_csv(output_csv, index=False)
print(f"\n✓ Mapped data saved to: {output_csv}")

# Show summary
print("\n" + "="*80)
print("DATA SUMMARY")
print("="*80)
print(f"Total records: {len(df_output)}")
print(f"States covered: {df_output['state'].nunique()}")
print(f"States: {sorted(df_output['state'].dropna().unique())}")
print(f"\nRecords by state:")
print(df_output.groupby('state').size())

print(f"\nTotal capacity:")
print(f"  Solar: {df_output['solar'].sum():.1f} GW")
print(f"  Wind: {df_output['wind'].sum():.1f} GW")
print(f"  Total RE: {df_output['re_potential_gw'].sum():.1f} GW")

# Show sample records
print("\n" + "="*80)
print("SAMPLE RECORDS")
print("="*80)
for i in range(min(10, len(df_output))):
    rec = df_output.iloc[i]
    print(f"\n[{i+1}] Page {rec['page']}")
    print(f"  State: {rec['state']}, District: {rec['district']}, Complex: {rec['complex']}")
    print(f"  Solar: {rec['solar']} GW, Wind: {rec['wind']} GW, Total: {rec['re_potential_gw']} GW")
    if rec['remarks']:
        print(f"  Remarks: {rec['remarks']}")

print("\n" + "="*80)
print("EXTRACTION COMPLETE")
print("="*80)
print("\nNext step: Review the mapped data and populate RE Potential sheet in Excel")
