# Admin Reporting Access Specification

## Purpose

Define access control and audit inventory boundaries for financial, reporting, export, and audit surfaces in 1.3.0.

## Requirements

### Requirement: Admin-Only Reporting Boundary

The system MUST restrict financial, reporting, export, and audit surfaces to admin users in 1.3.0. Affected repos: API, Desktop, Mobile.

#### Scenario: Admin can access reports

- GIVEN an authenticated admin user
- WHEN the user opens reporting or export surfaces
- THEN access is granted according to the report contract

#### Scenario: Non-admin cannot access reports

- GIVEN an authenticated non-admin user
- WHEN the user opens reporting, export, or audit surfaces
- THEN access is denied
- AND no report payload is returned

### Requirement: No Auditor Role in 1.3.0

The system MUST NOT require or expose an auditor role in 1.3.0, but contracts MAY avoid blocking a future role if that adds no 1.3.0 complexity. Affected repos: API, Desktop, Mobile.

#### Scenario: Auditor role is absent

- GIVEN roles are evaluated for reporting access
- WHEN 1.3.0 authorization rules are applied
- THEN only admin access grants reporting privileges

#### Scenario: Future role is not implemented accidentally

- GIVEN a client sends an auditor-role token or flag
- WHEN reporting authorization is evaluated
- THEN it does not grant access unless the user is admin

### Requirement: Audit Inventory from Existing Sources

The system MUST provide an audit inventory based on existing operational, closure, payment, expense, print, and user/session sources. It MUST identify coverage gaps and support the product goal of full audit over time. Desktop MUST surface existing-source audit limitations when supplied by the reporting dashboard payload. It MUST NOT introduce full event sourcing for 1.3.0. Affected repos: API, Desktop, Mobile.
(Previously: audit inventory required existing-source coverage and visible limitations, but did not require Desktop to surface supplied dashboard audit limitations.)

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
### Requirement: Explicit Non-Goals

Reporting and audit surfaces MUST be described as administrative financial-operational reporting. They MUST NOT claim support for formal accounting, taxes, commissions, payment-method accounting, machine-learning anomaly scoring, or auditor-role workflows in 1.3.0. Affected repos: API, Desktop, Mobile.
(Previously: excluded concepts were listed, but the administrative/non-accounting product framing was not explicit.)

#### Scenario: Non-goal fields are absent

- GIVEN an admin requests report metadata
- WHEN non-goals are represented
- THEN excluded capabilities are documented as unsupported
- AND no unsupported totals are returned as authoritative.

#### Scenario: Product framing is explicit

- GIVEN an admin opens reporting or audit surfaces
- WHEN explanatory labels are displayed
- THEN they describe administrative financial-operational reporting
- AND they do not describe formal accounting output.
### Requirement: Serious Audit Slice

The roadmap MUST include a first serious audit slice in 1.3.0 that supports administrative review of closures, payments, expenses, users/sessions, prints, and deterministic anomalies without assuming full event sourcing.

#### Scenario: Audit slice covers core sources

- GIVEN an admin reviews a journey
- WHEN audit data is requested
- THEN closure, payment, expense, user/session, print, and anomaly coverage are visible.

#### Scenario: Event sourcing is not required

- GIVEN the audit slice is implemented
- WHEN audit data is prepared
- THEN it uses available sources
- AND it does not require a new event stream.
