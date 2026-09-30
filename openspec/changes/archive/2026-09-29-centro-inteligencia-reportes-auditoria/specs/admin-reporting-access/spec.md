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

The system MUST provide an audit inventory based on existing operational, closure, payment, expense, print, and user/session sources. It MUST NOT introduce full event sourcing for 1.3.0. Affected repos: API, Desktop, Mobile.

#### Scenario: Existing-source inventory

- GIVEN an admin requests audit inventory for a period
- WHEN inventory is generated
- THEN it identifies available existing sources and their coverage
- AND it marks unavailable before/after history explicitly

#### Scenario: Event sourcing is excluded

- GIVEN audit inventory is requested
- WHEN the system prepares audit data
- THEN it does not require new append-only event streams for 1.3.0

### Requirement: Explicit Non-Goals

Reporting and audit surfaces MUST NOT claim support for formal accounting, taxes, commissions, payment-method accounting, machine-learning anomaly scoring, or auditor-role workflows in 1.3.0. Affected repos: API, Desktop, Mobile.

#### Scenario: Non-goal fields are absent

- GIVEN an admin requests report metadata
- WHEN non-goals are represented
- THEN excluded capabilities are documented as unsupported
- AND no unsupported totals are returned as if authoritative
