import pandas as pd
import pdfplumber
import re

def extract_regulation_52_data():
    """Extract data specifically from regulation 5.2 tables"""
    pdf_path = '175923696873MoM  40th CMETS NR meeting_F.pdf'
    regulation_data = []
    
    print('Extracting regulation 5.2 data...')
    
    with pdfplumber.open(pdf_path) as pdf:
        # We know regulation 5.2 is on page 9
        page = pdf.pages[8]  # Page 9 (0-indexed)
        tables = page.extract_tables()
        
        print(f'Found {len(tables)} tables on page 9')
        
        # Process table 3 which has the regulation 5.2 data
        if len(tables) >= 3:
            table = tables[2]  # Third table (0-indexed)
            print('Processing table 3 (regulation 5.2 data)')
            
            # Print table structure
            for i, row in enumerate(table[:5]):
                print(f'Row {i}: {row}')
            
            # Create DataFrame with proper headers
            # Headers are spread across first 3 rows, so we need to combine them
            headers = []
            for col_idx in range(len(table[0])):
                # Combine the three header rows for each column
                header_parts = []
                for row_idx in range(3):
                    if row_idx < len(table) and col_idx < len(table[row_idx]):
                        cell = table[row_idx][col_idx]
                        if cell and str(cell).strip():
                            header_parts.append(str(cell).strip())
                
                # Join the header parts
                full_header = ' '.join(header_parts)
                headers.append(full_header)
            
            print('Combined headers:')
            for i, header in enumerate(headers):
                print(f'  Column {i}: {header}')
            
            # Create DataFrame with data rows (starting from row 3)
            if len(table) > 3:
                df = pd.DataFrame(table[3:], columns=headers)
                print(f'Created DataFrame with {len(df)} rows')
                
                # Process each row
                for idx, row in df.iterrows():
                    try:
                        # Extract the required fields based on column positions
                        # From our analysis of the headers:
                        application_no_date = str(row.iloc[1]) if len(row) > 1 else ''
                        applicant = str(row.iloc[2]) if len(row) > 2 else ''
                        project_location = str(row.iloc[3]) if len(row) > 3 else ''
                        nature_applicant = str(row.iloc[4]) if len(row) > 4 else ''
                        app_quantum_conn = str(row.iloc[6]) if len(row) > 6 else ''
                        planned_capacity = str(row.iloc[8]) if len(row) > 8 else ''
                        date_additional = str(row.iloc[10]) if len(row) > 10 else ''
                        
                        # Parse the planned capacity for solar/wind logic
                        solar_val = 0
                        wind_val = 0
                        
                        if planned_capacity and planned_capacity != 'None' and planned_capacity != 'nan':
                            # Handle BESS values - they go to solar field
                            if 'BESS' in planned_capacity:
                                bess_matches = re.findall(r'(\d+)\s*\(BESS\)', planned_capacity)
                                for bess_val in bess_matches:
                                    solar_val += int(bess_val)
                            
                            # Handle Solar values
                            if 'Solar' in planned_capacity:
                                solar_matches = re.findall(r'(\d+)\s*\(Solar\)', planned_capacity)
                                for solar_val_only in solar_matches:
                                    solar_val += int(solar_val_only)
                            
                            # Handle Wind values
                            if 'Wind' in planned_capacity:
                                wind_matches = re.findall(r'(\d+)\s*\(Wind\)', planned_capacity)
                                for wind_val_only in wind_matches:
                                    wind_val += int(wind_val_only)
                        
                        print(f'Entry {idx + 1}:')
                        print(f'  Application: {application_no_date}')
                        print(f'  Applicant: {applicant}')
                        print(f'  Location: {project_location}')
                        print(f'  Nature: {nature_applicant}')
                        print(f'  Quantum: {app_quantum_conn}')
                        print(f'  Planned: {planned_capacity}')
                        print(f'  Date: {date_additional}')
                        print(f'  Solar: {solar_val}, Wind: {wind_val}')
                        print()
                        
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
                        
                    except Exception as e:
                        print(f'Error processing row {idx}: {e}')
                        continue
    
    print(f'Extracted {len(regulation_data)} entries')
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
            
            print(f'Added: {entry["applicant"]} - {entry["project_location"]}')
        
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
    print("Starting simple PDF extraction...")
    
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