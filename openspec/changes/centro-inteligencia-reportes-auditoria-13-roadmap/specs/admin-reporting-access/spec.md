# Delta for Admin Reporting Access

## MODIFIED Requirements

### Requirement: Audit Inventory from Existing Sources

The system MUST provide 1.3.0 audit inventory/readiness based on existing operational, closure, payment, expense, print, and user/session sources. It MUST NOT introduce full event sourcing or a transversal high-level before/after event log in immediate 1.3.0 core. Affected repos: API, Desktop, Mobile.
(Previously: excluded full event sourcing, but did not explicitly defer the transversal event log to 1.3.x.)

#### Scenario: Existing-source inventory

- GIVEN an admin requests audit inventory for a period
- WHEN inventory is generated
- THEN it identifies available existing sources and their coverage
- AND it marks unavailable before/after history explicitly

#### Scenario: Event sourcing is excluded

- GIVEN audit inventory is requested
- WHEN the system prepares audit data
- THEN it does not require new append-only event streams for 1.3.0

#### Scenario: Transversal event log is deferred

- GIVEN a high-level audit event log is requested for 1.3.0
- WHEN scope is evaluated
- THEN it is marked deferred to 1.3.x
- AND 1.3.0 exposes readiness/inventory only

## ADDED Requirements

### Requirement: Future Critical Event Audit Metadata

The future 1.3.x audit event log MUST capture before/after values, user, origin, reason, and session/device where applicable for critical events. 1.3.0 MUST only preserve readiness boundaries for this future requirement. Affected repos: API, Desktop, Mobile.

#### Scenario: Future metadata contract is explicit

- GIVEN a critical-event audit design is planned for 1.3.x
- WHEN required metadata is defined
- THEN before/after, user, origin, reason, and applicable session/device are required

#### Scenario: Immediate core does not implement event log

- GIVEN 1.3.0 audit readiness is implemented
- WHEN critical-event audit capability is checked
- THEN the transversal event log is not exposed as a 1.3.0 feature
