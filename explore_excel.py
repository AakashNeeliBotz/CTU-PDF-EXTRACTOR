import pandas as pd

file_path = r'c:\Users\Sree Charan\Desktop\fold2\CTU-PDF-EXTRACTOR\Connectivity_Application_Data_TEST_ALL_SHEETS38 (2).xlsx'
sheet_name = 'Data to be captured'

df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)

for idx, row in df.iterrows():
    row_values = [str(x) for x in row.values]
    row_text = ' '.join(row_values)
    if any(keyword in row_text for keyword in ['CMETS', 'GNA', 'LTA', 'Application ID']):
        print(f"Row {idx}: {row_values}")
    if idx > 20: # Limit output
        break
