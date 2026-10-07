# Delta for Operational Dashboard

## ADDED Requirements

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
