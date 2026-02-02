"""
Debug matching between CTS items and Element Codes
"""
import pandas as pd
import fitz
import re
from difflib import SequenceMatcher

EXCEL_PATH = r"c:\Users\Sree Charan\Desktop\fold2\CTU-PDF-EXTRACTOR\Connectivity_Application_Data_TEST_ALL_SHEETS38 (2).xlsx"
PDF_33 = r"c:\Users\Sree Charan\Desktop\fold2\CTU-PDF-EXTRACTOR\downloaded_pdfs\SN1\172381548953Minutes of 33rd CMETS NR meeting held on 05.08.2024.pdf"

def normalize_text(text):
    if not text:
        return ""
    text = str(text).lower()
    text = ' '.join(text.split())
    text = text.replace('–', '-').replace('—', '-')
    text = re.sub(r'[^\w\s\-/]', ' ', text)
    return text.strip()

def load_element_status():
    df = pd.read_excel(EXCEL_PATH, sheet_name='Element Status', header=None)
    
    element_map = {}
    code_to_desc = {}
    
    for i in range(len(df)):
        for j in range(min(6, len(df.columns))):
            cell = df.iloc[i, j]
            if pd.notna(cell):
                cell_str = str(cell).strip()
                if re.match(r'^EL-[A-Z0-9]{5}$', cell_str):
                    desc_col = 3 if j < 3 else 4
                    if desc_col < len(df.columns):
                        desc = df.iloc[i, desc_col]
                        if pd.notna(desc) and len(str(desc).strip()) > 10:
                            desc_str = str(desc).strip()
                            element_map[normalize_text(desc_str)] = cell_str
                            code_to_desc[cell_str] = desc_str
    
    return element_map, code_to_desc

def extract_annexure_ii():
    doc = fitz.open(PDF_33)
    text = ""
    for page in doc:
        text += page.get_text("text")
    doc.close()
    
    # Find Annexure-II
    pattern = r'Annexure-II\s*(.*?)(?=Annexure-[IVX\d]+|$)'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    
    if match:
        content = match.group(1)
        content = re.sub(r'Minutes of \d+.*?Page \d+ of \d+', '', content, flags=re.DOTALL)
        items = []
        for _, item_text in re.findall(r'(\d+)\.\s+(.+?)(?=\d+\.\s|\n\n|Additional|$)', content, re.DOTALL):
            cleaned = ' '.join(item_text.split())
            if len(cleaned) > 15:
                items.append(cleaned)
        return items
    return []

def main():
    print("Loading Element Status...")
    element_map, code_to_desc = load_element_status()
    print(f"Loaded {len(element_map)} element mappings")
    
    print("\nSample Element Status descriptions:")
    for i, (norm_desc, code) in enumerate(list(element_map.items())[:10]):
        orig = code_to_desc.get(code, "N/A")
        print(f"  {code}: {orig[:70]}...")
    
    print("\n\nExtracting Annexure-II items...")
    annexure_items = extract_annexure_ii()
    print(f"Found {len(annexure_items)} items")
    
    print("\nAnnexure-II items:")
    for i, item in enumerate(annexure_items[:5]):
        print(f"  {i+1}. {item[:80]}...")
    
    print("\n\nTrying to match Annexure-II items to Element Codes...")
    for item in annexure_items[:5]:
        item_norm = normalize_text(item)
        print(f"\nItem: {item[:60]}...")
        print(f"  Normalized: {item_norm[:60]}...")
        
        # Try exact match
        if item_norm in element_map:
            print(f"  EXACT MATCH: {element_map[item_norm]}")
            continue
        
        # Try partial match
        found = False
        for key, code in element_map.items():
            if len(key) > 15:
                score = SequenceMatcher(None, item_norm, key).ratio()
                if score > 0.6:
                    print(f"  FUZZY MATCH (score={score:.2f}): {code} -> {code_to_desc[code][:50]}...")
                    found = True
                    break
        
        if not found:
            print("  NO MATCH FOUND")
            # Try to find best candidate
            best_score = 0
            best_code = None
            for key, code in element_map.items():
                if len(key) > 15:
                    score = SequenceMatcher(None, item_norm, key).ratio()
                    if score > best_score:
                        best_score = score
                        best_code = code
            if best_code:
                print(f"  Best candidate (score={best_score:.2f}): {best_code}")
                print(f"    -> {code_to_desc[best_code][:60]}...")

if __name__ == "__main__":
    main()
