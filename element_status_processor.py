
import pdfplumber
import openpyxl
import pandas as pd
import re
import os
import warnings
from openpyxl.utils import get_column_letter

# Suppress pandas warnings
warnings.filterwarnings("ignore")

class ElementStatusProcessor:
    """
    Processor for 'Element Status' sheet data extraction.
    Integrates functionality from ElementStatusv2/modules/extractor.py and populator.py.
    """
    
    def __init__(self, target_text="Monitoring Report of Under Construction TBCB Projects"):
        self.target_text = target_text
        
        # --- Ported from ExcelPopulator.__init__ ---
        self.src_cols_map = {
            'Scope': ['Name', 'Scope'],
            'SPV': ['SPV', 'Transfe'],
            'Locs': ['Total', 'Locs'],
            'Found': ['Found', 'ation', 'Nos'],
            'Erect': ['Erecti', 'on', 'Nos'],
            'String': ['Stringin', 'g'],
            'Civil': ['Civil', 'works'],
            'EqptRec': ['Eqpt', 'Receive'],
            'EqptEre': ['Eqpt', 'Erectio'],
            'OrgSCOD': ['Target', 'Org'],
            'AntSCOD': ['Target', 'Anticipate'],
            'Remarks': ['Remarks'],
            'Length': ['Lengt', 'h']
        }
        
        # Absolute Column Indices (1-based) for the TARGET Excel
        self.mapping_rules = {
            16: 'SPV', 17: 'Length', 18: 'Locs', 19: 'Found', 20: 'Erect',
            21: 'String', 22: 'CALC_FOUND', 23: 'CALC_ERECT', 24: 'CALC_STRING',
            25: 'Civil', 26: 'EqptRec', 27: 'EqptEre', 28: 'OrgSCOD',
            29: 'AntSCOD', 30: 'Remarks'
        }

    # --- Methods from PDFExtractor ---
    def is_number(self, s):
        if not isinstance(s, str): return False, None
        try:
            if s.isdigit(): return True, int(s)
            if re.match(r'^-?\d+(\.\d+)?$', s): return True, float(s)
            return False, None
        except: return False, None

    def extract_from_pdf(self, pdf_path):
        """Extract tables from PDF (Ported from PDFExtractor.extract)"""
        print(f"  [Element Status] Opening PDF: {pdf_path}")
        all_tables = []
        started = False
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                if not started:
                    # Check first portion of text to see if we reached the section
                    text = page.extract_text()
                    if text and self.target_text.lower() in text.lower():
                        print(f"  [Element Status] Found start on Page {page_num + 1}")
                        started = True
                
                if started:
                    # Extract tables from this page
                    tables = page.extract_tables()
                    for table in tables:
                        # Clean cells
                        cleaned = [[(c.strip() if c else None) for c in row] for row in table]
                        all_tables.append(cleaned)
        return all_tables

    def merge_tables(self, tables):
        """Merge multiple extracted tables (Ported from PDFExtractor.merge_tables)"""
        if not tables: return []
        def is_header(row):
            # Heuristic: headers usually have "SN" in the first column
            if not row or not row[0]: return False
            val = str(row[0]).lower()
            return "sn" in val or "s.n" in val or "sl.no" in val

        # Find the first table that looks like a data table
        start_idx = 0
        start_row_idx = 0
        found_start = False
        
        for i, table in enumerate(tables):
            if not table: continue
            # Check first few rows of the table for header-like content
            for r_idx, row in enumerate(table[:5]): # Check first 5 rows
                # Check for key columns
                row_str = " ".join([str(c).lower() for c in row if c])
                
                has_sn = "sn" in row_str.split() or "s.n" in row_str or "sl.no" in row_str or "sl. no" in row_str
                has_scope = "scope" in row_str or "name" in row_str or "project" in row_str or "element" in row_str
                
                if has_sn and has_scope:
                    start_idx = i
                    start_row_idx = r_idx
                    found_start = True
                    break
            if found_start: break
            
        if not found_start:
            print("  [Element Status] Warning: Could not identify start table with standard headers. Using first table.")
            start_idx = 0
            start_row_idx = 0

        merged = [row[:] for row in tables[start_idx][start_row_idx:]]
        # If the matched row was not the first row, we should probably strip rows before it?
        # But usually headers are at top of table.
        
        # Merge subsequent
        for next_table in tables[start_idx+1:]:
            if not next_table: continue
            if is_header(next_table[0]):
                # If next table has header, skip it (append rows from index 1)
                merged.extend(next_table[1:])
            else:
                # No header, append all rows
                merged.extend(next_table)
        return merged

    def convert_to_dataframe(self, raw_data):
        """Convert list of lists to Pandas DataFrame for easier processing"""
        if not raw_data:
            return pd.DataFrame()
            
        # Assume first row is header if valid
        headers = raw_data[0]
        # Ensure unique headers
        data = raw_data[1:]
        
        # Basic cleanup of headers
        clean_headers = [str(h).strip() if h else f"Col_{i}" for i, h in enumerate(headers)]
        
        df = pd.DataFrame(data, columns=clean_headers)
        return df

    # --- Methods from ExcelPopulator ---
    def clean_text(self, val):
        if pd.isna(val) or val is None: return None
        # Normalize: strip, replace newlines/tabs with space, collapse multiple spaces
        text = str(val).strip().replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        # Standardize dashes and common special characters
        text = text.replace('û', '-').replace('–', '-').replace('—', '-')
        text = re.sub(r'\s+', ' ', text).strip()
        # Lowercase for consistent semantic matching
        return text.lower()

    def to_float(self, val):
        try: return float(val) if not pd.isna(val) else 0.0
        except: return 0.0

    def find_col(self, df, keywords):
        for col in df.columns:
            if all(k.lower() in str(col).lower() for k in keywords):
                return col
        return None

    def process_and_write(self, pdf_path, target_excel_path):
        """
        Main orchestration method:
         1. Extract tables from PDF
         2. Convert to intermediate DataFrame (Logic from Populator.sync loaded part)
         3. Write to Target Excel (Logic from Populator.sync write part)
        """
        # 1. Extract Data
        raw_tables = self.extract_from_pdf(pdf_path)
        merged_data = self.merge_tables(raw_tables)
        
        if not merged_data:
            print("  [Element Status] No data extracted from PDF.")
            return

        # 2. Prepare Source Data (in-memory)
        # We need to map the raw extracted columns to our internal 'src_data' dict
        # First, find the column names from the headers (first row of merged_data)
        
        if not merged_data: return
        
        # Create a temp DF for column mapping logic
        headers = merged_data[0]
        # print(f"  [DEBUG] Extracted Headers: {headers}")
        df_src = pd.DataFrame(merged_data[1:], columns=headers)
        
        # Identical logic to Populator.sync for finding source columns
        src_cols = {}
        for k, kw in self.src_cols_map.items():
            found = self.find_col(df_src, kw)
            if found: src_cols[k] = found
            else: print(f"  [Element Status] Warning: Missing source col for {k} ({kw})")

        src_data = {}
        for _, r in df_src.iterrows():
            if 'Scope' in src_cols:
                k_val = self.clean_text(r[src_cols['Scope']])
                if k_val: src_data[k_val] = r
            
        print(f"  [Element Status] Loaded {len(src_data)} records from extracted tables.")

        # 3. Write to Excel
        if not os.path.exists(target_excel_path):
            print(f"  [Element Status] Error: Target Excel {target_excel_path} does not exist.")
            return

        wb = openpyxl.load_workbook(target_excel_path)
        
        # Check if sheet exists, if not create it (though template should have it)
        if "Element Status" not in wb.sheetnames:
            print("  [Element Status] Creating new 'Element Status' sheet.")
            ws = wb.create_sheet("Element Status")
            # You might need to setup headers here if creating from scratch
        else:
            ws = wb["Element Status"]
            
        # Identify Scope Column in Target (Search Row 2)
        # Ported logic:
        scope_col = None
        for cell in ws[2]:
            if cell.value and "Transmission Scope" in str(cell.value):
                scope_col = cell.column
                break
        
        if not scope_col:
            print("  [Element Status] Error: 'Transmission Scope' column not found in row 2 of target sheet.")
            # Fallback or return? Let's return for safety.
            return

        updates, skips = 0, 0
        target_rows = list(ws.iter_rows(min_row=4))
        
        src_keys = list(src_data.keys())
        matched_src_indices = set()
        
        print(f"  [Element Status] Processing {len(target_rows)} rows in target Excel...")

        for r_idx, row_cells in enumerate(target_rows):
            # Safety check for column index
            if scope_col - 1 >= len(row_cells): continue
            
            raw_target_val = row_cells[scope_col-1].value
            target_key = self.clean_text(raw_target_val)
            
            src_row = None
            
            # Logic: If target is empty/too short, try sequential fill
            if not target_key or len(target_key) < 5:
                # Sequential Fallback
                if r_idx < len(src_keys):
                    sk = src_keys[r_idx]
                    src_row = src_data[sk]
                    matched_src_indices.add(r_idx)
            else:
                # Match Logic: Strict -> Fuzzy
                if target_key in src_data:
                    src_row = src_data[target_key]
                    try: matched_src_indices.add(src_keys.index(target_key))
                    except: pass
                else:
                    # Fuzzy match
                    for idx, sk in enumerate(src_keys):
                        if target_key in sk or sk in target_key:
                            src_row = src_data[sk]
                            matched_src_indices.add(idx)
                            break
            
            if src_row is None:
                continue

            # CLEAR specific columns before writing
            source_row_idx = row_cells[0].row
            
            # Clear logic from original code: Cols 3, 4, 5 (C, D, E) and mapped cols
            # Note: openpyxl is 1-based. 3=C, 4=D, 5=E.
            for col_idx in [3, 4, 5]:
                ws.cell(row=source_row_idx, column=col_idx).value = None
            for col_idx in self.mapping_rules.keys():
                ws.cell(row=source_row_idx, column=col_idx).value = None

            # Write Transmission Scope into Col 5 (E)
            src_scope_val = src_row[src_cols['Scope']]
            ws.cell(row=source_row_idx, column=5, value=src_scope_val)

            # Populate Other Mapping Rules
            for col_idx, rule in self.mapping_rules.items():
                cell = ws.cell(row=source_row_idx, column=col_idx)
                val = None
                
                if rule.startswith('CALC_'):
                    try:
                        k = rule.split('_')[1]
                        # Logic: Found/Locs, Erect/Locs, String/Length
                        num_col = src_cols['Found'] if k=='FOUND' else (src_cols['Erect'] if k=='ERECT' else src_cols['String'])
                        den_col = src_cols['Locs'] if k!='STRING' else src_cols['Length']
                        
                        num = self.to_float(src_row[num_col])
                        den = self.to_float(src_row[den_col])
                        
                        if den > 0: val = round(num/den, 2)
                    except: pass
                else:
                    src_col_name = src_cols.get(rule)
                    if src_col_name:
                        val = src_row[src_col_name]
                
                if val is not None and not pd.isna(val):
                    # Clean the value if string
                    if isinstance(val, str):
                        # Use is_number to check if it's numeric string (Ported from extractor)
                        is_num, num_val = self.is_number(val)
                        cell.value = num_val if is_num else val
                    else:
                        cell.value = val
                    updates += 1

        # APPEND Unmatched Records
        unmatched_indices = [i for i in range(len(src_keys)) if i not in matched_src_indices]
        
        if unmatched_indices:
            print(f"  [Element Status] Appending {len(unmatched_indices)} new records...")
            for idx in unmatched_indices:
                src_row = src_data[src_keys[idx]]
                
                # Create empty row list sufficient to cover max column index
                max_col = max(30, max(self.mapping_rules.keys()))
                new_row = [None] * (max_col + 1) # +1 for safety/padding
                
                # Transmission Scope at index 4 (Col 5)
                new_row[4] = src_row[src_cols['Scope']]
                
                for col_idx, rule in self.mapping_rules.items():
                    val = None
                    if rule.startswith('CALC_'):
                        try:
                            k = rule.split('_')[1]
                            num_col = src_cols['Found'] if k=='FOUND' else (src_cols['Erect'] if k=='ERECT' else src_cols['String'])
                            den_col = src_cols['Locs'] if k!='STRING' else src_cols['Length']
                            
                            num = self.to_float(src_row[num_col])
                            den = self.to_float(src_row[den_col])
                            
                            if den > 0: val = round(num/den, 2)
                        except: pass
                    else:
                        src_col_name = src_cols.get(rule)
                        if src_col_name: val = src_row[src_col_name]

                    if val is not None and not pd.isna(val):
                         if isinstance(val, str):
                             is_num, num_val = self.is_number(val)
                             new_row[col_idx-1] = num_val if is_num else val # openpyxl append takes list, 0-indexed relative to row? No, list maps to A, B, C...
                         else:
                             new_row[col_idx-1] = val
                
                ws.append(new_row)
                
        wb.save(target_excel_path)
        print(f"  [Element Status] Completed. {updates} updates made.")
