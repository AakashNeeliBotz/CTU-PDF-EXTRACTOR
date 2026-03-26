# CMETS NR Extractor

## What This Project Does

This is a **production data-extraction pipeline** that reads CTU (Central Transmission Utility) **CMETS NR** (Committee for Monitoring of Elements of Transmission System — Northern Region) **meeting-minutes PDFs** and produces a structured Excel workbook and CSV.

**In plain terms**: Government/regulatory meetings produce PDF documents containing tables about power transmission connectivity applications. This pipeline parses those PDFs, extracts tabular data, applies domain-specific business rules, and writes everything into a clean, validated Excel workbook.

## Tech Stack

| Library | Purpose |
|---|---|
| **Camelot** (`camelot-py[cv]`) | Lattice-mode table extraction from PDFs |
| **PyMuPDF** (`fitz`) | Text extraction from PDFs |
| **Pandas** | DataFrame manipulation during extraction |
| **OpenPyXL** | Excel workbook read/write |
| **pdfplumber** | Supplementary PDF parsing |
| **pytesseract** / **Pillow** | OCR support for scanned content |

## Current Coverage

The pipeline processes **10 CMETS meeting PDFs** in fixed order:

`43rd → 42nd → 41st → 40th → 39th → 38th → 37th → 36th → 35th → 34th`

Notes:
- `41st` is wired into the run but currently contributes `0` `Data to be captured` rows.
- `Bulk Consumers` is populated from GNARE tables across all supported CMETS PDFs.
- `Margin` is populated from the dedicated SN9 Margin PDFs.
- `Element Status` is populated from TBCB, RTM, 35th NCT, and CMETS-derived ATS/DTL/CTS elements.

## Outputs

| File | Content |
|---|---|
| `42nd_34th_CMETS_Extracted_Data_VoltageFix.xlsx` | Main workbook (4 sheets) |
| `extracted_data.csv` | CSV of the "Data to be captured" sheet |

### Workbook Sheets

| Sheet | Description | Validated Count |
|---|---|---|
| **Data to be captured** | Connectivity application records from all 10 meetings | 254 rows |
| **Bulk Consumers** | GNARE/Bulk consumer records | 27 rows |
| **Margin** | SN9 connectivity margin data | 232 rows |
| **Element Status** | TBCB, RTM, NCT, and CMETS-derived elements | 796 rows |

## Architecture

```
extract_42nd_cmets.py           ← thin CLI shim (entrypoint)
  └── cmets_extractor/
       ├── pipeline.py           ← orchestrates the full run
       ├── run_context.py        ← shared mutable state (caches/catalogs)
       ├── config.py             ← paths, constants, column maps
       ├── types.py              ← TypedDict shapes for all record types
       ├── adapters/             ← I/O layer (PDF, Excel, CSV)
       └── domain/               ← business logic layer
            ├── common/          ← text, IDs, numbers, dates helpers
            ├── meetings/        ← per-meeting extractors (42nd, 34th, hybrid)
            └── ...              ← deliberation, RE, margin, element status, etc.
```

**Key principle**: `pipeline` orchestrates → `domain` decides → `adapters` do I/O.

## Repository Layout

| Path | Description |
|---|---|
| `extract_42nd_cmets.py` | CLI entrypoint (thin compatibility shim) |
| `cmets_extractor/` | Main package — pipeline, domain logic, adapters |
| `Data to be captured PDFs/` | 10 CMETS meeting PDFs + 3 RE-effectiveness PDFs |
| `Margin PDFs/` | SN9 Connectivity Margin PDFs |
| `Element Status PDFs/` | TBCB, RTM, and 35th NCT source PDFs |
| `Connectivity Application Data.xlsx` | Template workbook (provides sheet structure) |
| `tests/` | Smoke, regression, rule characterization, and architecture tests |
| `kt_document.md` | Knowledge Transfer document for handoff |
| `documentation.md` | Detailed architecture and code map |
| `update.md` | Continuity notes and session handoff |
| `refactor.md` | Architecture redesign tracking |

## How To Run

### Prerequisites

- **Python 3.10+**
- Dependencies: `pip install -r requirements.txt`
- **Always close the output Excel workbook** before running to avoid `PermissionError`

---

### Option A: WSL (using the existing Windows venv) — RECOMMENDED

```bash
cd /mnt/c/Users/Admin/Documents/CTU-automated-pdf-extraction
"/mnt/c/Users/Admin/Documents/CTU-automated-pdf-extraction/myvenv/Scripts/python.exe" extract_42nd_cmets.py
```

**WSL notes:**
- The Windows venv may emit `ESC[6n` (cursor-position query) in a PTY. Reply with `ESC[1;1R` and keep the session alive.
- Ignore `UtilBindVsockAnyPort:307: socket failed 1` — it's WSL interop noise, not a pipeline failure.

---

### Option B: Native Windows (CMD)

```cmd
cd C:\Users\Admin\Documents\CTU-automated-pdf-extraction
myvenv\Scripts\activate.bat
python extract_42nd_cmets.py
```

---

### Option C: Native Windows (PowerShell)

```powershell
cd C:\Users\Admin\Documents\CTU-automated-pdf-extraction
.\myvenv\Scripts\Activate.ps1
python extract_42nd_cmets.py
```

If you get an execution policy error: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

---

### Option D: Fresh Linux / macOS Setup

```bash
cd CTU-automated-pdf-extraction
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
python3 -c "import camelot, fitz, pandas, openpyxl; print('All imports OK')"
python3 extract_42nd_cmets.py
```

**System dependencies** (required for Camelot and Tesseract):
- Ubuntu/Debian: `sudo apt-get install -y ghostscript python3-tk tesseract-ocr`
- Fedora/RHEL: `sudo dnf install -y ghostscript python3-tkinter tesseract`
- macOS: `brew install ghostscript tcl-tk tesseract`

---

### Option E: Fresh WSL Setup (no existing venv)

```bash
sudo apt-get update
sudo apt-get install -y python3.12-venv python3-pip ghostscript python3-tk tesseract-ocr
cd /mnt/c/Users/Admin/Documents/CTU-automated-pdf-extraction
python3 -m venv .venv_wsl
source .venv_wsl/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
python3 extract_42nd_cmets.py
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

### Running Tests

```bash
# WSL (with existing Windows venv)
"/mnt/c/Users/Admin/Documents/CTU-automated-pdf-extraction/myvenv/Scripts/python.exe" tests/run_test_suite.py

# Native Windows (venv activated)
python tests\run_test_suite.py

# Linux / macOS / WSL native venv
python3 tests/run_test_suite.py
```

## Key Rules To Preserve

- Withdrawn rows must keep blank voltage.
- `42nd` Reg. 5.2 rows must keep `granted_quantum_mw == application_quantum_mw`.
- RE lookup priority: `Oct first` → `Sept fallback` → `Dec detail merge`.
- LTA-expanded rows: copy only through `CMETS GNA Approved`; later fields stay blank.
- Empty granted quantum → `0`, except intentionally partial expanded rows.
- 34th "Reduced to X MW" → use the reduced value in output fields.
- Substation normalization: strip `PS`, `Sirohi PS` → `Sirohi-I`, preserve `Sirohi-II`.
- 34th collapsed-row fallback must recover IDs `2200000793` and `2200000891`.
- Sheet name must remain `Data to be captured` (exact).
- Element Status source order: `TBCB → RTM → NCT → CMETS`.

## Documentation

| File | Read When |
|---|---|
| `update.md` | **First** — current baseline and latest changes |
| `refactor.md` | Architecture redesign history and risk notes |
| `documentation.md` | Detailed code map and module guide |
| `kt_document.md` | Full knowledge transfer for new team members |
| `AGENTS.md` | Rules for AI assistants working on this repo |

**New session reading order**: `update.md` → `refactor.md` → `README.md` → `extract_42nd_cmets.py`

Last updated: `2026-03-26`
