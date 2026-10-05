# Delta for Canonical Reporting API

## ADDED Requirements

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

## MODIFIED Requirements

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
