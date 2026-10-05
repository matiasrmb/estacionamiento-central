# Delta for Reproducible Closed Reports

## MODIFIED Requirements

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
