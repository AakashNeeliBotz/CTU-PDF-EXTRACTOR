"""
Script to extract and analyze PDF content for 33rd and 34th CMETS meetings
"""
import fitz  # PyMuPDF
import re
import os

PDF_33 = r"c:\Users\Sree Charan\Desktop\fold2\CTU-PDF-EXTRACTOR\downloaded_pdfs\SN1\172381548953Minutes of 33rd CMETS NR meeting held on 05.08.2024.pdf"
PDF_34 = r"c:\Users\Sree Charan\Desktop\fold2\CTU-PDF-EXTRACTOR\downloaded_pdfs\SN1\172838877090Minutes of meeting 34th CMETS NR Meeting held on 20-9-24.pdf"

def extract_pdf_text(pdf_path):
    """Extract full text from PDF"""
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text("text")
    doc.close()
    return full_text

def find_application_sections(text):
    """Find all Application ID sections in the PDF"""
    # Look for patterns like "Application ID: 2200000516" or "GNA/ST II Application ID"
    app_id_pattern = r'(?:Application\s*ID|GNA/ST\s*II\s*Application\s*ID)[:\s]*(\d{10})'
    matches = re.findall(app_id_pattern, text, re.IGNORECASE)
    return matches

def find_transmission_sections(text, app_id):
    """Find the transmission sections for a specific application ID"""
    # Find the section for this application ID
    pattern = rf'{app_id}.*?(?=\d{{10}}|$)'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        section = match.group(0)
        
        # Look for transmission system sections
        result = {
            'app_id': app_id,
            'section_preview': section[:2000] if len(section) > 2000 else section
        }
        
        # Check for ATS
        if 'Associated Transmission System' in section or 'ATS' in section:
            ats_match = re.search(r'Associated\s*Transmission\s*System.*?(?=Transmission\s*System\s*under|$)', section, re.DOTALL | re.IGNORECASE)
            if ats_match:
                result['ATS'] = ats_match.group(0)[:500]
        
        # Check for DTL
        if 'Transmission System under applicant scope' in section or 'applicant scope' in section:
            dtl_match = re.search(r'Transmission\s*System\s*under\s*applicant\s*scope.*?(?=Transmission\s*system\s*for\s*Connectivity|Annexure|$)', section, re.DOTALL | re.IGNORECASE)
            if dtl_match:
                result['DTL'] = dtl_match.group(0)[:500]
        
        # Check for CTS/Annexure-II
        if 'Annexure-II' in section or 'CTS' in section or 'Connectivity under GNA' in section:
            cts_match = re.search(r'(?:Annexure-II|Connectivity\s*under\s*GNA).*', section, re.DOTALL | re.IGNORECASE)
            if cts_match:
                result['CTS'] = cts_match.group(0)[:1000]
        
        return result
    return None

def analyze_pdf(pdf_path):
    """Analyze a PDF and extract relevant sections"""
    print(f"\n{'='*80}")
    print(f"ANALYZING: {os.path.basename(pdf_path)}")
    print(f"{'='*80}")
    
    text = extract_pdf_text(pdf_path)
    print(f"Total characters extracted: {len(text)}")
    
    # Find all application IDs
    app_ids = find_application_sections(text)
    print(f"\nApplication IDs found: {app_ids}")
    
    # Look for "Details of Transmission system for Connectivity under GNA"
    if "Details of Transmission system for Connectivity under GNA" in text:
        print("\n[+] Found 'Details of Transmission system for Connectivity under GNA' section")
    
    # Check for key section markers
    markers = [
        "Associated Transmission System (ATS)",
        "Transmission System under applicant scope",
        "Transmission system for Connectivity under GNA",
        "Annexure-II"
    ]
    
    print("\nSection markers found:")
    for marker in markers:
        count = text.count(marker)
        if count > 0:
            print(f"  [+] '{marker}': {count} occurrence(s)")
    
    # Extract a sample section for analysis
    print("\n--- Sample section (first occurrence of 'Details of Transmission') ---")
    sample_match = re.search(r'Details of Transmission.*?(?:Annexure-II|$)', text, re.DOTALL | re.IGNORECASE)
    if sample_match:
        sample = sample_match.group(0)[:3000]
        # Encode to ASCII-safe for console
        print(sample.encode('ascii', 'replace').decode('ascii'))
    
    return text

def main():
    # Analyze both PDFs
    text_33 = analyze_pdf(PDF_33)
    text_34 = analyze_pdf(PDF_34)
    
    # Save full text for reference
    with open('pdf_33_text.txt', 'w', encoding='utf-8') as f:
        f.write(text_33)
    with open('pdf_34_text.txt', 'w', encoding='utf-8') as f:
        f.write(text_34)
    
    print("\n\nFull text saved to pdf_33_text.txt and pdf_34_text.txt")

if __name__ == "__main__":
    main()
