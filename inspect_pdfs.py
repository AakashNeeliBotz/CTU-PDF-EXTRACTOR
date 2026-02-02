import PyPDF2
import os
import re

pdf_dir = r'c:\Users\Sree Charan\Desktop\fold2\CTU-PDF-EXTRACTOR\downloaded_pdfs\SN1'
files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]

for filename in files:
    path = os.path.join(pdf_dir, filename)
    print(f"\n--- File: {filename} ---")
    with open(path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        # Check first page
        page = reader.pages[0]
        text = page.extract_text()
        print("First 1000 characters of First Page:")
        print(text[:1000])
        
        # Look for Application IDs in the whole document (or first few pages)
        # Actually I should probably scan more pages if it's a meeting minutes document.
        # But for now let's just see the top part for the date.
