# Canonical Reporting API Specification

## Purpose

Define canonical reporting semantics, metric names, period inputs, and read-model behavior used by API, Desktop, and Mobile in 1.3.0.

## Requirements

### Requirement: Metric Catalog and Sign Semantics

The system MUST expose a canonical metric catalog for reporting consumers. Charged solo lavado operational income MUST be represented as collected operational income for Desktop local reports; active and converted solo lavados MUST NOT be represented as collected income. Affected repos: API, Desktop, Mobile.
(Previously: operational income focused on collected payments but did not explicitly state Desktop solo lavado inclusion/exclusion.)

| Metric | Meaning | Sign |
|---|---|---|
| `operational_income_total` | Payments collected from operational sources, including charged solo lavado income | positive |
| `operational_expense_total` | Operational expenses | positive in expense lists; negative in result components |
| `operational_net_total` | Income minus expenses | signed |
| `mensualidad_sales_total` | Commercial mensualidad activity | positive |
| `vehicle_movement_count` | Vehicle entries/exits in the period | count |

Financial reporting MUST focus on payments. Commercial reporting MAY focus on mensualidad activity without treating it as payment-method accounting.

#### Scenario: Net calculation uses operational signs

- GIVEN operational income is 1000 and expenses are 150
- WHEN the report summary is requested
- THEN `operational_expense_total` is 150 in expense lists
- AND `operational_net_total` is 850

#### Scenario: Excluded accounting concepts are not exposed

- GIVEN a consumer requests financial metrics
- WHEN the API returns the metric catalog
- THEN taxes, commissions, payment-method accounting, and formal ledger balances MUST NOT appear

#### Scenario: Desktop charged solo lavado is operational income

- GIVEN Desktop has one charged solo lavado in the reporting period
- WHEN Desktop calculates local report totals
- THEN `operational_income_total` MUST include the charged solo lavado amount
- AND active or converted solo lavados MUST NOT be included
### Requirement: Operational Period Semantics

The system MUST define an operational day as the period from one daily closure to the next daily closure, including periods that cross calendar midnight. Operator login/logout attendance sessions MUST be modeled as operator sessions inside an operational day, not as operational days themselves. Affected repos: API, Desktop, Mobile.

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

