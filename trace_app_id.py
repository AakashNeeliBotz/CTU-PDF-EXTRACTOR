"""
Trace specific Application ID to understand why it's not being updated
"""
import fitz
import re

PDF_33 = r"c:\Users\Sree Charan\Desktop\fold2\CTU-PDF-EXTRACTOR\downloaded_pdfs\SN1\172381548953Minutes of 33rd CMETS NR meeting held on 05.08.2024.pdf"

def trace_app_id(app_id):
    """Find and display all content related to an Application ID"""
    doc = fitz.open(PDF_33)
    full_text = ""
    for page in doc:
        full_text += page.get_text("text")
    doc.close()
    
    print(f"\n{'='*60}")
    print(f"TRACING Application ID: {app_id}")
    print(f"{'='*60}")
    
    # Find all occurrences
    pattern = re.compile(rf'.{{500}}{app_id}.{{1500}}', re.DOTALL)
    matches = pattern.findall(full_text)
    
    print(f"\nFound {len(matches)} occurrences in PDF")
    
    for i, match in enumerate(matches[:2]):  # Show first 2 matches
        print(f"\n--- Occurrence {i+1} ---")
        # Clean for display
        clean = match.encode('ascii', 'replace').decode('ascii')
        print(clean)
    
    # Specifically look for transmission system section
    print("\n\n--- Looking for Details of Transmission section ---")
    
    # Find the section following this app ID
    idx = full_text.find(app_id)
    if idx > 0:
        # Find "Details of Transmission" AFTER this app ID
        after_text = full_text[idx:idx+5000]
        trans_idx = after_text.find("Details of Transmission system for Connectivity under GNA:")
        if trans_idx > 0:
            section = after_text[trans_idx:trans_idx+2500]
            print(section.encode('ascii', 'replace').decode('ascii'))
        else:
            print(f"'Details of Transmission' not found after App ID")
            print(f"Text after App ID:")
            print(after_text[:1500].encode('ascii', 'replace').decode('ascii'))

if __name__ == "__main__":
    # Test with specific app IDs that should be updated
    trace_app_id("2200000567")
    trace_app_id("2200000618")
