
import pdfplumber
import re

class AnnexureExtractor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        # Header to ignore (page header present on every page)
        self.header_pattern = r"Minutes of .* Consultation Meeting .*"
        # Strict pattern: Annexure must be on its own line
        self.annexure_pattern = r"^Annexure-[IVXLCDM]+$"

    def clean_text(self, text):
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            # Skip known page headers
            if re.search(self.header_pattern, line, re.IGNORECASE):
                continue
            # Skip empty lines
            if not line.strip():
                continue
            cleaned_lines.append(line.strip())
        return cleaned_lines

    def extract_annexures(self):
        annexures = []
        print(f"Opening PDF: {self.pdf_path}")
        
        current_annexure = None  # Track multi-page annexures
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                lines = self.clean_text(text)
                if not lines:
                    continue
                
                # Check for a new Annexure starting on this page
                annexure_number = None
                annexure_line_idx = -1
                
                for idx, line in enumerate(lines[:5]):
                    if re.match(self.annexure_pattern, line.strip()):
                        annexure_number = line.strip()
                        annexure_line_idx = idx
                        break
                
                if annexure_number:
                    # Save previous annexure if exists
                    if current_annexure:
                        annexures.append(current_annexure)
                    
                    print(f"  Found '{annexure_number}' at Page {i+1}")
                    
                    # Title is the next line after the Annexure label
                    title = ""
                    title_line_idx = annexure_line_idx + 1
                    if title_line_idx < len(lines):
                        title = lines[title_line_idx].strip()
                    
                    # Body starts after title
                    body_lines = lines[title_line_idx+1:]
                    body_text = "\n".join(body_lines).strip()
                    
                    # Start new annexure
                    current_annexure = {
                        "page": i+1,
                        "annexure_number": annexure_number,
                        "title": title,
                        "body": body_text
                    }
                    
                elif current_annexure:
                    # This page is a CONTINUATION of the current annexure
                    # Append all content to the body
                    continuation_text = "\n".join(lines).strip()
                    current_annexure["body"] += "\n" + continuation_text
                    print(f"  Continuing '{current_annexure['annexure_number']}' on Page {i+1}")
        
        # Don't forget the last annexure
        if current_annexure:
            annexures.append(current_annexure)
        
        return annexures
