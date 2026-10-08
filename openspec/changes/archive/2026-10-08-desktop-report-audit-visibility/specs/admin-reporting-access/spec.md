# Delta for Admin Reporting Access

## MODIFIED Requirements

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
