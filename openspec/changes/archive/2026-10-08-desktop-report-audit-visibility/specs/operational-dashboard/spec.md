# Delta for Operational Dashboard

## MODIFIED Requirements

### Requirement: Desktop Canonical Dashboard Rendering

Desktop MUST render API-provided dashboard metadata without replacing canonical labels. It MUST show period state, source state, completeness state, capacity metadata, and compact audit coverage/status when present. Audit coverage payload variants MAY be normalized only as needed to produce stable visible text. Missing or empty audit coverage MUST be shown as unavailable or not provided, not as official coverage. Any Desktop local fallback MAY exist only as degraded consultation data and MUST be labeled incomplete, local, non-official, and audit-unavailable. Affected repos: Desktop.
(Previously: Desktop rendered period/source/completeness/capacity metadata and local fallback labels, but did not require audit coverage/status visibility or audit-unavailable fallback labeling.)

#### Scenario: Canonical API labels are preserved

- GIVEN the dashboard payload contains canonical metric labels and values
- WHEN Desktop renders the reporting dashboard
- THEN each metric uses the API-provided label
- AND Desktop does not substitute legacy local labels.

#### Scenario: Period and source states are visible

- GIVEN the payload identifies `period_state` and `source_state`
- WHEN Desktop renders the dashboard
- THEN the user can see whether values come from API, operations, closure, or local fallback.

#### Scenario: API audit summary is visible

- GIVEN an API-backed dashboard payload includes audit coverage/status metadata
- WHEN Desktop renders the dashboard metadata area
- THEN a compact audit summary is visible
- AND it distinguishes available coverage from known gaps.

#### Scenario: Payload variants produce stable text

- GIVEN equivalent audit coverage/status payload variants are supplied
- WHEN Desktop prepares visible metadata
- THEN the rendered audit text remains stable
- AND normalization does not invent missing coverage.

#### Scenario: Empty audit coverage is unavailable

- GIVEN the API-backed payload omits audit coverage or supplies an empty value
- WHEN Desktop renders the dashboard metadata area
- THEN audit coverage is labeled unavailable or not provided
- AND it is not presented as official coverage.

#### Scenario: Local fallback is non-official

- GIVEN the API is unavailable and Desktop uses local fallback
- WHEN Desktop renders totals
- THEN it labels them incomplete, local, non-official, and audit-unavailable
- AND it does not present them as closure truth or audit coverage.

#### Scenario: Incomplete data warning remains visible

- GIVEN the payload marks reporting completeness as incomplete
- WHEN Desktop renders the dashboard
- THEN Desktop shows a warning without blocking available values.

#### Scenario: Capacity metadata is rendered

- GIVEN the payload contains capacity metadata
- WHEN Desktop renders the dashboard
- THEN capacity is shown with any historical limitation label.

## ADDED Requirements

### Requirement: Desktop Audit Visibility Scope Boundary

This change MUST NOT add API, Mobile, Installer, database, migration, remote validation, or new endpoint work. If the existing dashboard payload cannot support meaningful audit visibility, Desktop implementation MUST stop and recommend API change `api-report-audit-inventory`. Affected repos: Desktop.

#### Scenario: Existing payload is insufficient

- GIVEN available dashboard payloads cannot supply meaningful audit status or limitations
- WHEN Desktop audit visibility is evaluated
- THEN Desktop work stops for this change
- AND `api-report-audit-inventory` is recommended.

#### Scenario: Sibling repositories remain untouched

- GIVEN implementation tasks are planned for this change
- WHEN scope is evaluated
- THEN API, Mobile, Installer, database, migration, and new endpoint work are excluded.
