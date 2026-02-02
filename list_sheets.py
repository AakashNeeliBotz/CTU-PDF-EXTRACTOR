import pandas as pd

excel_path = r"c:\Users\Sree Charan\Desktop\fold2\CTU-PDF-EXTRACTOR\Connectivity_Application_Data_TEST_ALL_SHEETS38 (2).xlsx"

def list_sheets():
    xl = pd.ExcelFile(excel_path)
    print("Sheet names:", xl.sheet_names)

if __name__ == "__main__":
    list_sheets()
