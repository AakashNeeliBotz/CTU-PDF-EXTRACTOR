import pandas as pd

# Load the CSV
df = pd.read_csv('extraction_output/Data_to_be_captured_extracted_data.csv')

print("Total rows in CSV:", len(df))
print("Total columns in CSV:", len(df.columns))
print("\nAll column names:")
for i, col in enumerate(df.columns):
    print(f"{i+1}. '{col}'")

print("\n\nFirst record (row 0) - showing non-NaN values only:")
row0 = df.iloc[0]
for col, val in row0.items():
    if pd.notna(val):
        print(f"  {col}: {val}")

print("\n\nSecond record (row 1) - showing non-NaN values only:")
row1 = df.iloc[1]
for col, val in row1.items():
    if pd.notna(val):
        print(f"  {col}: {val}")
