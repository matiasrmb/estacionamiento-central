# Delta for Wash Operations

## ADDED Requirements

### Requirement: Preserve parking-linked washing

Affected repos: Desktop, API, Mobile.
The system MUST keep the current parking ingreso plus lavado flow available without changing parking salida billing semantics.

#### Scenario: Existing ingreso starts and finishes a wash

- GIVEN an active parking ingreso that is not already in wash
- WHEN an operator starts and finalizes a lavado for that ingreso
- THEN parking salida MUST include the wash amount
- AND parking time MUST exclude the wash interval according to existing behavior

### Requirement: Support solo lavado lifecycle

Affected repos: Desktop, API.
The system MUST support lavado for a plate without a prior parking ingreso and MUST record start time, end time, duration, status, operator, and historical wash price.

#### Scenario: Solo lavado is charged and leaves

- GIVEN a solo lavado is active for a plate
- WHEN the operator finalizes it as charge-and-leave
- THEN the system MUST charge the wash amount immediately
- AND cierre, caja, and reports MUST include the finalized solo lavado revenue

#### Scenario: Solo lavado continues as parking stay

- GIVEN a solo lavado is active for a plate
- WHEN the operator finalizes it as continue-as-stay
- THEN the system MUST create a normal parking ingreso starting at the wash end time
- AND the wash MUST NOT be charged until final parking salida

### Requirement: Report wash and stay ticket details

Affected repos: Desktop, API, Mobile.
Tickets for a wash followed by parking stay MUST show wash start, wash end, wash duration, wash amount, stay start, stay end, stay duration, stay amount, and total.

#### Scenario: Wash then stay ticket is generated

- GIVEN a solo lavado was converted into a parking stay
- WHEN final parking salida is confirmed
- THEN the ticket MUST show separate wash and stay detail sections
- AND the total MUST equal wash amount plus stay amount

## MODIFIED Requirements

## REMOVED Requirements
