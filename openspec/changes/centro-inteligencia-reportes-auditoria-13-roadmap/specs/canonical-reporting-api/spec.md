# Delta for Canonical Reporting API

## MODIFIED Requirements

### Requirement: Metric Catalog and Sign Semantics

The system MUST expose a canonical metric catalog for reporting consumers. `operational_net_total` MUST mean net cash collected in the operational journey, including mensualidades when collected in that journey, minus operational expenses. Affected repos: API, Desktop, Mobile.
(Previously: operational net was income minus expenses without explicitly approving journey-collected mensualidades.)

| Metric | Meaning | Sign |
|---|---|---|
| `operational_income_total` | Payments collected from operational sources, including journey-collected mensualidades | positive |
| `operational_expense_total` | Operational expenses | positive in expense lists; negative in result components |
| `operational_net_total` | Journey cash collected minus expenses | signed |
| `mensualidad_sales_total` | Commercial mensualidad activity | positive |
| `vehicle_movement_count` | Vehicle entries/exits in the period | count |

Financial reporting MUST focus on payments. Commercial reporting MAY focus on mensualidad activity without treating it as payment-method accounting.

#### Scenario: Net calculation uses operational signs

- GIVEN operational cash collected is 1000, journey-collected mensualidades are 200, and expenses are 150
- WHEN the report summary is requested
- THEN `operational_income_total` is 1200
- AND `operational_net_total` is 1050

#### Scenario: Excluded accounting concepts are not exposed

- GIVEN a consumer requests financial metrics
- WHEN the API returns the metric catalog
- THEN taxes, commissions, payment-method accounting, and formal ledger balances MUST NOT appear

### Requirement: Operational Period Semantics

The system MUST define operational, financial, and audit business-day reports primarily from one daily closure to the next. Calendar date MUST be secondary for filtering, grouping, and historical analysis. Operations after midnight but before closure MUST belong to the operational journey started the previous calendar day. Affected repos: API, Desktop, Mobile.
(Previously: operational day crossed midnight, but calendar-date secondary semantics and after-midnight attribution were not explicit.)

#### Scenario: Operational day crosses midnight

- GIVEN a daily closure occurs at 09:30 and the next daily closure occurs at 02:00 next day
- WHEN the operational period is requested
- THEN the period includes operations between both closures
- AND it is represented as one operational day

#### Scenario: Multiple operator sessions belong to one operational day

- GIVEN operator A works 09:30-14:30 and operator B works 14:30-19:30 before the next daily closure
- WHEN the current operational period is requested
- THEN both operator sessions belong to the same operational day
- AND reporting can still filter by operator/session without splitting the operational day

#### Scenario: Missing next closure keeps operational day open

- GIVEN a daily closure has occurred and no later closure exists
- WHEN the current operational day is requested
- THEN the operational day status is `open`
- AND results are calculated from live operations since the last closure

#### Scenario: After-midnight operation belongs to prior journey

- GIVEN the journey started on Monday and closes at Tuesday 02:00
- WHEN an operation occurs Tuesday 01:00
- THEN it belongs to Monday's operational journey

## ADDED Requirements

### Requirement: Capacity and Historical Completeness Semantics

The system MUST model maximum capacity as 50 total spaces including monthly customers. Effective transient capacity MUST subtract active monthly customers. Historical metrics before instrumentation MAY be partial or unavailable, and the system MUST state that explicitly. Affected repos: API, Desktop, Mobile.

#### Scenario: Effective transient capacity

- GIVEN maximum capacity is 50 and 12 monthly customers are active
- WHEN capacity metrics are requested
- THEN total capacity is 50
- AND effective transient capacity is 38

#### Scenario: Partial historical metrics are labelled

- GIVEN a requested historical period predates required instrumentation
- WHEN historical metrics are returned
- THEN completeness is `partial` or `unavailable`
- AND incomplete data MUST NOT be presented as complete historical truth
