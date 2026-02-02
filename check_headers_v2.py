import pandas as pd

file_path = r'Connectivity_Application_Data_TEST_ALL_SHEETS38 (2).xlsx'
sheet_name = 'Data to be captured'

df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)

target_cols = [
    "CMETS GNA Approved", 
    "CMETS LTA Approved", 
    "CMETS GNA Meeting Date", 
    "CMETS LTA Meeting Date"
]

found_headers = {}

for i, row in df.iterrows():
    row_list = [str(x).strip() for x in row.tolist()]
    for col_name in target_cols:
        if col_name in row_list:
            idx = row_list.index(col_name)
            found_headers[col_name] = (i, idx)
    
    # Also look for where Application IDs are stored
    if "GNA/ST II Application ID" in row_list:
        found_headers["GNA/ST II Application ID"] = (i, row_list.index("GNA/ST II Application ID"))
    if "LTA Application ID" in row_list:
        found_headers["LTA Application ID"] = (i, row_list.index("LTA Application ID"))

print(f"Found headers: {found_headers}")

# If we didn't find them exactly, search for partial matches
if len(found_headers) < len(target_cols):
    print("\nPartial matches:")
    for i, row in df.head(20).iterrows():
        row_list = [str(x).strip() for x in row.tolist()]
        for col_name in target_cols:
            for idx, val in enumerate(row_list):
                if col_name.lower() in val.lower():
                    print(f"Found partial '{col_name}' at Row {i}, Col {idx}: '{val}'")

# Check for GNA/LTA App ID columns
for i, row in df.head(10).iterrows():
    row_list = [str(x).strip() for x in row.tolist()]
    for idx, val in enumerate(row_list):
        if "Application ID" in val:
            print(f"Found potential App ID col at Row {i}, Col {idx}: '{val}'")
