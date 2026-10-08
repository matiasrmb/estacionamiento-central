# Delta for Reproducible Closed Reports

## ADDED Requirements

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
