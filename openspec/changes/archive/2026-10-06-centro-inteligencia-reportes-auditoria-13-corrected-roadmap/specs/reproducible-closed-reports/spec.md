# Delta for Reproducible Closed Reports

## RENAMED Requirements

### Requirement: PDF and CSV Export Reproducibility → PDF/XLSX Export Reproducibility Boundary

(Reason: Corrected roadmap allows PDF/XLSX exports in 1.3.x and removes CSV as the promised spreadsheet target.)
(Migration: Update references from CSV export promises to deferred PDF/XLSX export behavior.)

## MODIFIED Requirements

### Requirement: Exact Closed Report Reproduction

Closed reports MUST be exactly reproducible from trusted daily closure references and reproducibility metadata. Official closed reporting MUST be closure/journey-based, not calendar-day-based. Desktop closure references MUST preserve all collected sources, expenses, net revenue, and item inclusion exactly as saved. Affected repos: API, Desktop, Mobile.
(Previously: closed reports replayed closure references but did not explicitly make closure/journey truth official or cover all corrected revenue sources.)

#### Scenario: Replaying a closed journey report

- GIVEN a journey was closed with a stored reference
- WHEN the same closed report is requested later
- THEN totals, bounds, and exported values match the original closure reference exactly.

#### Scenario: Later operational edits do not rewrite closure reference

- GIVEN a closed journey has a stored reference
- WHEN operational rows are corrected later
- THEN the closure reference remains unchanged
- AND discrepancies are shown separately.

#### Scenario: Calendar grouping is not closure truth

- GIVEN a calendar date includes parts of two journeys
- WHEN an official closed report is requested
- THEN official totals are produced per closure/journey
- AND calendar grouping is labeled secondary.

#### Scenario: Charged solo lavado is replayed from closure reference

- GIVEN a saved closure includes charged solo lavado income
- WHEN the closed report is requested later
- THEN solo-lavado totals match the saved closure reference
- AND they are not recounted from later operations.

### Requirement: PDF/XLSX Export Reproducibility Boundary

Closed-period PDF and XLSX exports MAY be deferred to 1.3.x and MUST NOT block 1.3.0 reporting readiness. When delivered, exports MUST include enough metadata to reproduce the exact report and MUST use closure/journey truth. Affected repos: API, Desktop, Mobile, Installer if packaging assets are required.
(Previously: PDF and CSV exports were required as part of closed-report export reproducibility.)

#### Scenario: Exports deferred from 1.3.0

- GIVEN 1.3.0 reporting is planned without export delivery
- WHEN readiness is evaluated
- THEN missing PDF/XLSX exports do not block the release scope.

#### Scenario: Export includes reproducibility metadata

- GIVEN an admin exports a closed report in a later export slice
- WHEN PDF or XLSX is generated
- THEN it includes report id, journey bounds, closure reference id, generated timestamp, metric catalog version, filters, and source state.

#### Scenario: Spreadsheet target is XLSX

- GIVEN a spreadsheet export is offered
- WHEN the admin requests it
- THEN the format is XLSX
- AND the flow does not promise CSV as the target format.
