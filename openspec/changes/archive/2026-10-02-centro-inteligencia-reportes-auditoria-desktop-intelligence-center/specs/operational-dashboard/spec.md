# Delta for Operational Dashboard

## ADDED Requirements

### Requirement: Desktop Canonical Dashboard Rendering

Desktop MUST render API-provided dashboard metadata without replacing canonical labels. It MUST show period state, source state, completeness state, and capacity metadata when present. Affected repos: Desktop.

#### Scenario: Canonical API labels are preserved

- GIVEN the dashboard payload contains canonical metric labels and values
- WHEN Desktop renders the reporting dashboard
- THEN each metric uses the API-provided label
- AND Desktop does not substitute legacy local labels for those metrics

#### Scenario: Period and source states are visible

- GIVEN the dashboard payload identifies `period_state` and `source_state`
- WHEN Desktop renders the reporting dashboard
- THEN the user can see whether the period is open or closed
- AND the user can see whether values come from API, operations, closure, or local fallback state

#### Scenario: Incomplete data warning is visible

- GIVEN the dashboard payload marks reporting completeness as incomplete
- WHEN Desktop renders the reporting dashboard
- THEN Desktop shows a warning that totals may be incomplete
- AND the warning does not block rendering available values

#### Scenario: Capacity metadata is rendered

- GIVEN the dashboard payload contains capacity metadata for the reporting period
- WHEN Desktop renders the reporting dashboard
- THEN Desktop shows the capacity information next to the dashboard summary
- AND missing capacity metadata is rendered as unavailable rather than zero
