import fitz
import pytesseract
from PIL import Image
import io
import os
import re

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

pdf_dir = r'c:\Users\Sree Charan\Desktop\fold2\CTU-PDF-EXTRACTOR\downloaded_pdfs\SN1'
files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]

for filename in files:
    path = os.path.join(pdf_dir, filename)
    print(f"\n--- File: {filename} ---")
    doc = fitz.open(path)
    page = doc[0]
    pix = page.get_pixmap()
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    
    # Crop top 20%
    w, h = img.size
    top = img.crop((0, 0, w, h // 4))
    text = pytesseract.image_to_string(top)
    print("Top OCR text:")
    print(text)
    
    # Try to find date
    date_match = re.search(r'(\d{2}[-./]\d{2}[-./]\d{2,4})', text)
    if date_match:
        print(f"Extracted Date: {date_match.group(1)}")
    
    doc.close()
