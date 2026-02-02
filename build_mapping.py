import openpyxl

def build_element_mapping():
    wb = openpyxl.load_workbook('Connectivity_Application_Data_TEST_ALL_SHEETS38 (2).xlsx', data_only=True)
    sheet = wb['Element Status']
    
    mapping = {}
    # Row 1-3 are headers. Data starts from Row 4.
    for row in sheet.iter_rows(min_row=4):
        code = str(row[1].value).strip() if row[1].value else None
        # The description could be in Transmission Scheme (Col 4) or Transmission Scope (Col 5)
        scheme = str(row[3].value).strip() if row[3].value else ""
        scope = str(row[4].value).strip() if row[4].value else ""
        
        if code:
            if scheme:
                mapping[scheme.lower()] = code
            if scope:
                mapping[scope.lower()] = code
                
    # Also handle multiple lines or slightly different formatting if needed
    # For now, let's just print a few to see
    print(f"Total mapping items: {len(mapping)}")
    # Sample 10 items
    for k, v in list(mapping.items())[:10]:
        print(f"'{k}' -> '{v}'")

build_element_mapping()
