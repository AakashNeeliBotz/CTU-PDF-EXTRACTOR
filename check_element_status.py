
import pandas as pd

excel_path = r"c:\Users\Sree Charan\Desktop\fold2\CTU-PDF-EXTRACTOR\Connectivity_Application_Data_TEST_ALL_SHEETS38 (2).xlsx"
sheet_name_element = "Element Status"

df_element = pd.read_excel(excel_path, sheet_name=sheet_name_element, header=1)
print(df_element[['Element Code', 'Transmission Scheme', 'Transmission Scope']].head(10))
