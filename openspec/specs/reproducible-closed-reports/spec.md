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

Desktop closed-period PDF and XLSX exports MUST be available only for loaded API-backed closed reports with a closure reference. Exported output MUST preserve closure/journey truth and include enough metadata to reproduce the exact report. CSV MUST remain absent and unsupported. This change MUST NOT alter API, Mobile, Installer, audit inventory, user-selected destination, CSV, or local fallback export behavior. Affected repo: Desktop.
(Previously: PDF/XLSX exports could be deferred to 1.3.x and did not define Desktop enablement conditions.)

#### Scenario: Export controls require a valid API-backed closure

- GIVEN no report, a local calendar report, or an API payload without closure reference is loaded
- WHEN Desktop renders export controls
- THEN PDF and XLSX controls are hidden or disabled
- AND CSV is not shown or promised.

#### Scenario: Export includes reproducibility metadata

- GIVEN an admin exports a loaded API-backed closed report with a closure reference
- WHEN PDF or XLSX is generated
- THEN it includes report id, journey bounds, closure reference id, generated timestamp, metric catalog version, filters, and source state.

#### Scenario: Spreadsheet target is XLSX

- GIVEN a spreadsheet export is offered
- WHEN the admin requests it
- THEN the format is XLSX
- AND the flow does not label, request, or promise CSV.

### Requirement: Desktop Closed and Export Roadmap Boundaries

Desktop MUST retrieve closed reports through existing API-backed flows and MUST enable PDF/XLSX export controls only after a valid API-backed closed report with a closure reference is loaded. Export actions MUST call the existing `exportar_reporte_cerrado` path, surface saved path/status on success, preserve API/controller error details on failure, and keep the loaded report available for retry unless the report itself becomes invalid. Desktop MUST remain an admin-only consumer of existing API contracts, MUST display reproducibility, source, completeness, warning, and error states returned by the API, and MUST NOT add API endpoints, database schema, Mobile behavior, installer behavior, CSV export promises, historical plate UI, anomaly UI, local fallback exports, or formal accounting behavior. Affected repo: Desktop.
(Previously: Desktop exposed closed-report retrieval but treated PDF/XLSX export delivery as a roadmap boundary.)

#### Scenario: Closed report is retrieved from the API

- GIVEN an admin opens Desktop reporting and selects a closed report
- WHEN the API returns a closed-report payload
- THEN Desktop MUST display the report id, period bounds, closure reference, totals, and reproducibility metadata
- AND Desktop MUST show the API source and completeness state.

#### Scenario: Export controls become available after valid load

- GIVEN an admin has loaded an API-backed closed report with a closure reference
- WHEN Desktop renders the closed-report actions
- THEN PDF and XLSX controls are visible and enabled
- AND local calendar report state cannot enable them.

#### Scenario: PDF export request is operational

- GIVEN an admin views an API-backed closed report with a closure reference
- WHEN the admin requests PDF export
- THEN Desktop MUST call `exportar_reporte_cerrado` for PDF
- AND Desktop MUST show the saved path or success status returned by the controller.

#### Scenario: XLSX export request is operational

- GIVEN an admin views an API-backed closed report with a closure reference
- WHEN the admin requests spreadsheet export
- THEN Desktop MUST call `exportar_reporte_cerrado` for XLSX
- AND Desktop MUST NOT label, request, or promise CSV export for this flow.

#### Scenario: Export failure is retryable

- GIVEN an admin has loaded a valid API-backed closed report
- WHEN the export controller or API returns an error
- THEN Desktop MUST show the actionable error details
- AND Desktop MUST keep the loaded report available for another export attempt.

#### Scenario: Closed report API failure is explicit

- GIVEN an admin requests a closed report
- WHEN the API request fails or returns an error payload
- THEN Desktop MUST show an actionable error state
- AND Desktop MUST NOT fabricate closed-report totals or exports from local fallback data.
### Requirement: Desktop Closed Report Operation Drill-Down

Desktop MUST let admins inspect API-owned operation rows for a loaded closed report by requesting `GET /reporting/reports/operations` with `period_id=closure:{id}`. Desktop MUST render each returned operation row with category, amount, operator, plate, and timestamp fields, and MUST preserve API pagination, status, warnings, and error states. Affected repo: Desktop.

#### Scenario: Operation rows load for a closed report

- GIVEN an admin has loaded a closed report backed by closure id `42`
- WHEN Desktop requests the operation drill-down
- THEN the request uses `/reporting/reports/operations?period_id=closure:42`
- AND returned operation rows are displayed with category, amount, operator, plate, and timestamp.

#### Scenario: Operation rows are unavailable or empty

- GIVEN an admin has loaded a closed report
- WHEN the API returns an empty result or warning-bearing status
- THEN Desktop keeps the closed report visible
- AND Desktop shows the operation-table empty/status or warning state without local fallback fabrication.

#### Scenario: Operation drill-down API failure is explicit

- GIVEN an admin has loaded a closed report
- WHEN the operation drill-down API request fails or returns an error payload
- THEN Desktop shows an actionable operation-table error state
- AND Desktop MUST NOT fabricate API-owned operation rows from local calendar data.

### Requirement: Desktop API-Owned Operation Query Controls

Desktop MUST support only API-owned operation query controls: `category`, `operator`, `plate`, `sort`, `direction`, `limit`, and `offset`. Desktop MUST NOT invent unsupported query parameters or use operation drill-down for open/current periods. Affected repo: Desktop.

#### Scenario: Supported filters and sorting are sent

- GIVEN an admin applies category, operator, plate, sort, direction, limit, and offset controls
- WHEN Desktop requests operation rows for a closed report
- THEN the request includes only the applied supported parameters plus `period_id=closure:{id}`.

#### Scenario: Unsupported parameters are omitted

- GIVEN UI or controller state contains a value not owned by the operations API contract
- WHEN Desktop builds the operation drill-down request
- THEN the unsupported parameter is omitted from the API request
- AND the request still uses the closed-report closure period.

#### Scenario: Pagination is API-owned

- GIVEN the API returns operation rows with pagination metadata
- WHEN Desktop renders the operation drill-down
- THEN Desktop displays pagination status and uses API-owned limit and offset controls for navigation.

### Requirement: Desktop Local Report Boundary

Desktop MUST keep the existing local calendar report table as legacy/local consultation and separate it from canonical closed-report operation drill-down. Desktop MUST NOT use this slice to reimplement the dashboard, exports, API, Mobile, Installer, open/current operation rows, audit inventory UI, or ledger/event-sourcing behavior. Affected repo: Desktop.

#### Scenario: Local calendar report remains labeled legacy/local

- GIVEN an admin opens the existing calendar-date report table
- WHEN Desktop shows local report results
- THEN the surface is identifiable as legacy/local consultation
- AND it is not presented as canonical closed-report operation drill-down.

#### Scenario: Out-of-scope surfaces stay unchanged

- GIVEN this change is applied
- WHEN Desktop reporting is reviewed
- THEN dashboard behavior, export delivery, API/Mobile/Installer behavior, open/current rows, audit inventory UI, and ledger/event-sourcing behavior remain out of scope.
