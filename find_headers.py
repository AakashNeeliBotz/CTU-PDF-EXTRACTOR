import pandas as pd

excel_path = r"c:\Users\Sree Charan\Desktop\fold2\CTU-PDF-EXTRACTOR\Connectivity_Application_Data_TEST_ALL_SHEETS38 (2).xlsx"

def find_headers(sheet_name):
    print(f"--- Finding headers in {sheet_name} ---")
    df = pd.read_excel(excel_path, sheet_name=sheet_name, header=None, nrows=20)
    for i, row in df.iterrows():
        row_list = [str(x).strip() for x in row.tolist()]
        print(f"Row {i}: {row_list}")

if __name__ == "__main__":
    find_headers("Data to be captured")
    find_headers("Element Status")
