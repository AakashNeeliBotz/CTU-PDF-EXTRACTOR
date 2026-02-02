import openpyxl

def inspect_columns():
    wb = openpyxl.load_workbook('Connectivity_Application_Data_TEST_ALL_SHEETS38 (2).xlsx', data_only=True)
    sheet = wb['Data to be captured']
    
    # Headers usually span 1-3 rows. Let's look at them.
    for r in range(1, 4):
        headers = [str(cell.value).strip() if cell.value is not None else "" for cell in sheet[r]]
        print(f"Row {r} Headers:")
        for idx, h in enumerate(headers):
            if h:
                print(f"  Col {idx+1}: {h}")

inspect_columns()
