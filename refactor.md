# Architecture Refactor Handoff

## Purpose
- Single continuity document for the ongoing architecture redesign.
- Read this at the start of future refactor sessions to understand:
  - what has already been analyzed
  - what has already been moved
  - what has been validated
  - what is still risky or blocked
  - what the next safe slice should be

Last updated: `2026-03-25`

## Current Objective
- Decompose the large integrated extractor into a cleaner package structure.
- Preserve current behavior, CLI usage, file paths, workbook output contract, and meeting-specific edge-case handling.
- Avoid a big-bang rewrite.

## Original Prompt Rules And Guardrails
These are the standing rules from the original architecture-refactor prompt and should continue to govern future sessions.

### Non-negotiable constraints
- Do not do a careless big-bang rewrite.
- Preserve existing behavior unless a change is required for correctness.
- Maintain backward compatibility for:
  - public interfaces
  - CLI behavior
  - config behavior
  - environment-variable usage
  - input/output formats
  - API contracts
  - file paths
- Be cautious with:
  - side effects
  - initialization order
  - async/concurrency behavior
  - caching
  - logging
  - retries
  - exceptions
  - external integrations
- Validate every meaningful refactor step before proceeding.
- Prefer incremental, reviewable patches over large unsafe moves.
- Keep the code production-ready and readable.
- Do not silently remove edge-case handling.
- Avoid unnecessary abstractions and overengineering.
- The system must remain fully runnable.

### Required refactor workflow
- Phase 1: understand the current system first
- Phase 2: design the target architecture
- Phase 3: protect behavior before refactoring heavily
- Phase 4: refactor incrementally
- Phase 5: improve maintainability and quality after architecture stabilizes

### Preferred extraction order
- extract pure utility functions first
- then data models/types/schemas
- then config handling
- then external integrations/adapters
- then business rules and transformation logic
- then orchestration/pipeline coordination
- then global state / hidden dependency cleanup

### Engineering rules to preserve
- Prefer composition over inheritance.
- Prefer pure functions for transformation logic where practical.
- Keep I/O at the edges.
- Keep orchestration separate from business logic.
- Avoid circular imports.
- Avoid turning `utils.py` into a dumping ground.
- Do not create meaningless wrappers.
- Preserve performance characteristics unless a change is clearly safe and beneficial.
- Preserve logging and exception semantics unless there is a justified reason to change them.

## Current Refactor Status
- Phase 1: complete
  - current architecture assessed
- Phase 2: complete
  - target architecture proposed
- Phase 3: complete
  - characterization, regression, and smoke safety nets added
- Phase 4: complete
  - completed slices:
    - slice 1: config, PDF adapter, common helpers
    - slice 2: RE-effectiveness domain logic
    - slice 3: core deliberation parsing
    - slice 4: workbook and CSV writer adapters
    - slice 5: hybrid deliberation/context helper block
    - slice 6: Bulk Consumers domain logic
    - slice 7: Margin domain logic
    - slice 8: Element Status parser / normalization domain logic
    - slice 9: Element Status workbook adapter extraction
    - slice 10: shared data-capture common module extraction
    - slice 11: CMETS Element Status runtime/state extraction
    - slice 12: meeting module extraction (`hybrid`, `34th`, `42nd`)
    - slice 13: explicit run context + pipeline runner + root shim reduction
- Phase 5: complete
  - naming, module boundaries, docstrings, type-hint cleanup, logging-preserving cleanup, and architecture smoke coverage completed in the final pass

## Baseline Before Refactor
- Original root script size: `9524` lines
- Current root script size: `342` lines
- Runtime entrypoint remains:
  - `extract_42nd_cmets.py`
- Public/runtime behavior intentionally preserved:
  - same root script
  - same workbook template path usage
  - same source PDF folders
  - same output workbook and CSV names

## Current Target Architecture

### Package structure already introduced
- `cmets_extractor/config.py`
- `cmets_extractor/types.py`
- `cmets_extractor/adapters/csv.py`
- `cmets_extractor/adapters/pdf.py`
- `cmets_extractor/adapters/workbook.py`
- `cmets_extractor/adapters/element_status_workbook.py`
- `cmets_extractor/domain/common/text.py`
- `cmets_extractor/domain/common/ids.py`
- `cmets_extractor/domain/common/numbers.py`
- `cmets_extractor/domain/common/dates.py`
- `cmets_extractor/domain/re_effectiveness.py`
- `cmets_extractor/domain/deliberation.py`
- `cmets_extractor/domain/hybrid_context.py`
- `cmets_extractor/domain/data_capture_common.py`
- `cmets_extractor/domain/bulk_consumers.py`
- `cmets_extractor/domain/margin.py`
- `cmets_extractor/domain/element_status.py`
- `cmets_extractor/domain/element_status_runtime.py`
- `cmets_extractor/domain/meetings/__init__.py`
- `cmets_extractor/domain/meetings/hybrid.py`
- `cmets_extractor/domain/meetings/thirty_fourth.py`
- `cmets_extractor/domain/meetings/forty_second.py`
- `cmets_extractor/run_context.py`
- `cmets_extractor/pipeline.py`

### Still planned but not yet extracted
- none

## What Has Been Moved

### Slice 1: config, PDF adapter, common helpers
Moved from `extract_42nd_cmets.py` into package modules:

- `cmets_extractor/config.py`
  - hard-coded paths
  - meeting constants
  - sheet/column mappings
- `cmets_extractor/adapters/pdf.py`
  - PDF page count and Camelot chunked table-read boundary
- `cmets_extractor/domain/common/text.py`
  - text cleanup and order-preserving dedupe
- `cmets_extractor/domain/common/ids.py`
  - ID normalization helpers
- `cmets_extractor/domain/common/numbers.py`
  - numeric conversion helpers
- `cmets_extractor/domain/common/dates.py`
  - generic date parsing and SCOD/date normalization helpers

### Slice 2: RE-effectiveness rules
Moved into `cmets_extractor/domain/re_effectiveness.py`:

- RE effectiveness PDF parsing
- combined lookup building:
  - Oct first
  - Sept fallback
  - Dec detail merge
- project-type normalization
- project-type component conversion
- current-row and prior-connectivity merge logic
- LTA-to-ST-II expansion rules
- 42nd wrapper and hybrid Reg. 5.2 wrapper
- granted-quantum backfill policy

### Slice 3: deliberation parsing core
Moved into `cmets_extractor/domain/deliberation.py`:

- `extract_deliberation_text_for_pdf(...)`
- `extract_deliberation_text(...)`
- `extract_scod_date_from_deliberation(...)`
- `extract_status_from_deliberation(...)`
- `extract_voltage_from_deliberation(...)`

### Slice 4: workbook and CSV writers
Moved into adapter modules:

- `cmets_extractor/adapters/workbook.py`
  - `write_to_excel(...)`
  - `write_bulk_consumers_to_excel(...)`
  - `write_margin_to_excel(...)`
  - `prepare_data_capture_excel_value(...)`
  - `prepare_bulk_consumers_excel_value(...)`
- `cmets_extractor/adapters/csv.py`
  - `save_to_csv(...)`

### Slice 5: hybrid deliberation/context helpers
Moved into `cmets_extractor/domain/hybrid_context.py`:

- exact/inferred app-context selection helpers
- local app scoping helpers
- direct-anchor vs reference-only heuristics
- hybrid status scoring and resolution
- 35th hybrid status override helper
- 34th status/applied-signal helpers reused by hybrid logic
- battery-duration text extraction used by hybrid context selection

### Slice 6: Bulk Consumers domain logic
Moved into `cmets_extractor/domain/bulk_consumers.py`:

- GNARE table-layout/header detection helpers
- GNARE candidate-page scanning and page-range collapsing
- Bulk Consumers deliberation-context assembly
- GNARE dedicated-transmission substation parsing
- GNARE revoked/granted status resolution
- Bulk Consumers record dedupe/scoring
- `extract_bulk_consumers_from_pdf(...)`

### Slice 7: Margin domain logic
Moved into `cmets_extractor/domain/margin.py`:

- Margin state normalization helper
- pooling-station cleanup and `Complex` splitting
- parent-complex state propagation
- `Expected CoD` multiplication-pattern cleanup
- Margin table parsing / continuation tracking
- `extract_margin_data(...)`

### Slice 8: Element Status parser / normalization domain logic
Moved into `cmets_extractor/domain/element_status.py`:

- annexure parsing helpers
- CMETS ATS / DTL / CTS parsing helpers
- stable Element Status scope/code identity helpers
- TBCB / RTM source-table parsing helpers
- NCT parsing and normalization helpers
- Element Status source-row mapping helpers reused by the existing root-sheet writer
- legacy helper names re-imported through `extract_42nd_cmets.py` so the public/root surface stays intact

### Slice 9: Element Status workbook adapter extraction
Moved into `cmets_extractor/adapters/element_status_workbook.py`:

- existing-row index construction for Element Status sheet matching
- row clear/write behavior for monitoring and NCT source rows
- worksheet-level source-row update/append helper
- worksheet-level CMETS append helper
- workbook-path wrappers for:
  - TBCB population
  - RTM population
  - NCT population
  - CMETS Element Status append
- legacy helper names re-imported through `extract_42nd_cmets.py` so the root surface and call order stay intact

## What Still Lives In The Root Script
- compatibility imports for the legacy root-module API
- thin compatibility wrappers where the root surface still needs shared run-context injection:
  - CMETS Element Status cache/catalog compatibility functions
  - 34th wrappers that pass the shared run context
  - `populate_element_status_sheet_from_cmets(...)`
- legacy compatibility aliases backed by the explicit run context:
  - `ANNEXURE_ELEMENTS_CACHE`
  - `CMETS_ELEMENT_CATALOG`
- the `if __name__ == "__main__": run_pipeline(...)` entrypoint

## Final Architecture State
- orchestration now lives in `cmets_extractor/pipeline.py`
- explicit mutable run state now lives in `cmets_extractor/run_context.py`
- the remaining shared data-capture helper layer now lives in `cmets_extractor/domain/data_capture_common.py`
- the remaining CMETS Element Status cache/catalog/code-application layer now lives in `cmets_extractor/domain/element_status_runtime.py`
- meeting-specific extraction now lives in focused modules:
  - `cmets_extractor/domain/meetings/hybrid.py`
  - `cmets_extractor/domain/meetings/thirty_fourth.py`
  - `cmets_extractor/domain/meetings/forty_second.py`
- `extract_42nd_cmets.py` is now a compatibility shim rather than a business-logic file
- Element Status source ordering remains unchanged:
  - `TBCB -> RTM -> NCT -> CMETS`

## Safety Nets Added

### Test suite
- `tests/test_architecture_smoke.py`
- `tests/test_rule_characterization.py`
- `tests/test_output_regression.py`
- `tests/test_smoke.py`
- `tests/run_test_suite.py`
- `tests/_extractor_loader.py`

### Covered behavior
- reduced quantum parsing
- Sirohi/substation normalization
- SCOD last-mention behavior
- defer-vs-grant precedence
- hybrid context scoping before next-row bleed
- hybrid status resolution preferring direct exact defer context over shared grant context
- GNARE table-layout detection
- GNARE dedicated-transmission substation parsing
- GNARE explicit revoked-status handling
- Margin `Complex` pooling-station parsing
- Margin parent-state propagation
- CMETS annexure parsing with standalone numbering lines
- Element Status code stability when optional line tails are present
- NCT line-length circuit multiplication
- Element Status scheme-detail parsing
- 42nd granted-equals-applied rule
- LTA-expanded partial-row behavior
- granted-zero fill policy
- output baseline row presence
- import/export smoke checks
- pipeline/run-context/module-boundary smoke checks

### Current validation status
- latest suite result: `34` tests passed
- latest syntax smoke: passed
- latest completed full extraction: passed on `2026-03-25`
  - fresh default-output run completed successfully and was validated at `2026-03-25 13:34:44 UTC`
  - `Data to be captured = 254`
  - `Bulk Consumers = 27`
  - `Margin = 232`
  - validated fresh-output checks:
    - `2200000793` exists
    - `2200000891` exists
    - `2200000827` substation is `Sirohi-II`
    - `2200001044` keeps `50/50/50`
    - all populated 42nd Reg. 5.2 rows keep granted == applied
    - `12` partial LTA-expanded rows for `412100010` keep later columns blank
    - `Element Status` populated row count matched the validated baseline workbook:
      - `796`
- latest completion-pass runtime finding:
  - the fully extracted pipeline preserved the root runtime behavior and output contract during a fresh Windows-venv run
  - the root entrypoint is now a thin compatibility shim delegating to `cmets_extractor/pipeline.py`
  - direct sandboxed non-PTY Windows-venv script launches can still fail in this environment with:
    - `UtilBindVsockAnyPort:307: socket failed 1`
  - the reliable full-run path in this Codex/WSL session remained the documented PTY launch with cursor-position handshake

## Blocking Issues

### Current status
- There is no remaining code-level blocker for slice 9 validation.
- A full end-to-end run completed successfully for this slice and wrote validated temporary artifacts.
- In this Codex session, direct sandboxed Windows-venv invocations with script arguments still hit the WSL interop error:
  - `UtilBindVsockAnyPort:307: socket failed 1`
- The reliable validation path for this slice was an unrestricted Windows-venv execution against a temporary output workbook.

### Residual runtime caution
- Full end-to-end runs are still heavy and produce many expected Camelot warnings about image-based pages and no-table pages.
- Keep treating full extraction as a meaningful validation step for each major slice, especially before touching output-contract code or hybrid meeting logic.

## Old-To-New Responsibility Map

### Already extracted
- config/constants -> `cmets_extractor/config.py`
- PDF library boundary -> `cmets_extractor/adapters/pdf.py`
- generic text helpers -> `cmets_extractor/domain/common/text.py`
- generic ID helpers -> `cmets_extractor/domain/common/ids.py`
- generic numeric helpers -> `cmets_extractor/domain/common/numbers.py`
- generic date helpers -> `cmets_extractor/domain/common/dates.py`
- workbook writing helpers -> `cmets_extractor/adapters/workbook.py`
- CSV writing -> `cmets_extractor/adapters/csv.py`
- Element Status workbook mutation / row-write path -> `cmets_extractor/adapters/element_status_workbook.py`
- RE-effectiveness business rules -> `cmets_extractor/domain/re_effectiveness.py`
- core deliberation parsing -> `cmets_extractor/domain/deliberation.py`
- hybrid deliberation/context selection -> `cmets_extractor/domain/hybrid_context.py`
- Bulk Consumers extraction -> `cmets_extractor/domain/bulk_consumers.py`
- Margin extraction -> `cmets_extractor/domain/margin.py`
- Element Status parsing / normalization -> `cmets_extractor/domain/element_status.py`

### Not yet extracted
- meeting-specific data-capture logic -> still `extract_42nd_cmets.py`
- CMETS Element Status cache / catalog registration block -> still `extract_42nd_cmets.py`
- run orchestration -> still `extract_42nd_cmets.py`

## Refactor Completion State

### Remaining steps required for the refactor to be complete
- none

### Detailed work still remaining under each checklist item
- none

### Next-session execution order if the goal is to finish the refactor completely
- not applicable; the architecture refactor completion checklist is satisfied

### Next-session definition of done
The definition of done from the previous roadmap is now satisfied:

1. The canonical completion checklist is fully done.
2. `extract_42nd_cmets.py` is now a thin compatibility shim.
3. Meeting-specific parsing logic now lives under `cmets_extractor/domain/meetings/...`.
4. Element Status cache/catalog/code-application logic now lives in `cmets_extractor/domain/element_status_runtime.py`.
5. Hidden mutable root-script state has been replaced with `cmets_extractor/run_context.py`.
6. The pipeline runner now owns orchestration order in `cmets_extractor/pipeline.py`.
7. Phase 5 cleanup has been completed for the extracted architecture.
8. The final state was revalidated with:
   - `python3 tests/run_test_suite.py`
   - `python3 -m py_compile ...`
   - a fresh Windows-venv full extraction run with critical-row validation
9. `update.md` and `refactor.md` describe the completed state and the latest validation run.

### Current answer in one view
- The architecture refactor is complete.
- The root script is now a compatibility surface, not the implementation body.
- Business logic, runtime state, and orchestration all live under `cmets_extractor/...`.
- The pipeline still produces the validated baseline counts and critical rows.

### Ongoing maintenance expectation
- Keep using `extract_42nd_cmets.py` as the compatibility entrypoint unless there is an explicit migration decision.
- Preserve current meeting order, workbook contract, output names, and Element Status source ordering.
- Re-run the suite, syntax smoke, and a fresh extraction when future changes affect runtime behavior or output contracts.

## Resume Checklist For Future Sessions
1. Read `update.md`
2. Read this file: `refactor.md`
3. Read `README.md`
4. Read `extract_42nd_cmets.py`
5. Run:
   - `python3 tests/run_test_suite.py`
   - `python3 -m py_compile extract_42nd_cmets.py ...`
6. Treat the architecture refactor as complete unless a new redesign task is explicitly requested
7. Preserve the compatibility surface and validated output contract when making future feature or bug-fix changes
8. Update both:
   - `update.md`
   - `refactor.md`

## Rules To Preserve While Refactoring
- no big-bang rewrite
- preserve current CLI usage
- preserve current source/output file paths
- preserve print-based operator feedback for now
- preserve fallback ordering
- preserve partial-row behavior
- preserve exception semantics unless there is a correctness reason to change them
