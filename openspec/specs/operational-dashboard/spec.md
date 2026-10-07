# Operational Dashboard Specification

## Purpose

Define API-backed dashboard/report consumption for Desktop and Mobile in 1.3.0 using canonical closure-to-closure operational days and metrics.

## Requirements

### Requirement: API-Backed Dashboard Consumption

Desktop MUST consume API-backed reporting read models as the full administrative Intelligence Center. Mobile MUST consume the same canonical dashboard data only for quick consultation and MUST NOT become a full Desktop-equivalent reporting center in 1.3.0. Affected repos: API, Desktop, Mobile.
(Previously: Desktop and Mobile were both described as dashboard consumers without the corrected Desktop-full/Mobile-quick boundary.)

#### Scenario: Desktop uses canonical full-center totals

- GIVEN an admin opens Desktop reporting for the current journey
- WHEN Desktop renders reporting totals
- THEN totals come from the canonical API read model
- AND full-center navigation is available only in Desktop.

#### Scenario: Mobile remains quick consultation

- GIVEN an admin opens Mobile reporting for the same journey
- WHEN Mobile renders reporting data
- THEN totals match the canonical read model
- AND Mobile does not expose full Desktop-center workflows.

### Requirement: Dashboard Period States

The dashboard MUST identify whether a selected period is open or closed and MUST apply the correct reporting source. Affected repos: API, Desktop, Mobile.

#### Scenario: Open period dashboard

- GIVEN the selected operational day has no ending closure yet
- WHEN the dashboard is requested
- THEN period state is `open`
- AND values are calculated from operations

#### Scenario: Closed period dashboard

- GIVEN the selected operational day has an ending closure snapshot
- WHEN the dashboard is requested
- THEN period state is `closed`
- AND closure reference values are available for administrative comparison

### Requirement: Admin-Only Dashboard Access

Financial, reporting, and audit dashboard surfaces MUST be available only to admin users in 1.3.0. Affected repos: API, Desktop, Mobile.

#### Scenario: Admin accesses dashboard

- GIVEN an authenticated admin user
- WHEN the user requests dashboard reporting
- THEN the API returns the authorized read model

#### Scenario: Non-admin access is denied

- GIVEN an authenticated non-admin user
- WHEN the user requests dashboard reporting
- THEN access is denied
- AND no financial totals are returned

### Requirement: Dashboard Filter Consistency

The dashboard MUST apply canonical filters consistently across Desktop and Mobile for operational day, movement type, vehicle identity, user, and operator session where available. Affected repos: API, Desktop, Mobile.

#### Scenario: Matching filters produce matching totals

- GIVEN Desktop and Mobile use the same period and vehicle filter
- WHEN both request the dashboard read model
- THEN returned totals and counts are identical

#### Scenario: Unsupported consumer filter is explicit

- GIVEN a consumer requests an unsupported filter
- WHEN the API validates the request
- THEN the request is rejected with a clear validation error
### Requirement: Desktop Canonical Dashboard Rendering

Desktop MUST render API-provided dashboard metadata without replacing canonical labels. It MUST show period state, source state, completeness state, and capacity metadata when present. Any Desktop local fallback MAY exist only as degraded consultation data and MUST be labeled incomplete, local, and non-official. Affected repos: Desktop.
(Previously: local fallback had to show source/completeness but did not explicitly prohibit official closure-truth claims.)

#### Scenario: Canonical API labels are preserved

- GIVEN the dashboard payload contains canonical metric labels and values
- WHEN Desktop renders the reporting dashboard
- THEN each metric uses the API-provided label
- AND Desktop does not substitute legacy local labels.

#### Scenario: Period and source states are visible

- GIVEN the payload identifies `period_state` and `source_state`
- WHEN Desktop renders the dashboard
- THEN the user can see whether values come from API, operations, closure, or local fallback.

#### Scenario: Local fallback is non-official

- GIVEN the API is unavailable and Desktop uses local fallback
- WHEN Desktop renders totals
- THEN it labels them incomplete, local, and non-official
- AND it does not present them as closure truth.

#### Scenario: Incomplete data warning remains visible

- GIVEN the payload marks reporting completeness as incomplete
- WHEN Desktop renders the dashboard
- THEN Desktop shows a warning without blocking available values.

#### Scenario: Capacity metadata is rendered

- GIVEN the payload contains capacity metadata
- WHEN Desktop renders the dashboard
- THEN capacity is shown with any historical limitation label.
### Requirement: Slice 0 Reconciliation Gate

Before further reporting implementation, the system roadmap MUST classify already merged API, Desktop, and Mobile work as keep, change, remove, or defer against the corrected product decisions.

#### Scenario: Reconciliation blocks implementation planning

- GIVEN merged reporting work exists from the previous roadmap
- WHEN implementation planning starts
- THEN each merged behavior has a keep/change/remove/defer outcome
- AND unresolved items block further apply work.

#### Scenario: Deferred work remains explicit

- GIVEN a merged behavior is useful but not 1.3.0-critical
- WHEN Slice 0 classifies it
- THEN it is marked defer with the target follow-up scope.
### Requirement: Desktop Dashboard API-Owned Request Shape

Desktop MUST request the reporting dashboard using only the API-owned dashboard endpoint and parameters. Desktop MUST NOT send `period_id=current`, `state=open`, or any other dashboard query parameter unless the API contract declares it for `GET /reporting/dashboard`. Affected repos: Desktop.

#### Scenario: Desktop requests canonical dashboard endpoint

- GIVEN Desktop needs dashboard summary data
- WHEN it builds the dashboard API request
- THEN it targets `GET /reporting/dashboard`
- AND no undeclared dashboard query parameters are sent.

#### Scenario: Future API-owned parameter is allowed

- GIVEN the API contract later declares a dashboard parameter
- WHEN Desktop implements that declared parameter
- THEN the request remains within the API-owned dashboard contract.

### Requirement: Mocked Dashboard Contract Compatibility

Desktop MUST include mocked contract tests proving metric catalog and dashboard payload compatibility with the canonical reporting API. These tests MUST cover endpoint construction, canonical metric catalog fields, dashboard metadata preservation, and rendering of compatible payloads without requiring a live API server. Affected repos: Desktop.

#### Scenario: Metric catalog contract is covered

- GIVEN the mocked API exposes the canonical metric catalog
- WHEN Desktop fetches reporting catalog data
- THEN the test proves the canonical endpoint and metric keys are consumed compatibly.

#### Scenario: Dashboard payload metadata is preserved

- GIVEN a mocked dashboard payload includes period, catalog version, filters, metrics, and pagination
- WHEN Desktop normalizes and renders the payload
- THEN compatible metadata is preserved for the dashboard flow.

### Requirement: Optional Local API Smoke Evidence

Local API smoke validation MAY be performed only when an authenticated seeded local API is available. Delivery MUST NOT require remote, production, unauthenticated, or unavailable API smoke evidence when mocked contract tests pass. Affected repos: Desktop.

#### Scenario: Seeded local API is available

- GIVEN an authenticated seeded local API is available
- WHEN smoke validation is run
- THEN metric catalog and dashboard endpoints MAY be recorded as supporting evidence.

#### Scenario: Seeded local API is unavailable

- GIVEN no authenticated seeded local API is available
- WHEN delivery is verified
- THEN mocked contract tests remain the required validation gate.

### Requirement: Validation Scope Boundary

This change MUST NOT add Desktop operations drill-down or pagination UI, API changes, Mobile changes, Installer changes, remote validation, or production-data probing. Affected repos: Desktop.

#### Scenario: Operations pagination remains out of scope

- GIVEN `/reporting/reports/operations` supports pagination
- WHEN this validation change is implemented
- THEN Desktop dashboard behavior is not expanded into operations drill-down or pagination UI.

#### Scenario: Sibling repositories are untouched

- GIVEN the change is scoped to Desktop validation
- WHEN implementation tasks are planned
- THEN API, Mobile, and Installer work is excluded.
