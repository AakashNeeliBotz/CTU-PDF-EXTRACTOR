import pandas as pd

file_path = r'Connectivity_Application_Data_TEST_ALL_SHEETS38 (2).xlsx'
sheet_name = 'Data to be captured'

df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)

for i, row in df.head(10).iterrows():
    row_list = [str(x) for x in row.tolist()]
    if any('CMETS' in val for val in row_list):
        print(f"Row {i}: {row_list}")
    if any('Application ID' in val for val in row_list):
        print(f"Row {i} (App ID): {row_list}")

# Also print columns 0 to 50 for the first 5 rows to see the structure
print("\nFirst 5 rows, first 30 columns:")
print(df.iloc[:5, :30].to_string())
