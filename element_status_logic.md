# Element Status Extraction Logic - Documentation

> **Note**: This logic was implemented but later removed due to approach issues. This document preserves the implementation details for reference.

## Table of Contents
1. [Overview](#overview)
2. [Element Types](#element-types)
3. [Architecture](#architecture)
4. [Annexure Elements Extraction](#annexure-elements-extraction)
5. [Developer Section Identification](#developer-section-identification)
6. [Element Extraction Patterns](#element-extraction-patterns)
7. [Code Implementation](#code-implementation)
8. [Example Output](#example-output)

---

## Overview

### Purpose
Extract transmission system elements (ATS, DTL, CTS) from SN1 PDF meeting minutes and populate the "Element Status" sheet with unique element codes linked to developer applications.

### PDF Structure
SN1 PDFs contain narrative meeting minutes with transmission element details in sections like:
```
Details of Transmission system for Connectivity under GNA:

A. Associated Transmission System (ATS): NIL

B. Transmission System under applicant scope
   (i). M/s Developer Name Solar Power Project – Substation PS 220 kV S/c line

C. Transmission system for Connectivity under GNA: As per Annexure-I
```

---

## Element Types

| Type | Full Name | Description | Example |
|------|-----------|-------------|---------|
| **ATS** | Associated Transmission System | System associated with the pooling station | "NIL" or specific transmission lines |
| **DTL** | Developer Transmission Line | Transmission system under applicant scope | "M/s Developer Project – Bikaner-V PS 220 kV S/c line" |
| **CTS** | Connectivity Transmission System | Transmission system for connectivity under GNA | Usually references an Annexure (e.g., "As per Annexure-I") |

---

## Architecture

### Global State Management

```python
# Global counters for unique element codes (persist across PDFs)
_element_code_counters = {'CTS': 0, 'DTL': 0, 'ATS': 0}

# Global collection of Element Status records
_element_status_records = []
```

**Why Global?**
- Element codes must be unique across all developers in all PDFs
- Records are collected during PDF processing, then written to Excel at the end
- Counters increment: CTS-001, CTS-002, CTS-003, etc.

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│  PDF Text + Developer Name                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  extract_transmission_elements(pdf_text, developer_name)    │
│  1. Find developer's section (strict keyword matching)      │
│  2. Extract ATS elements                                     │
│  3. Extract DTL elements                                     │
│  4. Extract CTS elements (or Annexure reference)            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  If CTS references Annexure:                                 │
│  parse_annexure_elements(pdf_text, "Annexure-I")            │
│  - Find Annexure section header                             │
│  - Extract numbered list items                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  For each element:                                           │
│  1. Generate unique code: generate_element_code('CTS')      │
│  2. Add to global records: add_element_status_record()      │
│  3. Link code to main data record                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Annexure Elements Extraction

### Purpose
Many CTS elements are listed in an Annexure section rather than inline. The `parse_annexure_elements()` function extracts these.

### Annexure Structure in PDF

```
Annexure-I: Transmission System (Tentative)

1. 765kV Bhadla-IV PS – Bikaner-V PS D/c line
2. Establishment of 6000 MW, HVDC terminal station (4x1500 MW) at Bikaner along 
   with associated EHVAC system
3. Associated EHVAC system strengthening in WR/SR/ER
4. Bhadla-II PS – Sikar-II 765kV D/c line (2nd)
```

### Implementation

```python
def parse_annexure_elements(pdf_text, annexure_name="Annexure-I"):
    """
    Parse numbered list of elements from an Annexure section.
    
    Args:
        pdf_text: Raw PDF text
        annexure_name: Name of annexure to find (e.g., "Annexure-I")
        
    Returns:
        List of element descriptions
    """
    import re
    
    if not pdf_text:
        return []
    
    elements = []
    text_lower = pdf_text.lower()
    
    # ------------------------------------------------------------
    # STEP 1: Find Annexure Header
    # ------------------------------------------------------------
    # Pattern variations:
    # - "Annexure-I: Transmission System"
    # - "ANNEXURE - I"
    # - "Annexure-I (Tentative)"
    
    annexure_patterns = [
        rf'{annexure_name.lower()}[:\s]*transmission\s+system[^.]*?(?:tentative)?[:\s]*',
        rf'annexure[\s\-]*i[:\s]*',
    ]
    
    annexure_start = -1
    for pattern in annexure_patterns:
        match = re.search(pattern, text_lower)
        if match:
            annexure_start = match.end()
            break
    
    if annexure_start == -1:
        return []  # Annexure not found
    
    # ------------------------------------------------------------
    # STEP 2: Extract Text After Header
    # ------------------------------------------------------------
    # Limit to 5000 chars to avoid parsing unrelated content
    remaining_text = pdf_text[annexure_start:annexure_start + 5000]
    
    # ------------------------------------------------------------
    # STEP 3: Find Numbered Items
    # ------------------------------------------------------------
    # Pattern: "1. ", "2. ", "3. ", etc.
    # Captures: number + dot + description until next number
    
    # Example matches:
    # "1. 765kV Bhadla-IV PS – Bikaner-V PS D/c line"
    # "2. Establishment of 6000 MW, HVDC terminal station"
    
    numbered_pattern = r'(\d+)\.\s*([^\d][^.]*?(?:(?!\d+\.\s)[^.])*)'
    
    for match in re.finditer(numbered_pattern, remaining_text, re.IGNORECASE | re.DOTALL):
        element_text = match.group(2).strip()
        
        # Clean up whitespace
        element_text = re.sub(r'\s+', ' ', element_text)
        element_text = element_text.strip()
        
        # Filter out very short matches (likely extraction errors)
        if element_text and len(element_text) > 10:
            elements.append(element_text)
    
    return elements
```

### Key Patterns

| Pattern | Purpose | Example Match |
|---------|---------|---------------|
| `annexure[\s\-]*i[:\s]*` | Find Annexure header | "Annexure-I:", "ANNEXURE - I" |
| `(\d+)\.\s*([^\d][^.]*)` | Extract numbered items | "1. 765kV Bhadla-IV PS" |
| `re.sub(r'\s+', ' ', text)` | Normalize whitespace | "Line\n  with\n   breaks" → "Line with breaks" |

### Edge Cases Handled

1. **Multiple Annexures**: Only extracts from specified annexure (default: Annexure-I)
2. **No Annexure**: Returns empty list if header not found
3. **Short Matches**: Filters out matches < 10 chars (likely parsing errors)
4. **Whitespace Normalization**: Collapses multi-line descriptions into single line

---

## Developer Section Identification

### Challenge
PDFs contain multiple developers. Must identify the correct section for each developer.

### Strict Matching Approach

```python
# Normalize developer name
dev_lower = developer_name.lower().strip()
dev_lower = re.sub(r'^m/s\.?\s*', '', dev_lower)  # Remove "M/s" prefix
dev_lower = re.sub(r'\s*\(erstwhile[^)]*\)', '', dev_lower)  # Remove (erstwhile...) 

# Extract key identifying words
stop_words = {'and', 'the', 'pvt', 'ltd', 'private', 'limited', 'energy', 'power', 
              'solar', 'wind', 'renewable', 'renewables', 'green', 'project', 
              'projects', 'holding', 'holdings', 'company', 'corporation'}

dev_words = [w for w in dev_lower.split() if len(w) > 2 and w not in stop_words]

# Ensure at least 2 unique identifying words
if len(dev_words) < 2:
    dev_words = [w for w in dev_lower.split() if w not in stop_words][:2]
```

### Section Pattern

```python
# Require BOTH first two keywords to appear
section_pattern = rf'm/s\.?\s+[^.]*{re.escape(dev_words[0])}[^.]*{re.escape(dev_words[1])}[^.]*?details\s+of\s+transmission'

# Example: "Juniper Green Energy" → requires "juniper" AND "green"
# Matches: "M/s Juniper Green Energy Private Limited ... Details of Transmission"
# Rejects: "M/s Juniper Solar Power" (missing "green")
```

### Fallback: Context-Based Matching

If strict pattern fails:
```python
# Find "Details of Transmission" header
# Check if at least 2 developer keywords appear within ±400 chars
context_before = text_normalized[max(0, match.start()-400):match.start()]
context_after = text_normalized[match.end():match.end()+200]

words_found = sum(1 for w in dev_words[:3] if w in context_before or w in context_after)

if words_found >= min(2, len(dev_words)):
    # Valid match
```

---

## Element Extraction Patterns

### ATS (Associated Transmission System)

```python
# Pattern: "A. Associated Transmission System (ATS): [content]"
# Stops at: "B." or "Transmission System under"

ats_pattern = r'associated\s+transmission\s+system\s*\(?ats\)?\s*[:\-]?\s*([^\n]+?)(?=b\.|transmission\s+system\s+under|$)'

ats_match = re.search(ats_pattern, section_text, re.IGNORECASE)
if ats_match:
    ats_text = ats_match.group(1).strip()
    if ats_text.lower() != 'nil' and len(ats_text) > 2:
        result['ats'].append(ats_text)
```

**Example Matches**:
- "NIL" → Filtered out
- "765kV transmission line from Bhadla to Bikaner" → Captured

### DTL (Developer Transmission Line)

```python
# Pattern: "B. Transmission System under applicant scope"
# Can have sub-items: "(i).", "(ii).", etc.

dtl_pattern = r'transmission\s+system\s+under\s+applicant\s+scope\s*[:\-]?\s*(?:\([^)]*\)\s*)?(.+?)(?=c\.|transmission\s+system\s+for\s+connectivity|$)'

dtl_match = re.search(dtl_pattern, section_text, re.IGNORECASE | re.DOTALL)
if dtl_match:
    dtl_text = dtl_match.group(1).strip()
    
    # Check for numbered sub-items: (i), (ii), (iii)
    sub_items = re.findall(r'\([ivx]+\)\.\s*([^(]+?)(?=\([ivx]+\)\.|$)', dtl_text, re.IGNORECASE)
    
    if sub_items:
        result['dtl'].extend([item.strip() for item in sub_items if item.strip()])
    elif dtl_text.lower() != 'nil' and len(dtl_text) > 10:
        result['dtl'].append(dtl_text)
```

**Example Matches**:
```
Input:
"(i). M/s Developer Solar Power Project – Bikaner-V PS 220 kV S/c line
 (ii). Common Pooling station for M/s Developer (App. No. 123 & 456)"

Output:
['M/s Developer Solar Power Project – Bikaner-V PS 220 kV S/c line',
 'Common Pooling station for M/s Developer (App. No. 123 & 456)']
```

### CTS (Connectivity Transmission System)

```python
# Pattern: "C. Transmission system for Connectivity under GNA: [content]"

cts_pattern = r'transmission\s+system\s+for\s+connectivity\s+under\s+gna\s*[:\-]?\s*(.+?)(?=page\s+\d+|$)'

cts_match = re.search(cts_pattern, section_text, re.IGNORECASE | re.DOTALL)
if cts_match:
    cts_text = cts_match.group(1).strip()
    
    # Check if it references an Annexure
    annexure_ref = re.search(r'as\s+per\s+(annexure[^\s]*)', cts_text, re.IGNORECASE)
    
    if annexure_ref:
        result['cts_annexure'] = annexure_ref.group(1)  # "Annexure-I"
    elif cts_text.lower() != 'nil' and len(cts_text) > 10:
        result['cts'].append(cts_text)
```

**Annexure Reference Handling**:
```python
if elements.get('cts_annexure'):
    # Parse the referenced Annexure
    annexure_elements = parse_annexure_elements(pdf_text, elements['cts_annexure'])
    
    # Generate CTS codes for each Annexure element
    for element_desc in annexure_elements:
        code = generate_element_code('CTS')
        add_element_status_record(code, element_desc, 'CTS', developer_name)
```

---

## Code Implementation

### 1. Generate Unique Element Codes

```python
_element_code_counters = {'CTS': 0, 'DTL': 0, 'ATS': 0}

def generate_element_code(prefix):
    """
    Generate unique element code with incrementing counter.
    
    Args:
        prefix: 'CTS', 'DTL', or 'ATS'
        
    Returns:
        Unique code like 'CTS-001', 'DTL-002', etc.
    """
    global _element_code_counters
    _element_code_counters[prefix] += 1
    return f"{prefix}-{_element_code_counters[prefix]:03d}"
```

**Output Examples**: CTS-001, CTS-002, DTL-001, ATS-001

### 2. Add Record to Global Collection

```python
_element_status_records = []

def add_element_status_record(element_code, element_description, scope, developer_name):
    """
    Add an element to the Element Status records collection.
    
    Args:
        element_code: Unique code (e.g., CTS-001)
        element_description: Full element description text
        scope: 'ATS', 'DTL', or 'CTS'
        developer_name: Name of developer awarded the element
    """
    global _element_status_records
    _element_status_records.append({
        'element_code': element_code,
        'inter_intra_tx_element': element_description,
        'transmission_scope': scope,
        'awarded_to': developer_name
    })
```

### 3. Reset and Retrieve Records

```python
def reset_element_code_counters():
    """Reset element code counters and Element Status records (call at start of processing)."""
    global _element_code_counters, _element_status_records
    _element_code_counters = {'CTS': 0, 'DTL': 0, 'ATS': 0}
    _element_status_records = []

def get_element_status_records():
    """Return collected Element Status records."""
    global _element_status_records
    return _element_status_records
```

### 4. Integration in Main Pipeline

```python
# In extract_sn1_records_from_table():

# Skip element extraction for Withdrawn/Revoked developers
if status not in ['Withdrawn', 'Revoked']:
    elements = extract_transmission_elements(pdf_text, applicant)
    
    # Generate codes for ATS elements
    ats_codes = []
    for ats_elem in elements.get('ats', []):
        code = generate_element_code('ATS')
        ats_codes.append(code)
        add_element_status_record(code, ats_elem, 'ATS', applicant)
    if ats_codes:
        record['ats_element_unique_code'] = ', '.join(ats_codes)
    
    # Generate codes for DTL elements
    dtl_codes = []
    for dtl_elem in elements.get('dtl', []):
        code = generate_element_code('DTL')
        dtl_codes.append(code)
        add_element_status_record(code, dtl_elem, 'DTL', applicant)
    if dtl_codes:
        record['dtl_element_unique_code'] = ', '.join(dtl_codes)
    
    # Generate codes for CTS elements
    cts_codes = []
    
    # If CTS references an Annexure, parse it
    if elements.get('cts_annexure'):
        annexure_elements = parse_annexure_elements(pdf_text, elements['cts_annexure'])
        for element_desc in annexure_elements:
            code = generate_element_code('CTS')
            cts_codes.append(code)
            add_element_status_record(code, element_desc, 'CTS', applicant)
    else:
        # Regular CTS elements
        for cts_elem in elements.get('cts', []):
            code = generate_element_code('CTS')
            cts_codes.append(code)
            add_element_status_record(code, cts_elem, 'CTS', applicant)
    
    if cts_codes:
        record['cts_element_unique_code'] = ', '.join(cts_codes)
```

---

## Example Output

### Input PDF Section

```
M/s Avaada Energy Private Limited has applied for 400 MW connectivity.

Details of Transmission system for Connectivity under GNA:

A. Associated Transmission System (ATS): NIL

B. Transmission System under applicant scope
   (i). M/s Avaada Energy Solar Power Project – Bhadla-V PS 220 kV S/c line

C. Transmission system for Connectivity under GNA: As per Annexure-I
```

### Annexure-I Section

```
Annexure-I: Transmission System (Tentative)

1. 765kV Bhadla-IV PS – Bikaner-V PS D/c line
2. Establishment of 6000 MW, HVDC terminal station
3. Associated EHVAC system strengthening in WR/SR/ER
```

### Generated Records

#### Data to be Captured Sheet
| name_of_developers | ats_element_unique_code | dtl_element_unique_code | cts_element_unique_code |
|-------------------|------------------------|------------------------|------------------------|
| Avaada Energy Private Limited | - | DTL-001 | CTS-001, CTS-002, CTS-003 |

#### Element Status Sheet
| element_code | inter_intra_tx_element | transmission_scope | awarded_to |
|-------------|------------------------|-------------------|------------|
| DTL-001 | M/s Avaada Energy Solar Power Project – Bhadla-V PS 220 kV S/c line | DTL | Avaada Energy Private Limited |
| CTS-001 | 765kV Bhadla-IV PS – Bikaner-V PS D/c line | CTS | Avaada Energy Private Limited |
| CTS-002 | Establishment of 6000 MW, HVDC terminal station | CTS | Avaada Energy Private Limited |
| CTS-003 | Associated EHVAC system strengthening in WR/SR/ER | CTS | Avaada Energy Private Limited |

---

## Issues with This Approach

1. **Multiple Developers Sharing Annexures**: When multiple developers reference the same Annexure, the same elements get duplicated with different developer names.

2. **Section Boundary Detection**: Hard to determine where one developer's section ends and another begins, especially when PDF formatting is inconsistent.

3. **Annexure Attribution**: Annexures often contain regional/system-level elements not specific to individual developers.

4. **Element Uniqueness**: The same physical transmission line might be listed multiple times for different developers, getting different element codes.

5. **Withdrawn Developers**: Need to carefully filter out withdrawn applications to avoid extracting obsolete elements.

---

*This document was created to preserve the implementation details before removal of this logic.*
