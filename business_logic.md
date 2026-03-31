# Business Logic Reference



## 2. Cross-Cutting Parsing Rules

### IDs

- Application IDs are normalized by stripping non-digits and leading zeros.
- LTA IDs are detected by the prefix rule: IDs starting with `04` are treated as LTA IDs.
- A normalized ID must usually contain at least 7 digits to be kept.

### Dates

- Output-facing date text is normalized to `DD.MM.YYYY` where possible.
- When multiple dates appear in one field, the latest parsed date is selected.
- `gna_operationalization_yes_no` is derived at runtime:
  - `Yes` if parsed GNA operationalization date is less than or equal to the run date
  - `No` if parsed GNA operationalization date is after the run date
- This means the `Yes/No` result is time-sensitive and depends on when the extractor runs.

### Status semantics

Status resolution across the extractor uses these meanings:

- `Granted`
- `Applied`
- `Withdrawn`

Default precedence in non-hybrid deliberation parsing:

1. Defer/review/take-up-later language -> `Applied`
2. Close/withdraw language -> `Withdrawn`
3. Grant language -> `Granted`
4. Otherwise -> `Applied`
5. Revoked language -> `Revoked`  


### Region/state fallback

State/region is resolved in this order:

1. Parse explicit project-location text.
2. Use normalized substation-to-state and substation-to-region maps.
3. Default region to `NR` if no region is found.
4. Backfill state from region-level default if still missing.

## 3. Substation Normalization Rules

Substation cleanup is one of the most important compatibility layers in the project.

Core rules:

- Remove trailing `PS`, `SS`, `GSS`, and `S/S` style markers.
- Normalize roman numerals: `Ii -> II`, `Iv -> IV`, etc.
- Normalize slash variants by preferring the primary variant.
- Add `-I` to simple station names when they are otherwise unindexed.
- Reject sentence fragments and noise phrases as substations.

Documented stable mappings:

- `Sirohi PS` -> `Sirohi-I`
- `Pali PS` -> `Pali-I`
- `Sirohi (HVDC) PS (Sirohi-II)` -> `Sirohi-II`
- Roman-numbered variants such as `Sirohi-II` must be preserved.

Special parsing behavior:

- Parenthetical station names can override the outer name when they are more specific.
- `Bays at ...` is preserved in some meeting-specific contexts and stripped in others.
- Pooling-station mentions can be used as a substation fallback in 35th-style hybrid cases.

## 4. Capacity and Derived-Field Formulas

### Type/capacity parsing

The extractor attempts to parse explicit component breakups first:

- `Solar`
- `Wind`
- `Hydro`
- `BESS`

If explicit breakup labels are present, they are preferred over simpler fallback parsing.

`headline_total` rule:

- When a cell starts with a pattern like `150 MW (...)`, the `150` is stored as `_capacity_headline_total`.
- This headline total is later used in RE merge logic and hybrid reconciliation.

### Battery duration formula

If a duration is found in text such as `4 hours` or `four (4) hours`, then:

- `battery_mwh = battery_injection_mw * duration_hours`

This is skipped for pumped-storage rows.

### Pumped storage parsing

For PSP rows:

- detect pumped storage from nature/type text
- extract `Max Injection`
- extract `Max Drawl`
- write them to:
  - `psp_injection_mw`
  - `psp_drawl_mw`

If PSP values are populated, `battery_injection_mw` is cleared.

### NCT Element Status formulas

For NCT-derived Element Status rows:

- `MVA = sum(multiplier * MVA)` across all matched `n x MVA` fragments
- `Length = sum(km values) * circuit_multiplier`

Current implemented circuit multipliers:

- `double circuit` or `D/c` -> `2`
- `quad` -> `4`
- `quad` plus `double circuit` -> `2` (current implemented behavior)
- otherwise -> `1`

### Margin Expected CoD multiplication cleanup

In Margin data, patterns like `3 x 250` are converted to the numeric result:

- `3 x 250` -> `750`

## 5.  Meeting Logic

record rules:

- `application_id_enhancement_5_2_or_revision` comes from the application cell.
- Existing connectivity IDs and MW are parsed from the already-granted-connectivity cell.
- If table voltage/substation is missing, deliberation text is used as fallback.
- `application_quantum_mw` comes from the parsed connectivity quantum.
- `granted_quantum_mw` is always set equal to `application_quantum_mw`.
- This `granted == applied` rule is preserved even if the row status is `Withdrawn`.
- If status is `Withdrawn`, voltage is blanked.
- SCOD/GNA operationalization date is taken from deliberation text only for granted rows.
- When multiple SCOD mentions exist, the last SCOD mention in text order wins.

## 6. Hybrid Meeting Logic (35th, 36th, 37th, 38th, 39th, 40th, 41st, 43rd)

Hybrid meetings share one extractor but support multiple table layouts.

### Layout handling

Two major row families are extracted:

- connectivity-style rows
- Regulation 5.2 / additional-capacity rows

The extractor identifies the layout from header text rather than from fixed column positions alone.

### Context reconstruction

Hybrid meetings often need more than the raw table row. The extractor reconstructs app-local context from:

1. direct app-specific deliberation text
2. best exact app window from full-PDF text
3. inferred applicant-name context
4. preface/shared discussion context

Hybrid context selection preferences:

- direct app anchors are preferred
- reference-only contexts are penalized
- shared merged blocks can override weak exact contexts
- exact `Applied` context beats a broader shared `Granted` context when the exact text is direct and explicit

### Hybrid status rules

Hybrid status is resolved by combining:

- base deliberation status
- exact app context
- inferred/shared context

Important hybrid status rules:

- explicit defer/review language keeps status as `Applied`
- direct exact `Withdrawn` wins immediately
- direct exact `Granted` wins if it is not reference-only
- 35th has additional phrase-based overrides
- 36th has extra protections against false grants when direct local text is still applied/deferred

### Hybrid voltage/substation behavior

The extractor uses several voltage/substation sources:

- raw location cell
- 34th-style grant text parsing
- deliberation voltage parser
- substation-scoped voltage parser
- bay-level voltage parser

Important rules:

- if status is `Withdrawn`, voltage is blank
- if status is not `Granted` and the context is reference-only, voltage is blank and substation may be blank
- granted rows can pull voltage/substation from richer grant-side text even when the raw table cell is weak
- 35th uses additional pooling-station and `Bays at ...` logic
- 36th uses extra bay-voltage rescue logic

### Hybrid reduced-quantum behavior

When a quantum cell contains `Reduced to X MW`:

- some hybrid layouts preserve original requested quantum and store reduced granted quantum
- other layouts use the reduced value for both application and granted quantum

This is driven by the layout flag `preserve_original_on_reduced`.

### Hybrid Reg. 5.2 grant rule

For Regulation 5.2 rows in hybrid meetings:

- if the row is granted, `granted_quantum_mw = application_quantum_mw`

## 7. Meeting Logic



### row rules

- LTA/GNA handling depends on whether the parsed application ID starts with `04`.
- Status comes from inline 34th-style deliberation text.
- Withdrawn rows must keep blank voltage.
- Granted rows receive granted quantum if not already set.
- GNA operationalization date is taken from 34th-specific start-date text or, failing that, the latest parsed date in granted text.

### 34th reduced-quantum rule

For text like `150 (Reduced to 50 MW)`:

- default behavior: application quantum = `50`, granted quantum = `50`
- legacy preserve mode: application quantum = `150`, granted quantum = `50`

The connectivity-style 34th/hybrid layout that needs legacy preserve mode explicitly enables it.

## 8. RE-Effectiveness Rules

RE-effectiveness data comes from three PDFs merged in this priority order:

1. `Oct first`
2. `Sept fallback`
3. `Dec detail merge`

### Lookup merge rules

- Oct data is the primary source.
- Sept fills missing fields.
- Dec can add richer breakup/effective-date detail.
- ST-II IDs linked to LTA rows are carried forward when available.

### Project type normalization

The extractor normalizes RE-effectiveness types into:

- `Solar`
- `Wind`
- `Hydro`
- `BESS`
- `Hybrid`
- `Hybrid+BESS`
- `Solar+BESS`
- `Wind+BESS`
- `Hydro+BESS`
- `PSP`

### RE merge behavior

When RE data exists for a row:

- current explicit breakup is preferred over vague legacy type text
- previous connectivity component MW can be merged into current breakup
- additive same-component logic can preserve incremental additions
- hybrid headline totals can be retained where they represent the meaningful current total

### LTA -> ST-II expansion

If a record has:

- an `lta_application_id`
- no `gna_st_ii_application_id`
- linked ST-II IDs in the RE lookup

then the row is expanded into one row per linked ST-II ID.

Expansion contract:

- first expanded row stays full
- later expanded rows are partial rows marked with `_partial_row = True`
- partial rows copy only fields through `CMETS GNA Approved`
- partial rows intentionally keep later fields blank
- status and voltage are retained on partial rows

Hybrid Reg. 5.2 nuance:

- later partial rows also intentionally omit `cmets_gna_approved`

## 9. Bulk Consumers Logic

Bulk Consumers are extracted from GNARE-style tables.

### Table detection

A table is treated as a Bulk Consumers source when the header implies:

- GNA/GNARE
- applicant identity
- within-region quantum
- outside-region quantum
- total quantum

Candidate pages are first identified by page text from the first 40 pages.

### Row handling

- duplicate app IDs keep the highest-completeness record
- substation is primarily resolved from dedicated-transmission text
- fallback can use voltage/substation extraction from deliberation
- status supports an additional explicit value: `Revoked`

Revoked logic:

- phrases like `revoked`, `stands revoked`, `shall stand revoked`, or `decided to revoke` force `Revoked`

## 10. Margin Logic

Margin extraction is limited to SN9 connectivity-margin PDFs.

### Table acceptance

Only 20-column tables with SN9 margin-style headers are processed.

### Context persistence

Across continuation tables, the extractor carries forward:

- current region
- current timeline bucket
- parent complex serial number

### Complex and parent-child logic

- If pooling station text contains `Complex`, the text after `Complex` is preferred.
- Parent complex rows can receive state from child rows.
- Parent-state propagation uses the most common child state.

### Pooling-station cleanup

Pooling-station names are cleaned by removing:

- coordinates
- trailing voltage markers
- GIS/AIS suffixes
- PS/P.S./S/S style suffixes
- parenthetical noise

### Timeline rules

Timeline headers are interpreted into output values such as:

- `Existing`
- `Between ...`
- `Beyond Dec-25`

## 11. Element Status Logic

Element Status is a separate output pipeline appended after workbook creation.

### Source order

The sheet is populated in this fixed order:

1. TBCB monitoring PDF
2. RTM monitoring PDF
3. 35th NCT minutes PDF
4. CMETS-derived ATS/DTL/CTS catalog entries

### Stable code generation

Element codes are deterministic:

- normalize semantic scope text
- derive a stable identity key
- hash with MD5
- use the first 5 hex characters
- prefix with `EL-`

Formula:

- `ElementCode = "EL-" + md5(scope_identity)[:5].upper()`

Important identity rule:

- optional line tails such as `along with bus reactor` do not change the identity of the base line

### TBCB / RTM parsing

- Parent rows carry `InterIntra`, `Scheme`, and `SPV` context.
- Child rows inherit that context.
- Existing worksheet rows are updated or appended by semantic scope match.
- Existing rows are not overwritten unless the call explicitly enables overwrite.

### NCT parsing

The NCT parser uses page-coordinate text, not only generic table extraction.

NCT rules:

- hard-coded page ranges are used for the currently supported 35th NCT content
- scheme and inter/intra labels are derived from headings above the tables
- mode is inferred from remarks:
  - `RTM` if remarks mention RTM
  - `TBCB` if remarks mention TBCB
  - otherwise `NCT`
- awarded-to is inferred as `PGCIL` when remarks mention Powergrid/PGCIL

### CMETS-derived ATS/DTL/CTS rules

CMETS element codes are applied only to non-Reg. 5.2 rows.

General rules:

- non-granted rows usually have ATS/DTL/CTS codes cleared
- exception: 34th withdrawn rows may retain CTS while ATS and DTL are cleared
- annexure-derived CTS elements are cached per PDF path during a run
- all annexure CTS elements are registered into the CMETS catalog

Section mapping:

- `A.` -> ATS
- `B.` -> DTL
- `C.` -> CTS

CTS annexure rule:

- if the CTS section references annexures, annexure elements replace the inline CTS list

### CMETS fallback behavior

If direct mapping is incomplete, the runtime may:

- search inferred/shared hybrid context
- extract dedicated transmission elements from free text
- in 35th PSP cases, recover CTS by searching the 34th PDF by applicant name
- borrow richer DTL content from another app's deliberation when the current row references that app and the other row has the better DTL block

### CMETS append behavior in the workbook

When new CMETS catalog rows are appended into `Element Status`:

- columns `C` and `D` are kept blank
- columns `H` and `I` are kept blank
- meeting provenance is written in column `30` as `CMETS meeting(s): ...`

## 12. Hard-Coded Output Normalizations

The extractor contains explicit row-level fixes that are part of the current validated baseline.

### Shared carry-forward normalization

For Reg. 5.2 rows:

- if the row shares the same normalized site as an already granted connectivity row with the same linked ID
- and the Reg. 5.2 row is missing or mismatching voltage
- then voltage/substation may be carried forward from the granted connectivity row
