# CMETS NR Extractor

## Overview

This repository now uses a flattened root layout.

The active pipeline is the single integrated extractor:
- `extract_42nd_cmets.py`

It produces one workbook run covering:
- `Data to be captured`
- `Bulk Consumers`
- `Margin`
- `Element Status`

## Current Coverage

`Data to be captured` source meetings:
- `43rd`
- `42nd`
- `41st`
- `40th`
- `39th`
- `38th`
- `37th`
- `36th`
- `35th`
- `34th`

Current extraction order:
- `43rd -> 42nd -> 41st -> 40th -> 39th -> 38th -> 37th -> 36th -> 35th -> 34th`

Notes:
- `41st` is wired into the run but currently contributes `0` `Data to be captured` rows with the existing parser logic.
- `Bulk Consumers` is populated from GNARE tables across the supported CMETS PDFs.
- `Margin` is populated from the dedicated SN9 Margin PDFs.
- `Element Status` is populated from TBCB, RTM, 35th NCT, and CMETS-derived ATS/DTL/CTS elements.

## Repository Layout

- `extract_42nd_cmets.py`
  - integrated extraction pipeline
- `Data to be captured PDFs/`
  - CMETS meeting PDFs plus RE-effectiveness PDFs
- `Margin PDFs/`
  - SN9 Connectivity Margin PDFs
- `Element Status PDFs/`
  - TBCB, RTM, and 35th NCT source PDFs
- `update.md`
  - detailed handoff and session memory
- `documentation.md`
  - current architecture and validated output summary
- `Connectivity Application Data.xlsx`
  - root workbook template used to create the output workbook

## Key Rules To Preserve

- Withdrawn rows must keep blank voltage.
- `42nd` Reg. 5.2 rows must keep `granted_quantum_mw == application_quantum_mw`.
- RE lookup priority is `Oct first`, `Sept fallback`, `Dec last-resort detail fallback`.
- LTA to multi-ST-II expansion keeps the first expanded row full and later rows partial.
- Empty granted quantum is filled only for the documented cases.

## Current Outputs

- Workbook: `42nd_34th_CMETS_Extracted_Data_VoltageFix.xlsx`
- CSV: `extracted_data.csv`

Latest documented validated counts:
- `Data to be captured = 254`
- `Bulk Consumers = 27`
- `Margin = 232`

## How To Run

Preferred interpreter:

```bash
"/mnt/c/Users/Admin/Documents/CTU-automated-pdf-extraction/myvenv/Scripts/python.exe" extract_42nd_cmets.py
```

If the workbook is open in Excel, close it before rerunning the extractor.

## Working Notes

- Treat `update.md` as the source of truth for recent changes and handoff state.
- Treat `refactor.md` as the dedicated continuity file for the architecture redesign.
- Treat `documentation.md` as the concise architecture and output summary.
- After any substantial extractor change, update `update.md`.

Last updated: `2026-03-24`
