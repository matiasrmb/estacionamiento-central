# Canonical Reporting API Specification

## Purpose

Define canonical reporting semantics, metric names, period inputs, and read-model behavior used by API, Desktop, and Mobile in 1.3.0.

## Requirements

### Requirement: Metric Catalog and Sign Semantics

The system MUST expose a canonical metric catalog for administrative financial-operational reporting. Net revenue MUST equal all collected sources minus expenses for the selected closure, journey, or period. Collected sources MUST include parking records, bathrooms, washes including converted and solo charged washes, monthly payments, nights, and future service categories. Monthly payments MUST count in the journey where collected; the covered month MUST NOT define the financial period. Affected repos: API, Desktop, Mobile.
(Previously: operational income focused on narrower operational sources and did not define all collected sources, monthly-payment timing, future services, or corrected net revenue.)

| Metric | Meaning | Sign |
|---|---|---|
| `collected_sources_total` | All collected sources for the selected closure, journey, or period | positive |
| `operational_expense_total` | Operational expenses | positive in expense lists; negative in net components |
| `net_revenue_total` | Collected sources minus expenses | signed |
| `monthly_payments_collected_total` | Monthly payments collected in the selected journey | positive |
| `vehicle_movement_count` | Vehicle entries/exits in the period | count |

Financial-operational reporting MUST focus on collected money, not formal accounting ledgers.

#### Scenario: Net calculation uses collected sources

- GIVEN collected sources are 1000 and expenses are 150
- WHEN the report summary is requested
- THEN `net_revenue_total` is 850
- AND expenses remain visible as positive expense rows.

#### Scenario: Excluded accounting concepts are not exposed

- GIVEN a consumer requests reporting metrics
- WHEN the API returns the metric catalog
- THEN taxes, commissions, payment-method accounting, and ledger balances MUST NOT appear.

#### Scenario: Monthly payment follows collection journey

- GIVEN a monthly payment covering May is collected during the June 2 journey
- WHEN the June 2 journey report is requested
- THEN the payment is included in that journey's collected sources.

#### Scenario: Charged solo lavado is collected income

- GIVEN a charged solo lavado occurs in the reporting journey
- WHEN collected sources are calculated
- THEN the charged solo lavado amount is included
- AND active uncharged washes are excluded.

### Requirement: Operational Period Semantics

The system MUST define official reporting periods by daily closure/journey boundaries, including periods that cross calendar midnight. Calendar dates MAY filter or group reports secondarily but MUST NOT be the official financial period. Current daily closures are trusted closure anchors. Operator sessions remain sub-filters inside journeys. Affected repos: API, Desktop, Mobile.
(Previously: operational days were closure-to-closure, but calendar-day secondary status and trusted current closures were not explicit.)

#### Scenario: Journey crosses midnight

- GIVEN a closure occurs at 09:30 and the next closure at 02:00 next day
- WHEN the journey report is requested
- THEN all operations between closures are one official journey.

#### Scenario: Calendar is secondary

- GIVEN a calendar-date filter overlaps two journeys
- WHEN reporting totals are requested
- THEN official totals remain tied to journey boundaries
- AND calendar grouping is labeled secondary.

#### Scenario: Operator sessions remain journey filters

- GIVEN two operators work inside the same journey
- WHEN reporting filters by operator session
- THEN the official journey is not split
- AND filtered totals remain scoped to that journey.

#### Scenario: Missing next closure keeps journey open

- GIVEN a daily closure has occurred and no later closure exists
- WHEN the current journey is requested
- THEN journey status is `open`
- AND live operations since the trusted closure are used.
### Requirement: API Read Model Contract

The API MUST own canonical read models for dashboard and reports and MUST support about 400 vehicles/day without pagination loss. Affected repos: API, Desktop, Mobile.

#### Scenario: Shared consumer contract

- GIVEN Desktop and Mobile request the same period and filters
- WHEN both call the canonical API contract
- THEN metric names, totals, and period boundaries match

#### Scenario: Expected load is represented completely

- GIVEN a period contains about 400 vehicle movements
- WHEN a report read model is requested
- THEN all matching movements are represented in totals
- AND consumers receive stable pagination or complete summary metadata

### Requirement: Open Period Source of Truth

For open periods, the system MUST calculate reporting values from operational rows, not closure snapshots. Affected repos: API, Desktop, Mobile.

#### Scenario: Open period reflects latest operation

- GIVEN a period is open and a new paid exit is recorded
- WHEN the report summary is requested
- THEN operational income includes that payment

#### Scenario: Closure snapshot is ignored while open

- GIVEN a period is open
- WHEN reports are calculated
- THEN no closed-period snapshot is used as the source of truth
### Requirement: Desktop Canonical Dashboard Normalization

Desktop MUST normalize dashboard responses into a view model that preserves canonical reporting fields and exposes fallback metadata. Local fallback summaries MUST be marked incomplete and local. Affected repos: Desktop.

#### Scenario: API dashboard fields are preserved

- GIVEN the API returns metric labels, period state, source state, completeness, and capacity metadata
- WHEN Desktop normalizes the dashboard response
- THEN the normalized result preserves those fields for the view
- AND metric labels remain the canonical API labels

#### Scenario: Local fallback is marked incomplete

- GIVEN the API dashboard cannot be obtained and Desktop uses a local fallback summary
- WHEN Desktop normalizes the fallback summary
- THEN the normalized result sets completeness to incomplete
- AND source state identifies the data as local fallback

#### Scenario: Unit tests remain payload-driven

- GIVEN Desktop controller tests provide canonical dashboard payloads directly
- WHEN the tests verify normalization behavior
- THEN they do not require a live API containing PR #80, #81, or #82 fields
- AND live runtime verification may still list that API chain as a prerequisite
### Requirement: Preserve scope boundaries for pricing gaps

Affected repos: Desktop, API, Mobile. This change MUST NOT add quote persistence, monthly billing automation, API behavior changes, Mobile behavior changes, or installer schema parity.

#### Scenario: Quote and monthly flows stay unchanged

- GIVEN Desktop includes charged solo lavado operational income
- WHEN quote or monthly billing features are used
- THEN the change MUST NOT create quote records, monthly charges, PDFs, or conversion workflows

#### Scenario: API and Mobile remain semantic consumers

- GIVEN Desktop local reports include charged solo lavado income
- WHEN API or Mobile reporting behavior is exercised
- THEN their behavior MUST remain unchanged by this Desktop slice

### Requirement: Configurable Capacity and Historical Labels

The API MUST expose current installation capacity as configurable metadata with a default/current value of 50 vehicles. Historical periods without reliable capacity configuration MUST be labeled as capacity-unknown or capacity-limited, not inferred as 50.

#### Scenario: Current capacity is explicit

- GIVEN an installation capacity is configured as 50 vehicles
- WHEN a dashboard or report read model is requested
- THEN capacity metadata reports 50 as the configured current capacity
- AND the value is not hard-coded as immutable.

#### Scenario: Historical capacity is limited

- GIVEN a closed historical journey lacks capacity metadata
- WHEN the report is requested
- THEN the capacity state is labeled historical-capacity-limited
- AND utilization percentages are not presented as authoritative.

### Requirement: Basic Deterministic Anomaly Contract

The API SHOULD expose deterministic anomaly flags for obvious reporting inconsistencies in 1.3.0. The contract MUST NOT require machine learning or event sourcing.

#### Scenario: Closure mismatch anomaly

- GIVEN closure totals differ from recalculated operational totals
- WHEN a closed journey report is returned
- THEN the response includes a deterministic discrepancy anomaly.

#### Scenario: No anomaly for matching totals

- GIVEN closure and recalculated totals match
- WHEN anomalies are evaluated
- THEN no discrepancy anomaly is emitted.

