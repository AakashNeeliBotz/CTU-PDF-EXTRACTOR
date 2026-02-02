import pandas as pd

excel_path = r"c:\Users\Sree Charan\Desktop\fold2\CTU-PDF-EXTRACTOR\Connectivity_Application_Data_TEST_ALL_SHEETS38 (2).xlsx"

def inspect_excel():
    print("--- Inspecting 'Data to be captured' ---")
    df_head = pd.read_excel(excel_path, sheet_name="Data to be captured", header=None, nrows=10)
    print(df_head)
    
    print("\n--- Inspecting 'Element status' ---")
    df_status = pd.read_excel(excel_path, sheet_name="Element Status")
    print("Columns:", df_status.columns.tolist())
    print(df_status.head())

if __name__ == "__main__":
    inspect_excel()
