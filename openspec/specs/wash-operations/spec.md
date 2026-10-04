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
The system MUST support lavado for a plate without a prior parking ingreso and MUST record start time, end time, duration, status, operator, and historical wash price. Desktop MUST account only charged solo lavados immediately; active and converted solo lavados MUST remain outside immediate closure/report income until their qualifying charge event.
(Previously: finalized solo lavado revenue was required in cierre/caja/reports, but Desktop exclusion and one-time closure semantics were not explicit.)

#### Scenario: Solo lavado is charged and leaves

- GIVEN a solo lavado is active for a plate
- WHEN the operator finalizes it as charge-and-leave
- THEN the system MUST charge the wash amount immediately
- AND Desktop cierre, caja, and reports MUST include the finalized solo lavado revenue once

#### Scenario: Solo lavado continues as parking stay

- GIVEN a solo lavado is active for a plate
- WHEN the operator finalizes it as continue-as-stay
- THEN the system MUST create a normal parking ingreso starting at the wash end time
- AND the wash MUST NOT be charged until final parking salida

#### Scenario: Active solo lavado is not immediate income

- GIVEN a solo lavado has status `ACTIVO`
- WHEN Desktop calculates closure or report income
- THEN its wash amount MUST NOT be included

#### Scenario: Converted solo lavado is deferred

- GIVEN a solo lavado has status `CONVERTIDO_ESTADIA`
- WHEN Desktop calculates closure or report income before parking salida
- THEN its wash amount MUST NOT be included
### Requirement: Report wash and stay ticket details

Affected repos: Desktop, API, Mobile.
Tickets for a wash followed by parking stay MUST show wash start, wash end, wash duration, wash amount, stay start, stay end, stay duration, stay amount, and total.

#### Scenario: Wash then stay ticket is generated

- GIVEN a solo lavado was converted into a parking stay
- WHEN final parking salida is confirmed
- THEN the ticket MUST show separate wash and stay detail sections
- AND the total MUST equal wash amount plus stay amount

### Requirement: Close charged solo lavados once

Affected repos: Desktop. Desktop MUST include each charged solo lavado in exactly one daily closure and MUST mark it as closed when that closure is saved.

#### Scenario: Charged solo lavado is closed once

- GIVEN a solo lavado has status `FINALIZADO_COBRADO` and is not closed
- WHEN Desktop saves a daily closure
- THEN the closure MUST include its amount in solo-lavado and general totals
- AND the solo lavado MUST be marked closed for future closures

#### Scenario: Later closure excludes already closed solo lavado

- GIVEN a charged solo lavado was included in a previous closure
- WHEN Desktop saves a later closure
- THEN that solo lavado MUST NOT contribute to any total again

### Requirement: Maintain additive closure state support

Affected repos: Desktop. Desktop MUST tolerate existing databases by ensuring required solo-lavado closure state is available additively and idempotently before closure accounting uses it.

#### Scenario: Existing database receives closure support

- GIVEN a Desktop database lacks solo-lavado closure state
- WHEN Desktop prepares closure accounting
- THEN the required state support MUST exist without destructive data changes

#### Scenario: Schema support can run repeatedly

- GIVEN solo-lavado closure state already exists
- WHEN Desktop prepares closure accounting again
- THEN the preparation MUST succeed without duplicating or resetting state

## MODIFIED Requirements

## REMOVED Requirements
