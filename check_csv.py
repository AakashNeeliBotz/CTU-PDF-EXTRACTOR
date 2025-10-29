import pandas as pd

df = pd.read_csv('extraction_output/Data_to_be_captured_extracted_data.csv')
print('CSV shape:', df.shape)
print('\nCSV columns (first 15):', list(df.columns)[:15])
print('\nSample record 1:')
for k, v in list(df.iloc[0].items())[:10]:
    print(f'  {k}: {v}')

print('\n\nChecking for duplicate rows after dropping NaN:')
print('Total rows:', len(df))
df_no_na = df.dropna(how='all', axis=1)
print('Rows after dropping all-NA columns:', len(df_no_na))
print('Columns after dropping all-NA columns:', df_no_na.shape[1])
