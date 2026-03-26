# Knowledge Transfer: CMETS NR Extractor

> **Project**: CTU Automated PDF Extraction  
> **Date**: 2026-03-26  
> **For**: Incoming team member (cold start)

---

## 1. What This Project Does

This pipeline **extracts structured data from CTU CMETS meeting-minutes PDFs** and produces a single Excel workbook + CSV. CMETS stands for *Committee for Monitoring of Elements of Transmission System — Northern Region*.

**In plain terms**: Government/regulatory meetings produce PDF documents filled with tables about power transmission connectivity applications. This code reads those PDFs, parses the tables, applies business rules, and writes everything into a clean Excel workbook.

---

## 2. Source Files (Inputs)

| Category | Location | Files |
|---|---|---|
| CMETS Meeting PDFs | `Data to be captured PDFs/` | 10 PDFs (34th through 43rd meeting) |
| RE-Effectiveness PDFs | `Data to be captured PDFs/` | 3 PDFs (Oct, Sept, Dec) |
| SN9 Margin PDFs | `Margin PDFs/` | Multiple connectivity-margin reports |
| Element Status PDFs | `Element Status PDFs/` | TBCB, RTM, 35th NCT PDFs |
| Template Workbook | Root | `Connectivity Application Data.xlsx` |

---

## 3. Output Files

| File | Content |
|---|---|
| [42nd_34th_CMETS_Extracted_Data_VoltageFix.xlsx](file:///c:/Users/Admin/Documents/CTU-automated-pdf-extraction/42nd_34th_CMETS_Extracted_Data_VoltageFix.xlsx) | Main workbook with 4 sheets |
| [extracted_data.csv](file:///c:/Users/Admin/Documents/CTU-automated-pdf-extraction/extracted_data.csv) | CSV of the "Data to be captured" sheet |

### Excel Workbook Sheets

| Sheet | Description | Row Count |
|---|---|---|
| **Data to be captured** | Connectivity application records from all 10 meetings | 254 |
| **Bulk Consumers** | GNARE/Bulk consumer records | 27 |
| **Margin** | SN9 connectivity margin data | 232 |
| **Element Status** | TBCB, RTM, NCT, and CMETS-derived elements | 796 |

---

## 4. End-to-End Pipeline Flow

```
[Source PDFs] → Pipeline → [Excel + CSV]
```

**Detailed steps** (in exact execution order):

1. **Build RE-effectiveness lookup** — Reads Oct PDF first, then Sept as fallback, then Dec for detail merge
2. **Extract "Data to be captured"** — Processes meetings in fixed order: `43rd → 42nd → 41st → 40th → 39th → 38th → 37th → 36th → 35th → 34th`
3. **Apply RE-effectiveness rules** — Merges RE data, handles hybrid breakup and LTA/ST-II expansion
4. **Apply CMETS element codes** — Maps ATS/DTL/CTS codes to records
5. **Post-processing** — Fill empty granted quantum with `0`, apply output normalizations
6. **Extract Bulk Consumers** — From GNARE tables in each meeting PDF
7. **Extract Margin** — From SN9 connectivity margin PDFs
8. **Write workbook** — Sheets: Data → Bulk Consumers → Margin
9. **Populate Element Status** — Source order: `TBCB → RTM → NCT → CMETS`
10. **Write CSV** — [extracted_data.csv](file:///c:/Users/Admin/Documents/CTU-automated-pdf-extraction/extracted_data.csv)

---

## 5. Code Architecture (High-Level)

```
extract_42nd_cmets.py          ← CLI entry (thin shim — don't add logic here)
  └── cmets_extractor/
       ├── pipeline.py           ← runs the full pipeline in order
       ├── run_context.py        ← shared mutable state (caches/catalogs)
       ├── config.py             ← all paths, constants, column maps
       ├── types.py              ← TypedDict shapes (DataCaptureRecord, etc.)
       ├── adapters/             ← I/O layer
       │    ├── pdf.py           ← Camelot table reads
       │    ├── workbook.py      ← writes Data/Bulk/Margin sheets
       │    ├── csv.py           ← writes CSV
       │    └── element_status_workbook.py  ← Element Status sheet
       └── domain/               ← business logic layer
            ├── common/          ← text, IDs, numbers, dates helpers
            ├── meetings/        ← per-meeting extractors
            │    ├── forty_second.py   ← 42nd only
            │    ├── hybrid.py         ← 35th–41st, 43rd (shared)
            │    └── thirty_fourth.py  ← 34th only
            ├── deliberation.py        ← deliberation text parsing
            ├── re_effectiveness.py    ← RE lookup + LTA expansion
            ├── data_capture_common.py ← shared parsing (substation, voltage, etc.)
            ├── hybrid_context.py      ← context selection for hybrid meetings
            ├── bulk_consumers.py      ← Bulk Consumer parsing
            ├── margin.py              ← Margin parsing
            ├── element_status.py      ← TBCB/RTM/NCT parsing
            └── element_status_runtime.py  ← CMETS element cache/catalog
```

### Key Principle

> **[pipeline](file:///c:/Users/Admin/Documents/CTU-automated-pdf-extraction/cmets_extractor/pipeline.py#195-498) orchestrates → `domain` decides → `adapters` do I/O**

### Where to Change Things

| What You Want to Change | File to Edit |
|---|---|
| Meeting order or output order | [pipeline.py](file:///c:/Users/Admin/Documents/CTU-automated-pdf-extraction/cmets_extractor/pipeline.py) |
| File paths, sheet names, constants | [config.py](file:///c:/Users/Admin/Documents/CTU-automated-pdf-extraction/cmets_extractor/config.py) |
| 42nd-only parsing | [domain/meetings/forty_second.py](file:///c:/Users/Admin/Documents/CTU-automated-pdf-extraction/cmets_extractor/domain/meetings/forty_second.py) |
| 34th-only parsing | [domain/meetings/thirty_fourth.py](file:///c:/Users/Admin/Documents/CTU-automated-pdf-extraction/cmets_extractor/domain/meetings/thirty_fourth.py) |
| 35th–43rd shared parsing | [domain/meetings/hybrid.py](file:///c:/Users/Admin/Documents/CTU-automated-pdf-extraction/cmets_extractor/domain/meetings/hybrid.py) |
| RE lookup / LTA expansion | [domain/re_effectiveness.py](file:///c:/Users/Admin/Documents/CTU-automated-pdf-extraction/cmets_extractor/domain/re_effectiveness.py) |
| Substation, voltage, capacity normalization | [domain/data_capture_common.py](file:///c:/Users/Admin/Documents/CTU-automated-pdf-extraction/cmets_extractor/domain/data_capture_common.py) |
| Bulk Consumers parsing | [domain/bulk_consumers.py](file:///c:/Users/Admin/Documents/CTU-automated-pdf-extraction/cmets_extractor/domain/bulk_consumers.py) |
| Margin parsing | [domain/margin.py](file:///c:/Users/Admin/Documents/CTU-automated-pdf-extraction/cmets_extractor/domain/margin.py) |
| Element Status parsing rules | [domain/element_status.py](file:///c:/Users/Admin/Documents/CTU-automated-pdf-extraction/cmets_extractor/domain/element_status.py) |
| Element Status workbook write | [adapters/element_status_workbook.py](file:///c:/Users/Admin/Documents/CTU-automated-pdf-extraction/cmets_extractor/adapters/element_status_workbook.py) |
| Workbook writing (Data/Bulk/Margin) | [adapters/workbook.py](file:///c:/Users/Admin/Documents/CTU-automated-pdf-extraction/cmets_extractor/adapters/workbook.py) |

---

## 6. Data Connections Map

```
CMETS PDFs (10) ──────────────→ "Data to be captured" sheet (254 rows)
                                    + extracted_data.csv
RE-Effectiveness PDFs (3) ─────→ RE lookup merged into "Data to be captured"
CMETS PDFs (10) ──────────────→ "Bulk Consumers" sheet (27 rows)
SN9 Margin PDFs ──────────────→ "Margin" sheet (232 rows)
TBCB PDF ─────────────────────→ 
RTM PDF ──────────────────────→  "Element Status" sheet (796 rows)
35th NCT PDF ─────────────────→     sources combined: TBCB → RTM → NCT → CMETS
CMETS PDFs (element text) ────→ 
Template workbook ────────────→ provides sheet structure and headers
```

---

## 7. Critical Business Rules

> [!CAUTION]
> These rules are validated invariants. Breaking them will produce incorrect output. Verify after any code change.

| # | Rule | Details |
|---|---|---|
| 1 | **42nd Reg. 5.2** | `granted_quantum_mw` must equal `application_quantum_mw` |
| 2 | **Withdrawn voltage** | Withdrawn rows must have **blank** voltage |
| 3 | **Empty granted quantum** | Fill with `0`, *except* intentionally partial expanded rows |
| 4 | **42nd SCOD** | Use the **last SCOD mention** in text order |
| 5 | **RE lookup priority** | Oct first → Sept fallback → Dec detail merge |
| 6 | **LTA expanded rows** | Copy only through `CMETS GNA Approved`; later fields stay blank |
| 7 | **34th reduced quantum** | "Reduced to X MW" → use reduced value in output |
| 8 | **Substation normalization** | Strip trailing `PS`; `Sirohi PS` → `Sirohi-I`; preserve `Sirohi-II` |
| 9 | **34th collapsed rows** | Must recover IDs `2200000793` and `2200000891` |
| 10 | **Sheet name** | Must remain `Data to be captured` (exact) |
| 11 | **Element Status order** | Source order: `TBCB → RTM → NCT → CMETS` |
| 12 | **Meeting extraction order** | `43rd → 42nd → 41st → 40th → 39th → 38th → 37th → 36th → 35th → 34th` |

---

## 8. Validation Checklist

After any code change, run the full pipeline and verify:

- [ ] `2200000793` and `2200000891` exist in output
- [ ] `2200000827` substation is `Sirohi-II`
- [ ] `2200001044` has application/granted/solar all = `50`
- [ ] 42nd Reg. 5.2 rows: `granted == applied`
- [ ] Expanded LTA rows have blank columns after `CMETS GNA Approved`
- [ ] Data to be captured = 254 rows
- [ ] Bulk Consumers = 27 rows
- [ ] Margin = 232 rows
- [ ] Element Status = 796 populated rows

---

## 9. How to Run

### Prerequisites

- **Python 3.10+**
- Dependencies listed in `requirements.txt`:
  - `camelot-py[cv]`, `opencv-python`, `PyMuPDF`, `pandas`, `openpyxl`
  - `fuzzywuzzy`, `python-Levenshtein`, `pdfplumber`, `pytesseract`, `Pillow`
  - `requests`, `beautifulsoup4`
- The existing project venv is at: `myvenv/` in the repo root

> [!IMPORTANT]
> **Always close the output Excel workbook** before running. If it's open, you'll get a `PermissionError`. The pipeline will fall back to a timestamped temp file, but it's best to close it.

---

### Option A: WSL (using the existing Windows venv) — RECOMMENDED

This is the current preferred setup. WSL calls the Windows Python venv directly.

```bash
# Navigate to repo
cd /mnt/c/Users/Admin/Documents/CTU-automated-pdf-extraction

# Run the extractor
"/mnt/c/Users/Admin/Documents/CTU-automated-pdf-extraction/myvenv/Scripts/python.exe" extract_42nd_cmets.py
```

**WSL-specific notes:**
- The Windows venv may emit `ESC[6n` (cursor-position query) in a PTY terminal. This is normal — reply with `ESC[1;1R` and keep the session alive.
- Do not treat `UtilBindVsockAnyPort:307: socket failed 1` errors as pipeline failures — these are WSL interop noise.
- If the script appears to hang after the first output, it's likely waiting for the PTY handshake above — it's not stuck.

---

### Option B: Native Windows (CMD)

```cmd
REM Navigate to repo
cd C:\Users\Admin\Documents\CTU-automated-pdf-extraction

REM Activate the existing venv
myvenv\Scripts\activate.bat

REM Run the extractor
python extract_42nd_cmets.py
```

---

### Option C: Native Windows (PowerShell)

```powershell
# Navigate to repo
cd C:\Users\Admin\Documents\CTU-automated-pdf-extraction

# Activate the existing venv
.\myvenv\Scripts\Activate.ps1

# Run the extractor
python extract_42nd_cmets.py
```

> [!NOTE]
> If you get an execution policy error in PowerShell, run:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

---

### Option D: Fresh Linux / macOS Setup

If you're setting up on a fresh machine without the existing venv:

```bash
# Clone the repo and navigate in
cd CTU-automated-pdf-extraction

# Create a new venv
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Verify key imports work
python3 -c "import camelot, fitz, pandas, openpyxl; print('All imports OK')"

# Run the extractor
python3 extract_42nd_cmets.py
```

**Linux-specific notes:**
- Camelot requires `ghostscript` and `tkinter` system packages:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install -y ghostscript python3-tk
  # Fedora/RHEL
  sudo dnf install -y ghostscript python3-tkinter
  # macOS (Homebrew)
  brew install ghostscript tcl-tk
  ```
- `pytesseract` requires Tesseract OCR installed:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install -y tesseract-ocr
  # macOS
  brew install tesseract
  ```

---

### Option E: Fresh WSL Setup (no existing venv)

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3.12-venv python3-pip ghostscript python3-tk tesseract-ocr

# Create a WSL-native venv
cd /mnt/c/Users/Admin/Documents/CTU-automated-pdf-extraction
python3 -m venv .venv_wsl
source .venv_wsl/bin/activate

# Install Python deps
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Verify imports
python3 -c "import camelot, fitz, pandas, openpyxl; print('All imports OK')"

# Run
python3 extract_42nd_cmets.py
```

---

### Running Tests

```bash
# WSL (with existing Windows venv)
"/mnt/c/Users/Admin/Documents/CTU-automated-pdf-extraction/myvenv/Scripts/python.exe" tests/run_test_suite.py

# Native Windows (venv activated)
python tests\run_test_suite.py

# Linux / macOS / WSL native venv
python3 tests/run_test_suite.py
```

For syntax-only checks on modified files:
```bash
python3 -m py_compile extract_42nd_cmets.py
python3 -m py_compile cmets_extractor/pipeline.py
```

---

### Quick Reference

| Environment | Run Command |
|---|---|
| WSL + Windows venv | `"/mnt/c/.../myvenv/Scripts/python.exe" extract_42nd_cmets.py` |
| Windows CMD | `myvenv\Scripts\activate.bat && python extract_42nd_cmets.py` |
| Windows PowerShell | `.\myvenv\Scripts\Activate.ps1; python extract_42nd_cmets.py` |
| Linux / macOS | `source .venv/bin/activate && python3 extract_42nd_cmets.py` |
| WSL native venv | `source .venv_wsl/bin/activate && python3 extract_42nd_cmets.py` |

---

## 10. Key Documentation Files

| File | Purpose |
|---|---|
| [update.md](file:///c:/Users/Admin/Documents/CTU-automated-pdf-extraction/update.md) | Short continuity notes — **read first** in every session |
| [refactor.md](file:///c:/Users/Admin/Documents/CTU-automated-pdf-extraction/refactor.md) | Architecture redesign tracking |
| [README.md](file:///c:/Users/Admin/Documents/CTU-automated-pdf-extraction/README.md) | Project overview and layout |
| [documentation.md](file:///c:/Users/Admin/Documents/CTU-automated-pdf-extraction/documentation.md) | Detailed architecture and code map |
| [AGENTS.md](file:///c:/Users/Admin/Documents/CTU-automated-pdf-extraction/AGENTS.md) | Rules for AI assistants working on this repo |

**Reading order for new sessions**: [update.md](file:///c:/Users/Admin/Documents/CTU-automated-pdf-extraction/update.md) → [refactor.md](file:///c:/Users/Admin/Documents/CTU-automated-pdf-extraction/refactor.md) → [README.md](file:///c:/Users/Admin/Documents/CTU-automated-pdf-extraction/README.md) → [extract_42nd_cmets.py](file:///c:/Users/Admin/Documents/CTU-automated-pdf-extraction/extract_42nd_cmets.py)

---

## 11. Tech Stack

| Library | Version | Purpose |
|---|---|---|
| **Camelot** | — | Lattice-mode table extraction from PDFs |
| **PyMuPDF** (`fitz`) | — | Text extraction from PDFs |
| **Pandas** | — | DataFrame manipulation |
| **OpenPyXL** | — | Excel workbook read/write |

---

## 12. KT Diagram

The visual KT diagram is available in Excalidraw showing all 4 zones:
- **Blue**: Source PDFs
- **Purple**: Pipeline Steps  
- **Green**: Outputs
- **Red**: Critical Business Rules

[Open in Excalidraw](https://excalidraw.com/#json=MD28rcVjxKkgziUZ7Iva2,43RpgKPdHgdJ8WIFR7BqXQ)
