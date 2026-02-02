import pandas as pd
import pdfplumber
import re
import numpy as np

def extract_regulation_data():
    """Extract data from regulation 5.2 tables in the PDF"""
    pdf_path = '175923696873MoM  40th CMETS NR meeting_F.pdf'
    regulation_data = []
    
    print('Extracting data from PDF tables...')
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if 'regulation 5.2' in text.lower():
                print(f'Found regulation 5.2 on page {page_num + 1}')
                
                # Extract all tables from this page
                tables = page.extract_tables()
                
                # Process the tables to find the one with regulation 5.2 data
                for i, table in enumerate(tables):
                    if table and len(table) > 2:
                        # Print table structure for debugging
                        print(f'\nExamining table {i + 1} on page {page_num + 1}')
                        for r_idx, row in enumerate(table[:3]):  # Print first 3 rows
                            print(f'  Row {r_idx}: {row}')
                        
                        # Check if this table has the regulation 5.2 structure
                        # Look for tables that have the right column headers
                        if table and len(table) > 0:
                            # Check if the table has the right structure by looking for key column headers
                            first_row = table[0]
                            second_row = table[1] if len(table) > 1 else []
                            
                            # Combine first and second row to get complete headers
                            complete_headers = []
                            for idx in range(max(len(first_row), len(second_row))):
                                header1 = first_row[idx] if idx < len(first_row) else ''
                                header2 = second_row[idx] if idx < len(second_row) else ''
                                if header1 and header2:
                                    complete_headers.append(str(header1) + ' ' + str(header2))
                                elif header1:
                                    complete_headers.append(str(header1))
                                elif header2:
                                    complete_headers.append(str(header2))
                                else:
                                    complete_headers.append('')
                            
                            print(f'  Combined headers: {complete_headers}')
                            
                            # Check if this table has the key columns for regulation 5.2
                            has_applicant = any('Applicant' in str(h) for h in complete_headers)
                            has_application = any('Application' in str(h) and ('No.' in str(h) or 'Date' in str(h)) for h in complete_headers)
                            has_project_loc = any('Project' in str(h) and 'Location' in str(h) for h in complete_headers)
                            has_planned_cap = any('Planned' in str(h) and 'capacity' in str(h) for h in complete_headers)
                            
                            if has_applicant and has_application and has_project_loc and has_planned_cap:
                                print(f'\nProcessing regulation 5.2 table {i + 1} on page {page_num + 1}')
                                print('Headers:', complete_headers)
                                
                                # Create DataFrame starting from the actual data rows
                                if len(table) > 2:
                                    # Use the combined headers as column names and data from row 2 onwards
                                    df = pd.DataFrame(table[2:], columns=complete_headers)
                                else:
                                    df = pd.DataFrame(table[1:], columns=complete_headers)
                                
                                # Find the column indices based on headers
                                def find_column_index(headers_list, keywords):
                                    for i, header in enumerate(headers_list):
                                        header_str = str(header).lower()
                                        if all(keyword.lower() in header_str for keyword in keywords):
                                            return i
                                    return -1
                                
                                # Find column positions
                                applicant_col = find_column_index(complete_headers, ['Applicant'])
                                application_col = find_column_index(complete_headers, ['Application', 'No.'])
                                project_loc_col = find_column_index(complete_headers, ['Project', 'Location'])
                                nature_applicant_col = find_column_index(complete_headers, ['Nature', 'Applicant'])
                                conn_quantum_col = find_column_index(complete_headers, ['Conn.', 'Quantum'])
                                planned_cap_col = find_column_index(complete_headers, ['Planned', 'capacity'])
                                date_add_cap_col = find_column_index(complete_headers, ['Date', 'additional', 'capacity'])
                                
                                print(f'  Column mappings: applicant={applicant_col}, application={application_col}, project_loc={project_loc_col}, nature={nature_applicant_col}, conn_quantum={conn_quantum_col}, planned_cap={planned_cap_col}, date_add_cap={date_add_cap_col}')
                                
                                # Process each data row
                                for idx, row in df.iterrows():
                                    # Extract data according to your requirements
                                    try:
                                        # Get the application number and date
                                        application_no_date = str(row.iloc[application_col]) if application_col != -1 and pd.notna(row.iloc[application_col]) else ''
                                        
                                        # Get applicant name
                                        applicant = str(row.iloc[applicant_col]) if applicant_col != -1 and pd.notna(row.iloc[applicant_col]) else ''
                                        
                                        # Get project location (state)
                                        project_location = str(row.iloc[project_loc_col]) if project_loc_col != -1 and pd.notna(row.iloc[project_loc_col]) else ''
                                        
                                        # Get nature of applicant
                                        nature_applicant = str(row.iloc[nature_applicant_col]) if nature_applicant_col != -1 and pd.notna(row.iloc[nature_applicant_col]) else ''
                                        
                                        # Get already granted connectivity quantum
                                        app_quantum_conn_already = str(row.iloc[conn_quantum_col]) if conn_quantum_col != -1 and pd.notna(row.iloc[conn_quantum_col]) else ''
                                        
                                        # Get planned additional capacity
                                        planned_capacity = str(row.iloc[planned_cap_col]) if planned_cap_col != -1 and pd.notna(row.iloc[planned_cap_col]) else ''
                                        
                                        # Get date for additional capacity
                                        date_additional = str(row.iloc[date_add_cap_col]) if date_add_cap_col != -1 and pd.notna(row.iloc[date_add_cap_col]) else ''
                                        
                                        # Parse the planned capacity for solar/wind logic
                                        solar_val = 0
                                        wind_val = 0
                                        
                                        if planned_capacity and planned_capacity != 'None' and planned_capacity != 'nan':
                                            # Handle BESS values - they go to solar field
                                            if 'BESS' in planned_capacity:
                                                # Pattern like "300 (BESS)" or "BESS 300"
                                                bess_match = re.search(r'(\d+)\s*\(BESS\)|BESS\s*(\d+)', planned_capacity)
                                                if bess_match:
                                                    solar_val = int(bess_match.group(1) or bess_match.group(2))
                                            
                                            # Handle Solar values
                                            if 'Solar' in planned_capacity:
                                                solar_match = re.search(r'(\d+)\s*\(Solar\)|Solar\s*(\d+)', planned_capacity)
                                                if solar_match:
                                                    solar_val = int(solar_match.group(1) or solar_match.group(2))
                                            
                                            # Handle Wind values
                                            if 'Wind' in planned_capacity:
                                                wind_match = re.search(r'(\d+)\s*\(Wind\)|Wind\s*(\d+)', planned_capacity)
                                                if wind_match:
                                                    wind_val = int(wind_match.group(1) or wind_match.group(2))
                                            
                                            # Special case: if both BESS and Solar are present, sum them for solar field
                                            if 'BESS' in planned_capacity and 'Solar' in planned_capacity:
                                                # Extract both values and sum them
                                                bess_matches = re.findall(r'(\d+)\s*\(BESS\)', planned_capacity)
                                                solar_matches = re.findall(r'(\d+)\s*\(Solar\)', planned_capacity)
                                                solar_val = 0
                                                for bess_val in bess_matches:
                                                    solar_val += int(bess_val)
                                                for solar_val_only in solar_matches:
                                                    solar_val += int(solar_val_only)
                                        
                                        print(f'Row {idx}:')
                                        print(f'  Application: {application_no_date}')
                                        print(f'  Applicant: {applicant}')
                                        print(f'  Location: {project_location}')
                                        print(f'  Nature: {nature_applicant}')
                                        print(f'  Already granted: {app_quantum_conn_already}')
                                        print(f'  Planned capacity: {planned_capacity}')
                                        print(f'  Date additional: {date_additional}')
                                        print(f'  Parsed - Solar: {solar_val}, Wind: {wind_val}')
                                        print()
                                        
                                        regulation_data.append({
                                            'application_no_date': application_no_date,
                                            'applicant': applicant,
                                            'project_location': project_location,
                                            'nature_applicant': nature_applicant,
                                            'app_quantum_already_granted': app_quantum_conn_already,
                                            'planned_capacity': planned_capacity,
                                            'date_additional_capacity': date_additional,
                                            'solar_value': solar_val,
                                            'wind_value': wind_val
                                        })
                                    
                                    except Exception as e:
                                        print(f'Error processing row {idx}: {e}')
                                        continue
    
    print(f'\nExtracted {len(regulation_data)} entries from regulation 5.2 tables')
    return regulation_data

def update_excel_file(regulation_data):
    """Update the Excel file with the extracted data"""
    excel_path = 'Connectivity_Application_Data_TEST_ALL_SHEETS38.xlsx'
    
    print(f'\nLoading Excel file: {excel_path}')
    
    # Load the Excel file
    try:
        # Load all sheets to preserve them
        xl_file = pd.ExcelFile(excel_path)
        sheet_names = xl_file.sheet_names
        
        # Load the 'Data to be captured' sheet
        df_data = pd.read_excel(excel_path, sheet_name='Data to be captured')
        print(f'Loaded "Data to be captured" sheet with {len(df_data)} rows')
        
        # Find the next empty row to add new data
        # Look for the first row where the first column is empty
        start_row = 0
        for i in range(len(df_data)):
            if pd.isna(df_data.iloc[i, 0]) or df_data.iloc[i, 0] == '':
                start_row = i
                break
        
        if start_row == 0:
            start_row = len(df_data)  # Add to end if no empty rows found
        
        print(f'Starting to add data at row {start_row}')
        
        # Add the regulation data to the Excel sheet
        for i, entry in enumerate(regulation_data):
            row_idx = start_row + i
            
            # Extend the dataframe if needed
            if row_idx >= len(df_data):
                # Add empty rows
                empty_rows_needed = row_idx - len(df_data) + 1
                for _ in range(empty_rows_needed):
                    df_data.loc[len(df_data)] = [None] * len(df_data.columns)
            
            # Map the data to the correct columns based on the Excel structure
            # From our analysis, the columns are:
            # Column 6: Name of Developers
            # Column 3: State  
            # Column 35: Nature of Applicant
            # Column 10: Application ID under Enhancement 5.2 or revision
            # Column 16: Application Quantum (MW)(ST II)
            # Column 19: Solar (S column)
            # Column 20: Wind (T column)  
            # Column 34: Date from which additional capacity is to be added
            
            # Update the specific columns
            df_data.iloc[row_idx, 6] = entry['applicant']  # Name of Developers
            df_data.iloc[row_idx, 3] = entry['project_location']  # State
            df_data.iloc[row_idx, 35] = entry['nature_applicant']  # Nature of Applicant
            df_data.iloc[row_idx, 10] = entry['application_no_date']  # Application ID Enhancement
            df_data.iloc[row_idx, 16] = entry['app_quantum_already_granted']  # Application Quantum
            df_data.iloc[row_idx, 19] = entry['solar_value']  # Solar column (S)
            df_data.iloc[row_idx, 20] = entry['wind_value']  # Wind column (T)
            df_data.iloc[row_idx, 34] = entry['date_additional_capacity']  # Date additional capacity
            
            print(f'Added entry {i+1}: {entry["applicant"]} - {entry["project_location"]}')
        
        # Save the updated Excel file
        print(f'\nSaving updated Excel file...')
        
        # Create a new Excel writer
        with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            # Write the updated 'Data to be captured' sheet
            df_data.to_excel(writer, sheet_name='Data to be captured', index=False)
            
            # Write other sheets to preserve them
            for sheet_name in sheet_names:
                if sheet_name != 'Data to be captured':
                    df_sheet = pd.read_excel(xl_file, sheet_name=sheet_name)
                    df_sheet.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print('Excel file updated successfully!')
        
    except Exception as e:
        print(f'Error updating Excel file: {e}')
        import traceback
        traceback.print_exc()

def main():
    print("Starting PDF to Excel update process...")
    
    # Extract data from PDF
    regulation_data = extract_regulation_data()
    
    if regulation_data:
        # Update Excel file
        update_excel_file(regulation_data)
        print("\nProcess completed successfully!")
    else:
        print("No data extracted from PDF.")

if __name__ == "__main__":
    main()