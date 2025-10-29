from pdf_processor import extract_tables_with_camelot, convert_tables_to_records

tables = extract_tables_with_camelot('downloaded_pdfs/SN3/175747952599June 25_RE.pdf')
print(f'\nTables extracted: {len(tables)}\n')

if tables:
    print(f'Converting tables to records...\n')
    records = convert_tables_to_records(tables)
    
    print(f'\n=== RESULTS ===')
    print(f'Total records: {len(records)}')
    
    if records:
        print(f'\nFirst record keys: {list(records[0].keys())}')
        print(f'\nFirst record:')
        for key, value in records[0].items():
            print(f'  {key}: {value}')
