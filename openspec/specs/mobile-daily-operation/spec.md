# Delta for Mobile Daily Operation

## ADDED Requirements

### Requirement: Provide unified mobile operation screen

Affected repos: Mobile, API.
The mobile app MUST provide a unified daily-operation screen with plate search, newest-first operation list, and contextual actions for ingreso, salida, lavado, mensual, and baño where applicable.

#### Scenario: Plate search finds no active parking stay

- GIVEN the operator enters a plate with no active ingreso
- WHEN the unified search runs
- THEN the screen MUST offer ingreso creation
- AND it MAY offer eligible non-parking actions such as solo lavado

#### Scenario: Plate search finds an active parking stay

- GIVEN the operator enters a plate with an active ingreso
- WHEN the unified search runs
- THEN the screen MUST expose contextual actions for that record
- AND salida MUST remain blocked while the record is in active lavado

#### Scenario: Operation list loads

- GIVEN daily operations exist
- WHEN the unified screen loads
- THEN records MUST appear newest-first
- AND each record MUST expose actions appropriate to its state

### Requirement: Preserve Lavados/Baño module and add plate search

Affected repos: Mobile, API.
The mobile app MUST keep the existing Lavados/Baño module while adding plate search for active parking washes, solo lavado, and bathroom access.

#### Scenario: Operator uses Lavados/Baño after unification

- GIVEN the unified screen exists
- WHEN the operator opens Lavados/Baño
- THEN lavado and baño actions MUST remain available
- AND plate search MUST help locate active or eligible lavado records

## MODIFIED Requirements

## REMOVED Requirements
