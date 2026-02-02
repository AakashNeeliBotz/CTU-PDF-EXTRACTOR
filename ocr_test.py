import fitz
import pytesseract
from PIL import Image
import io
import os

pdf_path = r'c:\Users\Sree Charan\Desktop\fold2\CTU-PDF-EXTRACTOR\downloaded_pdfs\SN1\172381548953Minutes of 33rd CMETS NR meeting held on 05.08.2024.pdf'

doc = fitz.open(pdf_path)
page = doc[0]
pix = page.get_pixmap()
img_data = pix.tobytes("png")
img = Image.open(io.BytesIO(img_data))

# OCR the top part (top 20% of the page might contain the date)
width, height = img.size
top_part = img.crop((0, 0, width, height // 5))
text = pytesseract.image_to_string(top_part)

print("OCR Text from Top 20% of Page 1:")
print(text)

# Also try whole page if top part is not enough
# text_full = pytesseract.image_to_string(img)
# print("OCR Text from Page 1:")
# print(text_full[:1000])

doc.close()
