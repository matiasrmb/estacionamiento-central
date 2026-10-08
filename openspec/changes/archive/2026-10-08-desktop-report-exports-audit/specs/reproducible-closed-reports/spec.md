# Delta for Reproducible Closed Reports

## MODIFIED Requirements

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
