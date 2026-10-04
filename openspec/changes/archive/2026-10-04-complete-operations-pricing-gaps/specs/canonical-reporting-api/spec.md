# Delta for Canonical Reporting API

## ADDED Requirements

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

## MODIFIED Requirements

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
