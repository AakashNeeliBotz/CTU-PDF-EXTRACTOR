import openpyxl

wb = openpyxl.load_workbook('Connectivity Application Data.xlsx')
es = wb['Element Status']

# Write to file to avoid truncation
with open('element_sheet_structure.txt', 'w') as f:
    f.write("Element Status sheet structure:\n")
    f.write("="*60 + "\n\n")
    
    # Check first 15 rows, 20 columns
    for row_idx in range(1, 15):
        f.write(f"\nRow {row_idx}:\n")
        for col_idx in range(1, 20):
            val = es.cell(row=row_idx, column=col_idx).value
            if val:
                f.write(f"  Col {col_idx}: {val}\n")

wb.close()
print("Output written to element_sheet_structure.txt")
