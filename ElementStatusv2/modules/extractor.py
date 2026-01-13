
import pdfplumber
import openpyxl
from openpyxl.utils import get_column_letter
import re
import os

class PDFExtractor:
    def __init__(self, target_text="Monitoring Report of Under Construction TBCB Projects"):
        self.target_text = target_text

    def is_number(self, s):
        if not isinstance(s, str): return False, None
        try:
            if s.isdigit(): return True, int(s)
            if re.match(r'^-?\d+(\.\d+)?$', s): return True, float(s)
            return False, None
        except: return False, None

    def extract(self, pdf_path):
        print(f"Opening PDF: {pdf_path}")
        all_tables = []
        started = False
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                if not started:
                    text = page.extract_text()
                    if text and self.target_text.lower() in text.lower():
                        print(f"  Found start on Page {page_num + 1}")
                        started = True
                
                if started:
                    tables = page.extract_tables()
                    for table in tables:
                        cleaned = [[(c.strip() if c else None) for c in row] for row in table]
                        all_tables.append(cleaned)
        return all_tables

    def merge_tables(self, tables):
        if not tables: return []
        merged = [row[:] for row in tables[0]]
        
        def is_header(row):
            return row and "SN" in str(row[0])

        for next_table in tables[1:]:
            if not next_table: continue
            if is_header(next_table[0]):
                merged.extend(next_table[1:])
            else:
                merged.extend(next_table)
        return merged

    def save_to_excel(self, data, output_path):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "All_Data"
        
        for row in data:
            proc_row = []
            for cell in row:
                if cell is None or cell == "": proc_row.append("")
                else:
                    is_num, val = self.is_number(cell)
                    proc_row.append(val if is_num else cell)
            ws.append(proc_row)
            
        ws.freeze_panes = "A2"
        wb.save(output_path)
        print(f"  Saved raw data to {output_path}")

    def run(self, pdf_path, output_excel):
        raw = self.extract(pdf_path)
        merged = self.merge_tables(raw)
        self.save_to_excel(merged, output_excel)
        return output_excel
