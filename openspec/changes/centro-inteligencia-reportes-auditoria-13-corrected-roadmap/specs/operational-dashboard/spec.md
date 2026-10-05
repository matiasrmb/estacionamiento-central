# Delta for Operational Dashboard

## ADDED Requirements

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

## MODIFIED Requirements

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
