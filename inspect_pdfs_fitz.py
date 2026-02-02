import fitz # PyMuPDF
import os

pdf_dir = r'c:\Users\Sree Charan\Desktop\fold2\CTU-PDF-EXTRACTOR\downloaded_pdfs\SN1'
files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]

for filename in files:
    path = os.path.join(pdf_dir, filename)
    print(f"\n--- File: {filename} ---")
    doc = fitz.open(path)
    if len(doc) > 0:
        page = doc[0]
        text = page.get_text()
        print("First 1000 characters of First Page:")
        print(text[:1000])
    doc.close()
