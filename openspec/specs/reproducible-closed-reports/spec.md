# Reproducible Closed Reports Specification

## Purpose

Define exact closed-period replay, administrative closure reference behavior, drill-down, discrepancy visibility, and export reproducibility.

## Requirements

### Requirement: Exact Closed Report Reproduction

Closed reports MUST be exactly reproducible from their persisted closure reference and reproducibility metadata. Affected repos: API, Desktop, Mobile.

#### Scenario: Replaying a closed report

- GIVEN a report was closed with a stored reference
- WHEN the same closed report is requested later
- THEN totals, period bounds, and exported values match the original closure reference exactly

#### Scenario: Later operational edits do not rewrite closure reference

- GIVEN a closed period has a stored reference
- WHEN operational rows are corrected later
- THEN the closure reference remains unchanged
- AND discrepancies are shown separately

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
