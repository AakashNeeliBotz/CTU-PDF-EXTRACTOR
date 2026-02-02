import pandas as pd
import pdfplumber
import re

def extract_regulation_52_data():
    """Extract data specifically from regulation 5.2 tables - direct approach"""
    pdf_path = '175923696873MoM  40th CMETS NR meeting_F.pdf'
    regulation_data = []
    
    print('Extracting regulation 5.2 data directly...')
    
    with pdfplumber.open(pdf_path) as pdf:
        # We know regulation 5.2 is on page 9
        page = pdf.pages[8]  # Page 9 (0-indexed)
        tables = page.extract_tables()
        
        print(f'Found {len(tables)} tables on page 9')
        
        # Process table 3 which has the regulation 5.2 data
        if len(tables) >= 3:
            table = tables[2]  # Third table (0-indexed)
            print('Processing table 3 (regulation 5.2 data)')
            
            # Print table structure to understand it better
            print('\nRaw table data:')
            for i, row in enumerate(table):
                print(f'Row {i}: {row}')
            
            # Now process the data rows (skip the header rows)
            for row_idx in range(3, len(table)):  # Start from row 3 (data rows)
                row = table[row_idx]
                if len(row) >= 11:  # Ensure we have enough columns
                    print(f'\nProcessing raw row {row_idx}: {row}')
                    
                    # Extract data by direct index access
                    application_no_date = str(row[1]) if row[1] is not None else ''
                    applicant = str(row[2]) if row[2] is not None else ''
                    project_location = str(row[3]) if row[3] is not None else ''
                    nature_applicant = str(row[4]) if row[4] is not None else ''
                    app_quantum_conn = str(row[6]) if row[6] is not None else ''
                    planned_capacity = str(row[7]) if row[7] is not None else ''  # This is the planned capacity (column 7, not 8)
                    date_additional = str(row[10]) if row[10] is not None else ''
                    
                    # Clean up the values
                    application_no_date = application_no_date.strip() if application_no_date != 'None' else ''
                    applicant = applicant.strip() if applicant != 'None' else ''
                    project_location = project_location.strip() if project_location != 'None' else ''
                    nature_applicant = nature_applicant.strip() if nature_applicant != 'None' else ''
                    app_quantum_conn = app_quantum_conn.strip() if app_quantum_conn != 'None' else ''
                    planned_capacity = planned_capacity.strip() if planned_capacity != 'None' else ''
                    date_additional = date_additional.strip() if date_additional != 'None' else ''
                    
                    print(f"  Application: '{application_no_date}'")
                    print(f"  Applicant: '{applicant}'")
                    print(f"  Location: '{project_location}'")
                    print(f"  Nature: '{nature_applicant}'")
                    print(f"  Quantum: '{app_quantum_conn}'")
                    print(f"  Planned: '{planned_capacity}'")
                    print(f"  Date: '{date_additional}'")
                    
                    # Parse the planned capacity for solar/wind logic
                    solar_val = 0
                    wind_val = 0
                    
                    if planned_capacity and planned_capacity != 'nan' and planned_capacity.strip():
                        # Handle BESS values - they go to solar field
                        bess_matches = re.findall(r'(\d+)\s*\(BESS\)', planned_capacity)
                        for bess_val in bess_matches:
                            solar_val += int(bess_val)
                        
                        # Handle Solar values
                        solar_matches = re.findall(r'(\d+)\s*\(Solar\)', planned_capacity)
                        for solar_val_only in solar_matches:
                            solar_val += int(solar_val_only)
                        
                        # Handle Wind values
                        wind_matches = re.findall(r'(\d+)\s*\(Wind\)', planned_capacity)
                        for wind_val_only in wind_matches:
                            wind_val += int(wind_val_only)
                    
                    print(f'  Parsed - Solar: {solar_val}, Wind: {wind_val}')
                    
                    regulation_data.append({
                        'application_no_date': application_no_date,
                        'applicant': applicant,
                        'project_location': project_location,
                        'nature_applicant': nature_applicant,
                        'app_quantum_already_granted': app_quantum_conn,
                        'planned_capacity': planned_capacity,
                        'date_additional_capacity': date_additional,
                        'solar_value': solar_val,
                        'wind_value': wind_val
                    })
                else:
                    print(f"Skipping row {row_idx} due to insufficient columns: {row}")
    
    print(f'\nExtracted {len(regulation_data)} entries')
    return regulation_data

def update_excel(regulation_data):
    """Update the Excel file with extracted data"""
    excel_path = 'Connectivity_Application_Data_TEST_ALL_SHEETS38.xlsx'
    
    print(f'Updating Excel file: {excel_path}')
    
    try:
        # Load the Excel file
        xl_file = pd.ExcelFile(excel_path)
        df_data = pd.read_excel(excel_path, sheet_name='Data to be captured', header=None)
        
        print(f'Loaded Excel with {len(df_data)} rows')
        
        # Find the first empty row to add data
        start_row = 0
        for i in range(len(df_data)):
            if pd.isna(df_data.iloc[i, 0]) or df_data.iloc[i, 0] == '':
                start_row = i
                break
        
        if start_row == 0:
            start_row = len(df_data)
        
        print(f'Starting at row {start_row}')
        
        # Add data to Excel
        for i, entry in enumerate(regulation_data):
            row_idx = start_row + i
            
            # Extend DataFrame if needed
            while row_idx >= len(df_data):
                df_data.loc[len(df_data)] = [None] * len(df_data.columns)
            
            # Map to correct columns based on our analysis:
            # Column 6: Name of Developers
            # Column 3: State  
            # Column 35: Nature of Applicant
            # Column 10: Application ID under Enhancement 5.2 or revision
            # Column 16: Application Quantum (MW)(ST II)
            # Column 19: Solar (S column)
            # Column 20: Wind (T column)  
            # Column 34: Date from which additional capacity is to be added
            
            df_data.iloc[row_idx, 6] = entry['applicant']  # Name of Developers
            df_data.iloc[row_idx, 3] = entry['project_location']  # State
            df_data.iloc[row_idx, 35] = entry['nature_applicant']  # Nature of Applicant
            df_data.iloc[row_idx, 10] = entry['application_no_date']  # Application ID Enhancement
            df_data.iloc[row_idx, 16] = entry['app_quantum_already_granted']  # Application Quantum
            df_data.iloc[row_idx, 19] = entry['solar_value']  # Solar column (S)
            df_data.iloc[row_idx, 20] = entry['wind_value']  # Wind column (T)
            df_data.iloc[row_idx, 34] = entry['date_additional_capacity']  # Date additional capacity
            
            print(f'Added: {entry["applicant"]} - {entry["project_location"]} - Solar: {entry["solar_value"]}, Wind: {entry["wind_value"]}')
        
        # Save the updated file
        with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            # Write the updated 'Data to be captured' sheet
            df_data.to_excel(writer, sheet_name='Data to be captured', index=False, header=False)
            
            # Write other sheets to preserve them
            for sheet_name in xl_file.sheet_names:
                if sheet_name != 'Data to be captured':
                    df_sheet = pd.read_excel(xl_file, sheet_name=sheet_name)
                    df_sheet.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print('Excel file updated successfully!')
        
    except Exception as e:
        print(f'Error updating Excel: {e}')
        import traceback
        traceback.print_exc()

def main():
    print("Starting direct PDF extraction...")
    
    # Extract data
    data = extract_regulation_52_data()
    
    if data:
        # Update Excel
        update_excel(data)
        print("Process completed successfully!")
    else:
        print("No data extracted.")

if __name__ == "__main__":
    main()