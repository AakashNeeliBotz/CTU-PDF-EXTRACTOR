# CMETS Extractor Codebase Guide

## Purpose

This repository contains the production CMETS extraction pipeline.

One run produces:
- `Data to be captured`
- `Bulk Consumers`
- `Margin`
- `Element Status`
- `extracted_data.csv`

The public entrypoint is still:
- `extract_42nd_cmets.py`

That root file is now a compatibility shim. New business logic should go into the `cmets_extractor/` package, not back into the root script.

## Run The Extractor

Preferred command:

```bash
"/mnt/c/Users/Admin/Documents/CTU-automated-pdf-extraction/myvenv/Scripts/python.exe" extract_42nd_cmets.py
```

Operational notes:
- In this WSL/Codex setup, the Windows venv may emit `ESC[6n` in a PTY. Reply with `ESC[1;1R` and keep the session alive.
- If the main workbook is open in Excel, the pipeline will fall back to a timestamped temporary workbook instead of failing the whole run.

## Architecture At A Glance

The runtime split is:

1. `extract_42nd_cmets.py`
   - compatibility entrypoint
   - legacy imports/re-exports
   - creates the shared run context
   - calls `cmets_extractor.pipeline.run_pipeline()`
2. `cmets_extractor/pipeline.py`
   - top-level orchestration
   - fixed meeting order
   - output writing order
   - workbook-lock fallback behavior
3. `cmets_extractor/run_context.py`
   - explicit run-scoped mutable state
   - replaces hidden globals for CMETS element caches/catalogs
4. `cmets_extractor/domain/`
   - business rules and parsing logic
5. `cmets_extractor/adapters/`
   - PDF/workbook/CSV I/O

The high-level dependency rule is:
- `pipeline` orchestrates
- `domain` decides
- `adapters` perform I/O

## End-To-End Data Flow

`cmets_extractor/pipeline.py` runs the extractor in this validated order:

1. Build the RE-effectiveness lookup.
2. Extract `Data to be captured` records in fixed meeting order:
   - `43rd -> 42nd -> 41st -> 40th -> 39th -> 38th -> 37th -> 36th -> 35th -> 34th`
3. Apply meeting-specific RE rules.
4. Apply CMETS ATS/DTL/CTS code mapping where that meeting flow uses it.
5. Combine all `Data to be captured` records.
6. Apply shared output normalizations and empty-granted backfill rules.
7. Extract `Bulk Consumers`.
8. Extract `Margin`.
9. Write workbook sheets:
   - `Data to be captured`
   - `Bulk Consumers`
   - `Margin`
10. Populate `Element Status` in fixed source order:
   - `TBCB -> RTM -> NCT -> CMETS`
11. Write `extracted_data.csv`.

## Code Map

### Root

- `extract_42nd_cmets.py`
  - Keep this thin.
  - Safe changes here are limited to compatibility imports, wrappers, and CLI entry behavior.

### Shared Runtime

- `cmets_extractor/run_context.py`
  - Defines `ExtractionRunContext`.
  - Holds run-scoped mutable caches:
    - annexure element lookup cache
    - CMETS element catalog

- `cmets_extractor/pipeline.py`
  - Owns the full run order.
  - Owns output fallback behavior when the workbook is locked.
  - Best place to change orchestration, not parsing rules.

### Config And Types

- `cmets_extractor/config.py`
  - Paths, meeting constants, sheet names, column mappings, output names.
  - Change this for path/configuration constants, not business logic.

- `cmets_extractor/types.py`
  - TypedDict shapes for:
    - data-capture records
    - bulk-consumer records
    - margin records
    - element-status source rows

### Adapters

- `cmets_extractor/adapters/pdf.py`
  - Camelot/PDF read boundaries and page-count helpers.

- `cmets_extractor/adapters/workbook.py`
  - Writes `Data to be captured`, `Bulk Consumers`, and `Margin`.
  - Handles workbook template loading and Excel value preparation.

- `cmets_extractor/adapters/csv.py`
  - Writes `extracted_data.csv`.

- `cmets_extractor/adapters/element_status_workbook.py`
  - Workbook mutation logic for `Element Status`.
  - Preserves source ordering and row update/append behavior.

### Domain: Shared Helpers

- `cmets_extractor/domain/common/text.py`
  - generic text cleanup and dedupe helpers

- `cmets_extractor/domain/common/ids.py`
  - application ID normalization helpers

- `cmets_extractor/domain/common/numbers.py`
  - numeric parsing helpers

- `cmets_extractor/domain/common/dates.py`
  - generic date parsing and SCOD/date normalization helpers

### Domain: Data Capture Rules

- `cmets_extractor/domain/deliberation.py`
  - Extracts deliberation text from PDFs.
  - Resolves SCOD, status, and voltage from deliberation text.

- `cmets_extractor/domain/re_effectiveness.py`
  - Builds the RE-effectiveness lookup.
  - Applies RE merging, hybrid breakup, and LTA/ST-II expansion rules.

- `cmets_extractor/domain/data_capture_common.py`
  - Shared normalization and parsing used across meeting flows.
  - Substation/state/voltage/capacity parsing lives here.
  - Shared output normalizations live here.

- `cmets_extractor/domain/hybrid_context.py`
  - Context selection heuristics for hybrid meetings.
  - Use this when a hybrid row is getting the wrong local decision context.

### Domain: Meeting Extractors

- `cmets_extractor/domain/meetings/forty_second.py`
  - Dedicated 42nd meeting extractor.
  - Use for 42nd-only layout or rule changes.

- `cmets_extractor/domain/meetings/thirty_fourth.py`
  - Dedicated 34th meeting extractor.
  - Owns the 34th transition/connectivity flows and collapsed-row recovery.

- `cmets_extractor/domain/meetings/hybrid.py`
  - Shared extractor for the hybrid-style meetings:
    - `43rd`
    - `41st`
    - `40th`
    - `39th`
    - `38th`
    - `37th`
    - `36th`
    - `35th`
  - Use this for table-layout detection, hybrid connectivity parsing, and hybrid Reg. 5.2 parsing.

### Domain: Other Outputs

- `cmets_extractor/domain/bulk_consumers.py`
  - GNARE/Bulk Consumers parsing and context resolution.

- `cmets_extractor/domain/margin.py`
  - Margin parsing and normalization.

- `cmets_extractor/domain/element_status.py`
  - Pure Element Status parsing/normalization logic.
  - Includes TBCB/RTM table parsing, NCT parsing, and CMETS element text parsing.

- `cmets_extractor/domain/element_status_runtime.py`
  - Run-context-backed CMETS element lookup/catalog behavior.
  - Use this when debugging ATS/DTL/CTS registration, annexure caches, or code assignment.

## Where To Change Things

Use this as the shortest navigation guide:

- Change meeting order or output order:
  - `cmets_extractor/pipeline.py`

- Change paths, file names, sheet names, or constants:
  - `cmets_extractor/config.py`

- Change a 42nd-only parsing rule:
  - `cmets_extractor/domain/meetings/forty_second.py`

- Change a 34th-only parsing rule:
  - `cmets_extractor/domain/meetings/thirty_fourth.py`

- Change a shared hybrid-meeting rule:
  - `cmets_extractor/domain/meetings/hybrid.py`
  - `cmets_extractor/domain/hybrid_context.py`

- Change RE lookup or ST-II/LTA expansion behavior:
  - `cmets_extractor/domain/re_effectiveness.py`

- Change shared substation, voltage, capacity, or normalization behavior:
  - `cmets_extractor/domain/data_capture_common.py`

- Change `Bulk Consumers` parsing:
  - `cmets_extractor/domain/bulk_consumers.py`

- Change `Margin` parsing:
  - `cmets_extractor/domain/margin.py`

- Change Element Status parsing rules:
  - `cmets_extractor/domain/element_status.py`

- Change Element Status workbook write/update behavior:
  - `cmets_extractor/adapters/element_status_workbook.py`

- Change CMETS ATS/DTL/CTS cache/catalog behavior:
  - `cmets_extractor/domain/element_status_runtime.py`

- Change workbook writing for `Data to be captured`, `Bulk Consumers`, or `Margin`:
  - `cmets_extractor/adapters/workbook.py`

## Stable Invariants

These rules are part of the current validated behavior and should not be changed casually:

- Keep `extract_42nd_cmets.py` as the compatibility entrypoint.
- Preserve current meeting order and output order.
- Preserve Element Status source ordering:
  - `TBCB -> RTM -> NCT -> CMETS`
- Sheet name `Data to be captured` must remain unchanged.
- `42nd` Reg. 5.2 rows must keep `granted_quantum_mw == application_quantum_mw`.
- Empty granted quantum should become `0`, except intentionally partial expanded rows.
- Withdrawn rows must keep blank voltage.
- 42nd SCOD parsing should use the last SCOD mention in text order.
- RE lookup priority remains:
  - `Oct first`
  - `Sept fallback`
  - `Dec detail merge`
- Expanded LTA rows should copy only through `CMETS GNA Approved`; later fields stay blank.
- 34th reduced-quantum text like `Reduced to X MW` should use the reduced value in output fields.
- Substation normalization rules around `PS`, `Sirohi`, and `Sirohi-II` must remain intact.
- 34th collapsed-row fallback must keep recovering skipped IDs such as `2200000793` and `2200000891`.

## Tests And Validation

The repo has four useful test layers:

- `tests/test_smoke.py`
  - root-surface and import-level stability

- `tests/test_rule_characterization.py`
  - business-rule regression checks for known edge cases

- `tests/test_output_regression.py`
  - checks the committed baseline output artifacts for critical known-good rows

- `tests/test_architecture_smoke.py`
  - pipeline/run-context/module-boundary sanity checks

Run the suite with:

```bash
python3 tests/run_test_suite.py
```

For syntax-only verification of touched modules:

```bash
python3 -m py_compile extract_42nd_cmets.py
```

You can extend that command with any touched package modules.

## Current Baseline

Latest validated full-run counts:

- `Data to be captured = 254`
- `Bulk Consumers = 27`
- `Margin = 232`
- `Element Status populated rows = 796`

Critical spot checks from the validated baseline:

- `2200000793` exists
- `2200000891` exists
- `2200000827` substation is `Sirohi-II`
- `2200001044` remains `50/50/50`
- populated 42nd Reg. 5.2 rows keep `granted == applied`
- partial `412100010` rows keep later fields blank

## Practical Editing Rules

- Add new logic to package modules, not the root compatibility script.
- Keep parsing logic in `domain/`.
- Keep file and workbook side effects in `adapters/`.
- Keep run-order changes in `pipeline.py`.
- If a change needs run-scoped mutable state, add it to `ExtractionRunContext` instead of adding a hidden module global.

Last updated: `2026-03-25`
