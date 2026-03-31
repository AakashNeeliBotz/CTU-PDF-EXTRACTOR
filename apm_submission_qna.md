Aakash Neeli: # Project Submission Questionnaire - Answered from Current Repo Understanding

Generated on: 2026-03-05  
Source basis: `documentation.md`, `update.md`, `extract_42nd_cmets.py`, `requirements.txt`.

Note:
- Answers are limited to what is currently visible in this codebase.
- Where evidence is missing, answer is marked `Not documented` or `NA`.
- For checklist slides, responses are given in `Yes / No / NA` format as requested.

## SLIDE 1 - COVER PAGE

- Date of Submission: `2026-03-05`
- Project Title: `CTU Automated PDF Data Extraction and Consolidation (42nd/34th/39th/38th/37th/36th CMETS + Margin + Element Status)`
- BU / Function: `Power Transmission / ISTS Connectivity data processing (inferred from project content)`
- CIO / CDO Name: `Not available in repository`
- Project Lead / IT Owner: `Not available in repository`
- Business Sponsor / Functional Owner: `Not available in repository`

---

## SLIDES 2-3 - PRE-SUBMISSION CHECKLIST (Yes / No / NA)

| # | Question | Answer | Repo-based note |
|---|---|---|---|
| 1 | Checked in APM that no existing solution can be leveraged? | NA | APM evidence not present in repo. |
| 2 | BRD available and signed off by BU stakeholders/owners? | No | No BRD/sign-off document found. |
| 3 | Business needs categorized into must-have and good-to-have? | No | Priorities appear in changelog but no formal categorization document. |
| 4 | Functional evaluation completed against BRD and rankings established? | No | No formal BRD-evaluation matrix found. |
| 5 | Partner responses to Technology questionnaire attached? | NA | No external partner questionnaire in repo. |
| 6 | CIA (Confidentiality-Integrity-Availability) aspects captured? | No | No formal CIA worksheet found. |
| 7 | As-is architecture provided? | Yes | Textual current-state flow exists in `documentation.md`/`update.md`. |
| 8 | BU landscape diagram provided? | No | No BU landscape diagram file found. |
| 9 | Logical architecture provided? | Yes | Logical flow is documented textually in docs and code. |
| 10 | End-to-end integration architecture provided? | Yes | End-to-end extraction flow is defined in integrated pipeline. |
| 11 | Cyber Security Architecture available? | No | No dedicated cybersecurity architecture document found. |
| 12 | Data Flow Architecture provided? | Yes | Data flow is inferable from documented run flow and code pipeline. |
| 13 | Privacy Impact Assessment available? | No | No PIA document found. |
| 14 | Deployment architecture provided (network zoning/segmentation)? | No | No deployment network-zoning design found. |
| 15 | Data Security controls in place (encryption, tokenization, masking)? | No | No explicit controls documented in this repo. |
| 16 | Legal and Regulatory compliance controls in place? | No | Not documented in repository artifacts. |
| 17 | Application profile details added (user base, deployment model, interfaces)? | No | No formal application profile sheet found. |
| 18 | Integration details provided (API, interconnects, communication medium)? | No | No formal integration catalog; mostly file-based local processing. |
| 19 | Non-Functional Requirements captured (uptime, RPO/RTO, scalability, etc.)? | No | NFR spec sheet not found. |
| 20 | High-level TCO for at least 3 years provided and within budget? | No | No TCO/budget worksheet found. |
| 21 | Technical evaluation completed against NFRs and rankings established? | No | No formal technical scoring file found. |

---

## SLIDE 4 - PARTNER SELECTION CHECKLIST (Yes / No / NA)

| # | Question | Answer | Repo-based note |
|---|---|---|---|
| 1 | OEM/Service Provider turnover >= INR 200 Cr avg over last 3 financial years? | NA | No OEM/bidder profile in repo. |
| 2 | Bidder has minimum 200 full-time rostered manpower? | NA | Bidder details not present. |
| 3 | Security certifications available (HIPAA, GDPR, ISO27001, SOC2 Type2)? | No | No partner certification evidence in repo. |
| 4 | VA and PT reports available for complete solution stack? | No | No VA/PT reports found. |
| 5 | Solution deployed >=1 year for an org with 10+ sites / 15k users? | NA | No partner deployment references found. |
| 6 | Partner shared Cyber Security Policy? | No | Not available in repo. |
| 7 | Partner shared ISO20k certification and ITSM processes? | No | Not available in repo. |
| 8 | All third-party/open-source software dependencies documented? | Yes | Dependencies listed in `requirements.txt`. |
| 9 | Partner agreed to penalty clauses for security breaches? | NA | No partner contract artifact found. |
| 10 | Partner has stated disclosure process for security breaches with escalation matrix? | No | No such partner process document in repo. |

---

## SLIDE 5 - VENDOR CREDENTIALS EVALUATION

- Vendor/Option Name: `Internal in-house Python extraction pipeline (no external vendor profile in repository)`
- 1. Company size (revenue and headcount): `NA - not documented in repo`
- 2. Office details - HQ address: `NA`
  - Development/support center addresses: `NA`
- 3. Global customer base size + top customer names: `NA`
- 4. India customer base size + top customer names: `NA`
- 5. Product strategy and roadmap (brief description):
  - `Current roadmap in docs: generalize parser for additional CMETS meetings and reduce hard-coded meeting assumptions.`
- 6. Partner ecosystem (key technology partners):
  - `Open-source stack: Camelot, PyMuPDF, pdfplumber, pandas, openpyxl, opencv, pytesseract (via requirements).`
- 7. Presence in Adani Group (which entities): `Not documented in repository`
- 8. Reference customer name(s) checked: `NA`
- 9. Turnover in last financial year: `NA`
- 10. Previous deployments of equal/larger scale (mention user base size): `NA (no deployment references in repo)`

---

## SLIDE 7 - AT A GLANCE / EXECUTIVE SUMMARY

- Overall Business Need (2-3 lines):
  - `Automate extraction of CMETS/RE-effectiveness/monitoring PDF data into a standardized workbook and CSV.`
  - `Reduce manual effort, improve consistency in status/quantum/voltage/substation fields, and preserve repeatable business rules.`
- Recommended Solution Approach (4-6 bullet points):
  - `Use one integrated Python extractor (`extract_42nd_cmets.py`) for all required sheets.`
  - `Continue folderized input management for Data/Margin/Element Status PDFs.`
  - `Keep deterministic parser rules for known CMETS layouts and track all changes in update log.`
  - `Run full pipeline to generate workbook + CSV in one command.`
  - `Add regression validation for anchor application IDs after each rule change.`
- Solution Option 1 (name or NA): `Manual extraction and workbook updates`
- Solution Option 2 (name or NA): `Semi-automated meeting-wise scripts`
- Solution Option 3 - Recommended (name): `Integrated multi-meeting extractor (current root-level pipeline)`

---

## SLIDE 8 - IMPACT TO BUSINESS CAPABILITIES

- Capability 1 - Regulatory data preparation and reporting | Impact: High | `Automates extraction for CMETS-derived data fields required for tracking and review.`
- Capability 2 - Data quality and consistency | Impact: High | `Central rule engine applies normalization and repeatable logic across meetings.`
- Capability 3 - Operational productivity | Impact: High | `Replaces repetitive manual parsing from PDFs to workbook.`
- Capability 4 - Traceability and auditability | Impact: Medium | `Detailed `update.md` logs rule changes and validation outcomes.`
- Capability 5 - Decision support readiness | Impact: Medium | `Produces consolidated `Data to be captured`, `Margin`, and `Element Status` outputs.`
- Capability 6 - Knowledge continuity | Impact: Medium | `Runbook + changelog-based handoff lowers dependency on individual analysts.`

---

## SLIDE 9 - BUSINESS NEEDS / REQUIREMENTS

| Req # | Priority | Requirement | Must-Have / Nice-to-Have |
|---|---|---|---|
| 1 | P1 | Extract `Data to be captured` from 42nd/34th/39th/38th/37th/36th PDFs in a single run. | Must-Have |
| 2 | P1 | Preserve critical business rules (withdrawn voltage blank, 42nd Reg 5.2 granted=applied, etc.). | Must-Have |
| 3 | P1 | Populate `Margin` sheet from dedicated SN9 Margin PDFs with legacy-compatible logic. | Must-Have |
| 4 | P1 | Populate `Element Status` from TBCB and RTM monitoring PDFs. | Must-Have |
| 5 | P1 | Generate both Excel workbook and CSV output in one execution. | Must-Have |
| 6 | P2 | Extract and map CMETS ATS/DTL/CTS element codes and append to `Element Status`. | Must-Have |
| 7 | P2 | Keep input PDFs organized by purpose-specific folders. | Must-Have |
| 8 | P2 | Maintain change history and validation evidence in `update.md`. | Must-Have |
| 9 | P3 | Reduce row/app-specific normalizations by improving generic parsers. | Nice-to-Have |
| 10 | P3 | Generalize meeting discovery for future CMETS PDFs with minimal code edits. | Nice-to-Have |

---

## SLIDE 10 - APPLICATION PROFILE

- Application Category (tick all that apply):
  - [ ] Web Application
  - [ ] Thick Client (desktop)
  - [ ] Mobile Application
  - [x] Analytics

- Deployment vs. Development Type (tick one cell):

|         | SaaS | PaaS | IaaS | On-Premise |
|---|---|---|---|---|
| Custom | [ ] | [ ] | [ ] | [x] |
| COTS   | [ ] | [ ] | [ ] | [ ] |

- Integration Category (tick all that apply):
  - [ ] Integration with SAP
  - [x] Integration with non-SAP Systems (file-based PDF/Excel ingestion and output)
  - [ ] OT Integration
  - [ ] ADFS / IDM / IAM / PIM / PAM

- User Category (tick all that apply):
  - [ ] External Users
  - [x] Internal Users
  - [ ] Available Over Internet

- Architecture (tick one):
  - [x] Monolithic
  - [ ] Micro-Services

---

## SLIDE 11 - INTEGRATION / INTERCONNECTS DETAILS

### Integration 1
- Interfacing Application: `CMETS PDF source folders (Data to be captured PDFs)`
- Auth/Authorization/Accounting method: `OS file access controls (no app-level AAA implemented)`
- Type of Data Exchanged: `PDF tables and deliberation text`
- Direction: `Inbound`
- Mode: `Batch / On-Demand`
- Interface Method: `File-based ingestion (Camelot + PyMuPDF/pdfplumber)`
- Deployment Type: `On-Prem to On-Prem`
- Integration Middleware: `Point-to-Point (script-driven)`
- Handshaking Mechanism: `File path availability / read access`
- Interface Monitoring and Error Handling: `Yes (runtime logs and exceptions)`

### Integration 2
- Interfacing Application: `SN9 Margin PDFs`
- Auth/Authorization/Accounting method: `OS file access controls`
- Type of Data Exchanged: `Margin table data`
- Direction: `Inbound`
- Mode: `Batch / On-Demand`
- Interface Method: `File-based ingestion`
- Deployment Type: `On-Prem to On-Prem`
- Integration Middleware: `Point-to-Point`
- Handshaking Mechanism: `File path availability / read access`
- Interface Monitoring and Error Handling: `Yes`

### Integration 3
- Interfacing Application: `Output workbook and CSV consumers`
- Auth/Authorization/Accounting method: `OS file access controls`
- Type of Data Exchanged: `Structured Excel/CSV records`
- Direction: `Outbound`
- Mode: `Batch`
- Interface Method: `File write (XLSX/CSV)`
- Deployment Type: `On-Prem to On-Prem`
- Integration Middleware: `Point-to-Point`
- Handshaking Mechanism: `File lock and path checks`
- Interface Monitoring and Error Handling: `Yes`

---

## SLIDE 12 - TECHNOLOGY STACK

1. Web Server and Underlying OS: `NA (no web server in current solution)`
2. Application Server and Underlying OS: `Python runtime on Windows venv (used from WSL); local execution model`
3. Container Registry: `NA`
4. Database Platform and Underlying OS (name + version): `NA (no database; file-based XLSX/CSV outputs)`
5. Development Technology:
   - Frontend: `NA`
   - Backend: `Python`
   - ORM / Middleware: `NA (no ORM; parser libraries used directly)`
6. Compatible Browsers (include aNet): `NA`
7. OS Compatibility: `Windows (primary runtime), WSL/Linux for code operations`
8. Security Components (SSO, MFA, RBAC, TLS, etc.): `No dedicated app-level SSO/MFA/RBAC implemented in current script`
9. Other components not captured above:
   - `camelot-py[cv]`
   - `PyMuPDF (fitz)`
   - `pdfplumber`
   - `pandas`
   - `openpyxl`
   - `opencv-python`
   - `pytesseract`

---

## SLIDE 13 - AS-IS ARCHITECTURE (Current State)

- Current Input Sources (what data/systems exist today):
  - `CMETS meeting PDFs (42/34/39/38/37/36)`
  - `RE-effectiveness PDFs (Dec/Oct/Sept)`
  - `SN9 Margin PDFs`
  - `TBCB and RTM monitoring PDFs`
- Current Data Processing approach (how is data processed now):
  - `Single Python script parses tables + text, applies business rules, merges RE context, and performs normalization.`
- Current Storage mechanism (where is data stored today):
  - `In-memory record dictionaries during runtime, then output to XLSX + CSV files.`
- Current Output/Reporting method:
  - `Workbook: 42nd_34th_CMETS_Extracted_Data_VoltageFix.xlsx`
  - `CSV: extracted_data.csv`
- Key pain points/problems with the current state (3-5 bullet points):
  - `Parser maintenance burden due to layout variability across meetings.`
  - `Some row-level behavior still relies on targeted output normalizations.`
  - `No formal non-functional/security architecture documentation in repo.`
  - `Execution can fail when output workbook is locked in Excel.`
  - `Runtime environment interop issues can occur in specific sessions (documented in update log).`

---

## SLIDE 14 - PROPOSED SOLUTION ARCHITECTURE (High Level)

- Input Sources for new solution:
  - `Same three folderized PDF groups (Data, Margin, Element Status).`
- Data Processing Layer components:
  - `Table extraction, text extraction, normalization rules, RE enrichment, element-code mapping.`
- Intermediate Storage components:
  - `In-memory Python objects; optional temporary files for validation runs.`
- Workflow / Governance Layer:
  - `Deterministic run order, changelog-driven governance via update.md, validation scripts for anchors.`
- Output / Reporting:
  - `Consolidated XLSX sheets + CSV export.`
- Key improvements over As-Is (3-5 bullets):
  - `Unified pipeline for all target sheets in one run.`
  - `Consistent business-rule enforcement across meetings.`
  - `Reduced manual intervention in data assembly.`
  - `Better traceability through detailed update history.`
  - `Structured PDF folder organization for maintainability.`

---

## SLIDE 15 - PROPOSED LOGICAL / FUNCTIONAL ARCHITECTURE

- Presentation Layer components (UI, dashboards, portals):
  - `Excel workbook sheets consumed by analysts/business users.`
- Application / Business Logic Layer components:
  - `extract_42nd_cmets.py parser modules for CMETS, Margin, and Element Status logic.`
- Data Storage Layer (databases, caches):
  - `File-based outputs (XLSX/CSV); no DB layer.`
- Integration and Processing Layer (APIs, SSO, external system connections):
  - `File-based ingestion/parsing from PDF sources; no API gateway layer currently.`
- Feature / Service Layer (search, audit, notifications, workflow state, etc.):
  - `Field normalization, status resolution, date extraction, code generation, reconciliation rules.`
- Infrastructure and Operations (servers, containers, hosting):
  - `Local/on-prem execution on analyst/developer workstation runtime.`
- User roles and hierarchy (who creates/assigns/uses what):
  - `Developer/IT owner maintains parser rules; business analysts run pipeline and review outputs.`

---

## SLIDE 16 - DATA FLOW ARCHITECTURE

- Data Sources:
  - `CMETS PDFs, RE PDFs, Margin PDFs, TBCB/RTM PDFs, template workbook.`
- Data Injection / Ingestion process:
  - `Camelot/pdfplumber/PyMuPDF load tabular and textual content by meeting/type.`
- Transformation Logic (mapping, normalization):
  - `Meeting-specific + hybrid parsing, RE linking, quantum/type normalization, substation/voltage/status rule application.`
- Storage layers (transactional, cached, audit):
  - `In-memory transactional objects; outputs persisted in XLSX/CSV; change audit via update.md history.`
- Data Preparation / Validation steps:
  - `Post-processing fills (granted defaults, normalizations), anchor checks, reruns with validators.`
- Presentation / Output (dashboards, reports, read-only views):
  - `Data to be captured, Margin, Element Status sheets plus CSV extract.`
- Features applied on data (RBAC, workflow state, commenting, authentication):
  - `Data workflow logic exists; RBAC/authentication controls not implemented at app level.`
- Integration back to external systems:
  - `No automated outbound API integration currently; file outputs are produced for downstream use.`

---

## SLIDE 17 - INTERIM PROCESS ARCHITECTURE (Current / near-term integration state)

- Sources (data inputs): `Folderized PDF inputs in the repository root`
- Access Layer components: `Local filesystem access + Python runtime`
- Raw Data Layer: `Raw PDF text/tables extracted by parser libraries`
- Application Layer services: `Single integrated extraction script`
- Consumption Layer (dashboards, UIs): `Excel workbook and CSV`
- Governance and Security controls: `Manual governance via update log and code review; no dedicated security platform controls in repo`
- Any notes (e.g., serverless SQL, Adani environment boundary): `No serverless SQL or cloud boundary artifacts documented in repo`

---

## SLIDE 18 - FUTURE INTEGRATION ARCHITECTURE

- Future external systems to be integrated: `Not yet specified in repository`
- Future Sources: `Additional CMETS meeting PDFs and possibly standardized source feeds`
- Future Access Layer changes: `Potential service wrapper/API trigger for scheduled runs`
- Future Application Layer additions: `Generic meeting discovery and schema adaptation`
- Future Consumption Layer additions: `Potential dashboard/API delivery beyond workbook outputs`
- Governance and Security updates for future state: `Formal CIA/PIA/NFR/security controls should be defined before scale-out`
- Any notes: `Roadmap item exists to generalize parser for new CMETS variants`

---

## SLIDE 19 - DATA FLOW DIAGRAM

- Data Sources (list all):
  - `CMETS PDFs (42/34/39/38/37/36)`
  - `RE-effectiveness PDFs (Dec/Oct/Sept)`
  - `SN9 Margin PDFs`
  - `TBCB + RTM monitoring PDFs`
- Extract Layer components (APIs, submission services, auth, whitelisting):
  - `File ingestion + parser libraries; no API/whitelisting layer in current implementation`
- Data Processing Hub (validation checks, workflow engine steps):
  - `Meeting extraction -> RE merge -> element mapping -> margin extraction -> sheet writes`
- Validation and Data Checks applied (list all):
  - `Rule checks (withdrawn voltage blank, granted/applied rules), app anchors, counts validation`
- Workflow Engine steps (approval chain, actions, transitions):
  - `Scripted deterministic sequence; no BPM/approval workflow engine currently`
- Storage Segregation (processed store, cleaned store, audit/metadata store):
  - `Processed/cleaned records in memory; final persistence in XLSX/CSV; audit metadata in update.md`
- Consumption Layer (UIs, dashboards, read-only views):
  - `Excel sheets + CSV`
- Platform Governance and Monitoring (RBAC, audit logs, health monitoring):
  - `Basic run logs and manual checks; no central monitoring stack documented`
- Integration back to external systems (trigger conditions, failure handling):
  - `No direct external-system callback integration; failures handled in runtime/log review`

---

## SLIDE 20 - DEPLOYMENT ARCHITECTURE

- Cloud Provider: `NA (current execution is local/on-prem)`
- Region / Data center location: `NA`
- VM / Container setup (describe tiers: web, app, DB): `NA (no containerized tiered deployment documented)`
- Network zones / subnets: `NA`
- Load balancer / gateway: `NA`
- Any on-premise components: `Yes - local machine runtime, filesystem, workbook outputs`
- Backup / snapshot setup: `Not formally documented (manual file/version backups observed)`
- Brief description of diagram if you want it reproduced:
  - `Single-node batch pipeline: PDF folders -> parser engine -> output workbook/CSV`

---

## SLIDE 21 - WEB APP / SOLUTION ARCHITECTURE

- Data Sources (external systems): `PDF source files and template workbook`
- Middleware layer (APIs, REST methods used: GET/POST/PUT/DELETE): `NA (no REST middleware layer)`
- Application Layer (workflow engine, role-based UI, features): `Rule-based batch parser; no role-based UI`
- Client Access Layer (device types, end user roles): `Internal analyst/developer desktop execution`
- Communication format (JSON, XML, etc.): `Internal Python objects; output as XLSX and CSV`
- Authentication mechanism (JWT, token-based, Azure AD, etc.): `NA (no app-level auth mechanism)`
- Key architectural principle / summary statement (1-2 lines):
  - `A deterministic, file-driven ETL pipeline focused on repeatable extraction quality and business-rule consistency.`

---

## SLIDE 22 - NETWORK ARCHITECTURE

- Network topology summary (VNETs, subnets, zones): `Not documented for this local batch tool`
- Application Gateway / Load Balancer type: `NA`
- Firewall / WAF setup: `NA at application level`
- Internal vs. external network separation: `Tool is not exposed as internet-facing service in current design`
- Adani environment boundary details: `Not documented in repository`
- Any notes: `Primarily local filesystem processing; network architecture artifacts absent`

---

## SLIDE 23 - SECURITY ARCHITECTURE

- Network Segmentation (VNETs, subnets, public access controls): `Not documented`
- OT Security (is there OT/ICS integration? Yes/No, describe): `No OT/ICS integration evidenced`
- Endpoint Security controls: `Not defined in repo (likely inherited from corporate endpoint controls)`
- Vulnerability Management process: `Not documented`
- Application Security (RBAC, unauthorized access prevention): `No explicit app-level RBAC/auth layer`
- Cloud Security (key vault, secrets management): `NA (no cloud platform implementation documented)`
- Security Monitoring (event tracking, logging): `Basic runtime logs only`
- SDLC and DevSecOps practices: `No formal DevSecOps process documented`
- SAST / SCA (static analysis, dependency scanning): `SCA partially visible through pinned requirements; no formal SAST pipeline found`
- Encryption (at rest and in transit - method/standard): `Not documented in codebase`
- Identity Security (SSO, MFA, AD integration): `Not implemented in current tool`
- Network Security (HTTPS-only, public DB access controls): `NA (no web/API/DB exposure)`
- Notes / exceptions: `Security controls should be formally baselined before enterprise-scale deployment`

---

## SLIDES 24-31 - TECHNICAL EVALUATION (NFRs)

| # | Question | Answer |
|---|---|---|
| 1 | Deployment mode (Cloud / On-Prem / Hybrid) | On-Prem (current) |
| 2 | Deployment location (Cloud region/DC) | NA (local/on-prem runtime) |
| 3 | Hardware - new vs. reused (if on-prem) | Reused workstation/runtime (assumed) |
| 4 | OS, DB and software - N or N-1 version? | OS/software not formally governed in repo; DB NA |
| 5 | Additional licensing requirements (OS, DB, integration platform) | Not documented; no DB/integration platform license artifacts found |
| 6 | Open-source software used (list all, note community versions) | Yes - `requests`, `beautifulsoup4`, `camelot-py[cv]`, `opencv-python`, `pandas`, `openpyxl`, `fuzzywuzzy`, `python-Levenshtein`, `PyMuPDF`, `pytesseract`, `Pillow`, `pdfplumber` |
| 7 | API integration capabilities | Limited/NA currently (file-based processing, no API layer) |
| 8 | Native / Responsive Mobile app available? | No |
| 9 | Mobile apps compliant with ACE (AppConfig) guidelines? | NA |
| 10 | Compliant with 3rd party EMM solutions? List which | NA |
| 11 | Performance requirements (response time, throughput, concurrent users) | Not documented |
| 12 | Compliant with 3rd party MDM solution? List which | NA |
| 13 | RPO and RTO figures | Not documented |
| 14 | Uptime availability offered (%) | Not documented (batch tool, no SLA stated) |
| 15 | HA, DR and Backup provided? | No formal HA/DR documented |
| 16 | Infra sizing and scalability (scale up/out, concurrent users, TPS, data size) | Not documented |
| 17 | Network bandwidth and infra requirements | Not documented |
| 18 | ITO partner has skills to support? | Not documented |
| 19 | Other customers exist in India? | NA |
| 20 | SI and Support partners exist in India? | NA |
| 21 | Partner supports data destruction upon exit? | Not documented |
| 22 | Security Governance - senior executive oversight, regular reviews? | Not documented |
| 23 | Secure SDLC measures (SAST, DAST, code review, binary scan, threat model) | Not documented as formal process |
| 24 | Security standards and certifications held (ISO27001, SOC2, NIST, etc.) | Not documented for this solution |
| 25 | Identity and Access - AD integration, RBAC, MFA capability? | AD: No evidence, RBAC: No, MFA: No |
| 26 | Encryption - data at rest and in transit (capability and methods) | Not documented |
| 27a | Security Controls - Firewall, WAF, Proxy, EP, AV/EDR | Not documented at application architecture level |
| 27b | PIM/PAM/SSO/MFA/RADIUS/IDM/IAM tools used | Not documented |
| 27c | Key and Certificate Management tool/method | Not documented |
| 27d | Sandboxing and Data Sanitization approach | No dedicated data-sanitization controls documented |
| 27e | Monitoring and Logging (data, network) | Basic script-level logging only |
| 27e (testing) | Testing tools - SAST, DAST, VAPT | Not documented |
| 27f | Endpoint Protection - AV/EDR/XDR tools | Not documented in repo |
| 28 | Application and Platform Hardening Guidelines followed | Not documented |
| 29a | Incident Management process - escalation matrix, MTTR, SLA | Not documented |
| 29b | Patch and Version Management process in place? | Partially via code updates/changelog; formal process not documented |
| 29c | Vulnerability Management process in place? | Not documented |
| 29d | Security Event Monitoring and Incident/Breach reporting to client? | Not documented |
| 30a | Data storage location and localization support | Local file storage; localization support not documented |
| 30b | Data Archival period and Data Destruction policy | Not documented |
| 30c | Master Data Management integration with centrally governed MDG? | NA / Not integrated |
| 30d | CIA impact rating (Low/Medium/High for C, I, A) | Proposed from project context: C=Medium, I=High, A=Medium |
| 30e | Data Classification (Public / Internal / Confidential / Restricted) | Internal (potentially Confidential depending on business policy) |
| 30f | Privacy Impact Assessment controls at design/operations stage | Not documented |
| 30g | Data Access model implemented (RBAC / Context-based / Other) | Other: filesystem/OS-access based |
| 30h | Data duplication avoided? | Partially; both XLSX and CSV are intentionally produced |
| 30i | Data Sharing - APIs only? Other methods (SFTP, WebHook)? | File-based sharing (XLSX/CSV), no API/SFTP/WebHook documented |
| 31 | Periodic Assessment and Testing - methodology and frequency | Ad-hoc reruns + anchor validations; no formal periodic schedule documented |
| 31a | Development Process Compliance (ISO27001, DevSecOps, SAST, DAST, Library Scanning)? | Not documented |
| 31b | Security Testing (COTS) - VA/PT/Grey Box/report furnished? | Not documented |
| 31c | Security Testing (Dev) - framework and test frequency? | Not documented |
| 31d | Third-party/open-source component validation process in place? | Partial (pinned deps); formal validation process not documented |
| 32a | Background checks on all employees and contractors? | Not documented |
| 32b | Cloud/DC provider security policy compliance process in place? | NA (no cloud/DC architecture documented) |
| 32c | Supplier and licensor security standards compliance process? | Not documented |
| 33 | Environment - Multitenant or Dedicated? Data segregation process? Dev/QA/Staging/Prod segregated? | Dedicated/local runtime; formal environment segregation not documented |
| 34 | Change Control procedures and Assurance methodologies | Manual change tracking via `update.md`; formal CAB/assurance process not documented |
| 35 | Audit Trail available (user, user actions, critical transactions)? | Partial technical trace via logs/changelog; no full user-action audit subsystem |
| 36 | Additional licensing required for any components? | Not documented; none explicitly captured in repository |

---

## Final confidence summary

- Strong confidence: extraction flow, sheets covered, parser stack, run command, meeting coverage, current output counts.
- Medium confidence: inferred BU/function and capability impacts.
- Low confidence / needs BU confirmation: governance, partner, legal/compliance, security certifications, TCO/NFR commitments, named owners.
