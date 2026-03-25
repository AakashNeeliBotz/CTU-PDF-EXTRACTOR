# AGENTS.md - CTU Automated PDF Extraction Workspace Guide

## Scope
These instructions apply to this repository.

## First-read order for future sessions
1. `update.md`
2. `refactor.md`
3. `README.md`
4. `extract_42nd_cmets.py`

Do not start implementation before reviewing these files.

For architecture-refactor sessions, `refactor.md` is the primary continuity file for what has already been moved, what is validated, and what remains risky.

## Repo layout note
- The repository was flattened on `2026-03-24`.
- Historical notes inside `update.md` may still reference `42nd-cmets-sheet/...`; treat those as root-relative paths now.

## Environment and venv policy

### Preferred runtime (recommended)
Use the existing Windows venv from WSL for this project:
- Interpreter: `/mnt/c/Users/Admin/Documents/CTU-automated-pdf-extraction/myvenv/Scripts/python.exe`

Reason:
- This environment already has Camelot/PyMuPDF/OpenPyXL and project dependencies working in this workspace.

### Typical run command
From repo root:
```bash
"/mnt/c/Users/Admin/Documents/CTU-automated-pdf-extraction/myvenv/Scripts/python.exe" extract_42nd_cmets.py
```

### Codex runtime note
When running the Windows venv from the Codex terminal:
- Prefer a live PTY / interactive run for the full extractor.
- If the first visible output is the terminal cursor-position query `ESC[6n`, do **not** assume the pipeline is hung.
- Reply with the cursor-position report `ESC[1;1R` and keep the same session alive; after that, the extractor should continue normally.
- Do not treat plain non-PTY or redirected Windows-venv launch failures as extractor failures in this workspace. In this WSL session they can fail early with:
  - `UtilBindVsockAnyPort:307: socket failed 1`
- Only diagnose a real pipeline stall after the PTY handshake above has been satisfied and the run still stops making progress.

### If you must use a WSL venv
If WSL Python environment is missing `venv`/`pip`:
1. Install system packages (requires privilege):
```bash
apt-get update
apt-get install -y python3.12-venv python3-pip
```
2. Create venv:
```bash
python3 -m venv .venv_wsl
```
3. Activate and install dependencies:
```bash
source .venv_wsl/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

## Dependency install policy
- Primary dependency source: root `requirements.txt`.
- Do not install ad-hoc packages unless required and documented in `update.md`.
- After dependency changes, verify imports:
```bash
python -c "import camelot, fitz, pandas, openpyxl"
```

## 42nd/34th CMETS extraction rules to preserve
- Sheet name must remain `Data to be captured`.
- 42nd (Reg. 5.2): `granted_quantum_mw == application_quantum_mw` regardless of status.
- Empty granted quantum should be written as `0` (except intentionally partial expanded rows).
- Withdrawn rows must have blank voltage.
- SCOD parsing for 42nd should take the last SCOD mention in text order.
- RE effectiveness lookup: Oct PDF first, Sept fallback.
- LTA-expanded rows (missing ST-II originally): copy only fields up to `CMETS GNA Approved`; leave rest blank.
- 34th reduced quantum pattern `Reduced to X MW`: use reduced value in application/granted/type capacity.
- Substation normalization:
  - Remove trailing `PS`.
  - `Sirohi PS` -> `Sirohi-I`.
  - Keep roman variants (`Sirohi-II`, etc.).
  - Preserve special extraction for `Sirohi (HVDC) PS (Sirohi-II)` -> `Sirohi-II`.
- 34th collapsed-row fallback must recover skipped IDs like `2200000793`, `2200000891`.

## Validation checklist after code changes
Run full extraction and confirm at least:
1. `2200000793` and `2200000891` exist in output.
2. `2200000827` substation is `Sirohi-II`.
3. `2200001044` has application/granted/solar all `50`.
4. 42nd rows satisfy granted==applied.
5. Expanded LTA rows have blank columns after `CMETS GNA Approved`.

## Output file handling
- Default output can fail with `PermissionError` if open in Excel.
- If locked, close the workbook and rerun.
- For validation runs, use a temporary output name and report it clearly.

## Documentation hygiene
Every substantial change must update `update.md` with:
- date
- requirement
- root cause
- changed code areas
- run command
- output file
- verification result
- caveats
