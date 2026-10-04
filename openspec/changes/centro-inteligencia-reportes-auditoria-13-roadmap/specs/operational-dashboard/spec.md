# Delta for Operational Dashboard

## MODIFIED Requirements

### Requirement: API-Backed Dashboard Consumption

Desktop and Mobile dashboards MUST consume API-backed reporting read models for 1.3.0 instead of independently redefining financial/reporting semantics. Desktop MUST be the primary Intelligence Center client. The API MUST remain reusable for future Mobile expansion without duplicating reporting logic. Mobile 1.3.0 MUST show only daily dashboard and operational summaries relevant to daily work. Affected repos: API, Desktop, Mobile.
(Previously: Desktop and Mobile both consumed dashboard read models without an explicit Desktop-first roadmap or Mobile 1.3.0 scope limit.)

#### Scenario: Desktop uses canonical totals

- GIVEN an admin opens the Desktop Intelligence Center for the current operational day
- WHEN Desktop renders reporting totals
- THEN totals come from the canonical API read model
- AND labels map to the canonical metric catalog

#### Scenario: Mobile uses limited operational summary

- GIVEN an admin opens Mobile reporting in 1.3.0
- WHEN Mobile renders dashboard totals
- THEN it shows daily operational summaries only
- AND it does not expose closed reports or exports

#### Scenario: API contract remains reusable

- GIVEN a future Mobile client needs richer reporting
- WHEN it consumes reporting contracts
- THEN it reuses API read models rather than duplicating Desktop logic

## ADDED Requirements

### Requirement: Desktop Intelligence Center Roadmap Boundary

The system MUST treat Desktop/API as the roadmap home for the Intelligence Center, including closed reports, exports, historical analysis, and audit readiness. Mobile closed reports and exports MUST be deferred to later 1.3.x work. Affected repos: API, Desktop, Mobile.

#### Scenario: Desktop owns full reporting roadmap

- GIVEN an admin needs closed reports or exports
- WHEN 1.3.0 client scope is evaluated
- THEN Desktop/API are the supported Intelligence Center path

#### Scenario: Mobile future scope is explicit

- GIVEN a Mobile user requests closed exports in 1.3.0
- WHEN scope is evaluated
- THEN the capability is marked deferred to 1.3.x
