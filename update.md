# 42nd/34th CMETS Extractor - Current Continuity Notes

## Why this file exists

This is the short continuity file for future sessions.

It intentionally replaces the older long-form session log. The goal now is:
- keep only the current baseline
- keep only the latest important completed change
- make it easy to append fresh updates from here

Last updated: `2026-03-27`

## Current Baseline

- Runtime entrypoint:
  - `extract_42nd_cmets.py`
- Architecture status:
  - refactor complete
  - root script is now a thin compatibility shim
  - orchestration lives in `cmets_extractor/pipeline.py`
  - shared mutable run state lives in `cmets_extractor/run_context.py`
- Primary outputs:
  - workbook: `42nd_34th_CMETS_Extracted_Data_VoltageFix.xlsx`
  - csv: `extracted_data.csv`
- Current validated output counts:
  - `Data to be captured = 254`
  - `Bulk Consumers = 27`
  - `Margin = 232`
  - `Element Status populated rows = 796`

## Critical Rules To Preserve

1. `Data to be captured` sheet name must not change.
2. Preserve current meeting order and output order.
3. Preserve Element Status source ordering:
   - `TBCB -> RTM -> NCT -> CMETS`
4. Withdrawn rows must keep blank voltage.
5. 42nd SCOD parsing must use the last SCOD mention in text order.
6. 42nd Reg. 5.2 rows must keep `granted_quantum_mw == application_quantum_mw`.
7. Empty granted quantum should become `0`, except intentionally partial expanded rows.
8. Expanded LTA rows should copy only through `CMETS GNA Approved`; later fields stay blank.
9. RE lookup priority remains:
   - `Oct first`
   - `Sept fallback`
   - `Dec detail merge`
10. 34th reduced-quantum text like `Reduced to X MW` should use the reduced value in output fields.
11. Substation normalization rules around `PS`, `Sirohi-I`, and `Sirohi-II` must stay stable.
12. 34th collapsed-row fallback must keep recovering skipped IDs such as `2200000793` and `2200000891`.

## Latest Major Completed Change

### 2026-03-30: Extended main pipeline coverage from 43rd down to 14th

Requirement:
- Make the main `extract_42nd_cmets.py` pipeline capable of processing the newly added `33rd` through `14th` CMETS PDFs, while keeping the existing `43rd` through `34th` behavior stable.

Root cause:
- The production pipeline only knew about `43rd` through `34th`.
- Older meetings use multiple legacy layouts that were not represented in config/pipeline orchestration.
- Large scan-heavy PDFs could stall or crash Camelot on wide lattice page ranges.
- Older hybrid-family meetings were still attempting Reg. `5.2` scans that do not yield records for those layouts and made runs unnecessarily fragile.

Changed files/modules:
- `cmets_extractor/config.py`
- `cmets_extractor/pipeline.py`
- `cmets_extractor/adapters/pdf.py`
- `cmets_extractor/domain/meetings/hybrid.py`
- `cmets_extractor/domain/meetings/legacy_transition.py`
- `cmets_extractor/domain/meetings/legacy_stage.py`
- `cmets_extractor/domain/meetings/__init__.py`
- `cmets_extractor/domain/bulk_consumers.py`

Run command:
- `"/mnt/c/Users/Admin/Documents/CTU-automated-pdf-extraction/myvenv/Scripts/python.exe" extract_42nd_cmets.py`

Output file:
- workbook: `42nd_34th_CMETS_Extracted_Data_VoltageFix.xlsx`
- csv: `extracted_data.csv`

Verification result:
- `python3 -m py_compile` passed on the root entrypoint and touched extractor modules.
- Targeted extractor smokes passed:
  - `24th = 1`
  - `18th = 10`
  - legacy Bulk Consumers: `14th = 1`, `17th = 1`
- Earlier extractor characterization/smoke work in this workspace also confirmed:
  - `33rd = 76`
  - `26th = 19`
  - `25th = 10`
  - `23rd = 7`
  - `22nd = 60`
  - `21st = 12`
  - `19th = 8`
  - `14th = 27`
- Full end-to-end `extract_42nd_cmets.py` execution was intentionally not re-run to completion in this turn because the user requested to run the full pipeline locally.

Caveats:
- For older hybrid-family meetings, legacy Reg. `5.2` scans are now skipped where they were only producing `0` records and slowing the run.
- Large scan-heavy PDFs now reduce Camelot lattice chunk size automatically for stability.
- `Stage-I` application IDs from the old stage-family tables are mapped into the `lta_application_id` output column per requirement.
- Current targeted extraction behavior for `28th`, `29th`, `30th`, and `32nd` is a clean `0`-record result rather than a crash.

### 2026-03-27: Added consolidated business-logic reference document

Requirement:
- Create one repo document listing the implemented formulas, extraction rules, niche edge cases, and literal output overrides.

Changed files/modules:
- `business_logic.md`
- `README.md`
- `update.md`

Run command:
- `python3 tests/run_test_suite.py`

Output file:
- `business_logic.md`

Verification result:
- test suite passed (`34` tests)

Caveats:
- The document reflects current implemented behavior, including hard-coded row-level corrections in `cmets_extractor/domain/data_capture_common.py` and `cmets_extractor/domain/re_effectiveness.py`.

### 2026-03-25: Architecture refactor completed

What changed:
- `extract_42nd_cmets.py` was reduced to a compatibility shim.
- Top-level orchestration moved to `cmets_extractor/pipeline.py`.
- Hidden mutable globals were replaced with `ExtractionRunContext` in `cmets_extractor/run_context.py`.
- Remaining meeting flows were extracted into:
  - `cmets_extractor/domain/meetings/hybrid.py`
  - `cmets_extractor/domain/meetings/thirty_fourth.py`
  - `cmets_extractor/domain/meetings/forty_second.py`
- Remaining CMETS Element Status runtime/cache logic moved to:
  - `cmets_extractor/domain/element_status_runtime.py`
- Shared data-capture normalization/parsing moved to:
  - `cmets_extractor/domain/data_capture_common.py`

Validation completed for that change:
- `python3 tests/run_test_suite.py`
  - passed
- `python3 -m py_compile` on touched modules
  - passed
- fresh full extraction with the Windows venv entrypoint
  - passed
- validated output checks remained aligned:
  - `2200000793` exists
  - `2200000891` exists
  - `2200000827` substation is `Sirohi-II`
  - `2200001044` remains `50/50/50`
  - populated 42nd Reg. 5.2 rows keep `granted == applied`
  - partial `412100010` rows keep later fields blank

## Operational Notes

Preferred run command:

```bash
"/mnt/c/Users/Admin/Documents/CTU-automated-pdf-extraction/myvenv/Scripts/python.exe" extract_42nd_cmets.py
```

Environment notes:
- In Codex/WSL, a PTY run may emit `ESC[6n`; reply with `ESC[1;1R` and keep the session alive.
- Do not treat the known sandboxed Windows-venv interop failure as a pipeline regression.
- If the workbook is open in Excel, the pipeline may write to a timestamped temporary workbook instead.

## Where To Look First

Read in this order:
1. `update.md`
2. `refactor.md`
3. `README.md`
4. `extract_42nd_cmets.py`

For architecture navigation after that:
- `documentation.md`

## How To Append Future Updates

Add new entries above this section and keep them short:
- date
- requirement
- changed files/modules
- run command
- output file
- verification result
- caveats

Older detailed historical entries were intentionally removed when this file was condensed on `2026-03-25`.
