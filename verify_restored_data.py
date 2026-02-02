import pandas as pd

# Check the restored file
file_path = 'c:/Users/Sree Charan/Desktop/fold2/CTU-PDF-EXTRACTOR/Connectivity_Application_Data_TEST_ALL_SHEETS38.xlsx'

# Load the Data to be captured sheet with proper headers
df = pd.read_excel(file_path, sheet_name='Data to be captured', header=1)

print('Total rows in Data to be captured:', len(df))
print('Last 10 rows of the sheet:')
print(df.tail(10)[['Name of Developers', 'State', 'Application Quantum (MW)(ST II)', 'Solar', 'Wind']].fillna(''))

# Check if our extracted data is there
print('\nOur extracted regulation 5.2 data:')
extracted_data = df.tail(5)
for idx, row in extracted_data.iterrows():
    developer = row['Name of Developers'] if pd.notna(row['Name of Developers']) else 'N/A'
    state = row['State'] if pd.notna(row['State']) else 'N/A'
    solar = row['Solar'] if pd.notna(row['Solar']) else 0
    wind = row['Wind'] if pd.notna(row['Wind']) else 0
    print(f'Row {idx}: Developer={developer}, State={state}, Solar={solar}, Wind={wind}')