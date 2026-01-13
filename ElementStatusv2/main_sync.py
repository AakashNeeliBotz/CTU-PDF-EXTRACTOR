
import sys
import os
from modules.extractor import PDFExtractor
from modules.populator import ExcelPopulator

# Paths
MASTER_FILE = "Connectivity Application Data 1.xlsx"
TEMP_FILE = "Output_Report_TBCB_UC.xlsx"

def main():
    if len(sys.argv) < 2:
        print("Usage: python main_sync.py <path_to_pdf>")
        return

    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} not found.")
        return

    print("--- 1. PDF EXTRACTION ---")
    extractor = PDFExtractor()
    extractor.run(pdf_path, TEMP_FILE)

    print("\n--- 2. MASTER SYNC ---")
    populator = ExcelPopulator()
    result = populator.sync(TEMP_FILE, MASTER_FILE)
    print(result)

    print("\nWorkflow Complete.")

if __name__ == "__main__":
    main()
