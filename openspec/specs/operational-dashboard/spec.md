# Operational Dashboard Specification

## Purpose

Define API-backed dashboard/report consumption for Desktop and Mobile in 1.3.0 using canonical closure-to-closure operational days and metrics.

## Requirements

### Requirement: API-Backed Dashboard Consumption

Desktop and Mobile dashboards MUST consume API-backed reporting read models for 1.3.0 instead of independently redefining financial/reporting semantics. Affected repos: API, Desktop, Mobile.

#### Scenario: Desktop uses canonical totals

- GIVEN an admin opens the Desktop dashboard for the current operational day
- WHEN Desktop renders reporting totals
- THEN totals come from the canonical API read model
- AND labels map to the canonical metric catalog

#### Scenario: Mobile uses the same read model

- GIVEN an admin opens Mobile reporting for the same operational day
- WHEN Mobile renders dashboard totals
- THEN totals match Desktop for the same filters

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
