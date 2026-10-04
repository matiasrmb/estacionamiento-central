# Reproducible Closed Reports Specification

## Purpose

Define exact closed-period replay, administrative closure reference behavior, drill-down, discrepancy visibility, and export reproducibility.

## Requirements

### Requirement: Exact Closed Report Reproduction

Closed reports MUST be exactly reproducible from their persisted closure reference and reproducibility metadata. Desktop closure references MUST preserve charged solo lavado totals and item inclusion exactly as saved. Affected repos: API, Desktop, Mobile.
(Previously: closed reports had to replay persisted closure references, but solo lavado closure totals were not explicit.)

#### Scenario: Replaying a closed report

- GIVEN a report was closed with a stored reference
- WHEN the same closed report is requested later
- THEN totals, period bounds, and exported values match the original closure reference exactly

#### Scenario: Later operational edits do not rewrite closure reference

- GIVEN a closed period has a stored reference
- WHEN operational rows are corrected later
- THEN the closure reference remains unchanged
- AND discrepancies are shown separately

#### Scenario: Charged solo lavado is replayed from closure reference

- GIVEN Desktop saved a closure containing charged solo lavado income
- WHEN that closed report is requested later
- THEN solo-lavado totals and general totals MUST match the saved closure reference
- AND the solo lavado MUST NOT be recounted from a later open-period calculation
### Requirement: Closure Reference and Operations Drill-Down

Closed periods MUST preserve closure values as administrative reference and SHALL allow drill-down against operational rows. Affected repos: API, Desktop, Mobile.

#### Scenario: Closed period comparison

- GIVEN a closed period exists
- WHEN an admin opens the report detail
- THEN closure reference totals and operation-derived totals are both visible

#### Scenario: Drill-down explains totals

- GIVEN an admin views a closed report total
- WHEN the admin opens drill-down
- THEN the contributing operations are listed with canonical categories

### Requirement: Discrepancy Visibility

The system MUST show discrepancies between closure reference values and recalculated operational values without treating either view as formal accounting. Affected repos: API, Desktop, Mobile.

#### Scenario: Discrepancy is visible

- GIVEN closure income is 1000 and recalculated operational income is 980
- WHEN the closed report is requested
- THEN a discrepancy of -20 is shown
- AND the report identifies both compared sources

#### Scenario: No discrepancy

- GIVEN closure and recalculated operation totals match
- WHEN the closed report is requested
- THEN discrepancy status is `none`

### Requirement: PDF and CSV Export Reproducibility

Closed-period PDF and CSV exports MUST include enough metadata to reproduce the exact report. Affected repos: API, Desktop, Mobile, Installer if packaging assets are required.

#### Scenario: Export includes reproducibility metadata

- GIVEN an admin exports a closed report
- WHEN PDF or CSV is generated
- THEN it includes report id, period bounds, closure reference id, generated timestamp, metric catalog version, filters, and source state

#### Scenario: Same closed export content

- GIVEN the same closed report and same export format are requested twice
- WHEN no export template version changes
- THEN report data content is identical
### Requirement: Desktop Closed and Export Roadmap Boundaries

Desktop MUST expose closed-report and export entry points as roadmap boundaries only in this slice. It MUST NOT implement API-backed closed-report retrieval or export generation flows here. Affected repos: Desktop.

#### Scenario: Closed report boundary is visible but non-calling

- GIVEN an admin opens Desktop reporting
- WHEN the closed-report action is shown
- THEN Desktop labels it as a future API-backed capability
- AND activating it does not call a closed-report API endpoint

#### Scenario: Export boundary is visible but non-generating

- GIVEN an admin opens Desktop reporting
- WHEN the export action is shown
- THEN Desktop labels PDF/CSV export as a future API-backed capability
- AND activating it does not generate PDF or CSV output

#### Scenario: Boundary copy states prerequisites

- GIVEN Desktop renders closed/export roadmap boundaries
- WHEN the user reads the boundary text
- THEN it states that API-backed closed/export support is required before the flow becomes operational
