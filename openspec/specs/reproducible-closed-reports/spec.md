# Reproducible Closed Reports Specification

## Purpose

Define exact closed-period replay, administrative closure reference behavior, drill-down, discrepancy visibility, and export reproducibility.

## Requirements

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
### Requirement: Desktop Closed and Export Roadmap Boundaries

Desktop MUST replace the closed-report and export roadmap-boundary entry points with operational API-backed closed-report retrieval and PDF/XLSX export flows. Desktop MUST remain an admin-only consumer of existing API contracts, MUST display reproducibility, source, completeness, warning, and error states returned by the API, and MUST NOT add API endpoints, database schema, Mobile behavior, installer behavior, CSV export promises, historical plate UI, anomaly UI, or formal accounting behavior. Affected repo: Desktop.
(Previously: Desktop exposed visible closed-report and PDF/CSV export entry points as future-only boundaries and did not call API-backed closed/export flows.)

#### Scenario: Closed report is retrieved from the API

- GIVEN an admin opens Desktop reporting and selects a closed report
- WHEN the API returns a closed-report payload
- THEN Desktop MUST display the report id, period bounds, closure reference, totals, and reproducibility metadata
- AND Desktop MUST show the API source and completeness state

#### Scenario: Incomplete closed report remains usable with warnings

- GIVEN the API returns a closed report marked incomplete or warning-bearing
- WHEN Desktop renders the closed report
- THEN Desktop MUST keep the report visible to the admin
- AND Desktop MUST show the incompleteness or warning message without treating it as formal accounting

#### Scenario: Closed report API failure is explicit

- GIVEN an admin requests a closed report
- WHEN the API request fails or returns an error payload
- THEN Desktop MUST show an actionable error state
- AND Desktop MUST NOT fabricate closed-report totals from local fallback data

#### Scenario: PDF export request is operational

- GIVEN an admin views an API-backed closed report
- WHEN the admin requests PDF export
- THEN Desktop MUST request the API-backed PDF export and surface the returned file or download result
- AND Desktop MUST preserve API error details if the export fails

#### Scenario: XLSX export replaces CSV promise

- GIVEN an admin views an API-backed closed report
- WHEN the admin requests spreadsheet export
- THEN Desktop MUST request XLSX export
- AND Desktop MUST NOT label, request, or promise CSV export for this flow
