# Delta for Admin Reporting Access

## MODIFIED Requirements

### Requirement: Audit Inventory from Existing Sources

The system MUST provide audit inventory based on existing operational, closure, payment, expense, print, and user/session sources. It MUST identify coverage gaps and support the product goal of full audit over time. Desktop MUST surface existing-source audit limitations when supplied by reporting payloads and MUST render a compact audit inventory/readiness panel using only API-supplied fields from `GET /reporting/audit-inventory` with optional `period_id`. Desktop MUST NOT fabricate local coverage, source totals/counts, freshness timestamps, event sourcing, or persisted anomaly data. Affected repos: API, Desktop, Mobile. This delta changes Desktop only; API and Mobile behavior remain unchanged.
(Previously: Desktop surfaced supplied dashboard audit limitations but did not require a detailed audit inventory/readiness panel backed by `GET /reporting/audit-inventory`.)

#### Scenario: Existing-source inventory

- GIVEN an admin requests audit inventory for a journey
- WHEN inventory is generated
- THEN it identifies available sources and their coverage
- AND unavailable history is labeled explicitly.

#### Scenario: Event sourcing is excluded

- GIVEN audit inventory is requested
- WHEN the system prepares audit data
- THEN it does not require new append-only event streams for 1.3.0.

#### Scenario: Audit trajectory is visible

- GIVEN the 1.3.0 audit slice has known gaps
- WHEN report metadata is shown
- THEN gaps are labeled as audit limitations
- AND they are not presented as complete audit coverage.

#### Scenario: Supplied dashboard limitations are surfaced

- GIVEN an API-backed dashboard payload supplies audit limitations or unavailable sources
- WHEN Desktop renders report metadata
- THEN the limitations are visible to the admin
- AND Desktop does not reclassify them as complete coverage.

#### Scenario: Missing limitations are not fabricated

- GIVEN the dashboard payload does not supply audit limitations
- WHEN Desktop renders report metadata
- THEN Desktop shows audit limitations as unavailable or not provided
- AND no source coverage is fabricated.

#### Scenario: Desktop requests audit inventory by period

- GIVEN an admin opens the Desktop audit inventory panel with no period or a supported `period_id`
- WHEN Desktop loads inventory readiness
- THEN it requests only `GET /reporting/audit-inventory` with optional `period_id`
- AND it does not send undeclared query parameters.

#### Scenario: Desktop renders API-supplied readiness

- GIVEN the audit inventory response includes `period_id`, `coverage[]`, source states, source groups, affected scopes, unavailable history, and unsupported behaviors
- WHEN Desktop renders the panel
- THEN it shows available, partial, unavailable, affected-scope, event-sourcing, persisted-anomaly, and unsupported-behavior readiness from those fields.

#### Scenario: Desktop handles unavailable inventory payloads

- GIVEN the audit inventory response is missing required fields or the request fails
- WHEN Desktop renders the panel
- THEN it shows inventory readiness as unavailable or error
- AND it does not infer coverage from local state or other Desktop data.
