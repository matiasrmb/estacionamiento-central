# Delta for Admin Reporting Access

## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Audit Inventory from Existing Sources

The system MUST provide an audit inventory based on existing operational, closure, payment, expense, print, and user/session sources. It MUST identify coverage gaps and support the product goal of full audit over time. It MUST NOT introduce full event sourcing for 1.3.0. Affected repos: API, Desktop, Mobile.
(Previously: audit inventory listed existing sources and excluded event sourcing, but did not require an initial serious audit slice or full-audit trajectory.)

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
