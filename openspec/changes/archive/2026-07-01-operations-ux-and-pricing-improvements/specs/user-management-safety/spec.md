# Delta for User Management Safety

## ADDED Requirements

### Requirement: Delete users only when history is safe

Affected repos: Desktop, API.
The system MUST allow hard deletion only for users with no operational, audit, or historical activity; otherwise it MUST preserve history by deactivating or soft-deleting the user.

#### Scenario: User has no activity

- GIVEN a user has no referenced activity or audit history
- WHEN an authorized administrator deletes the user
- THEN the system MAY hard-delete the user
- AND the user MUST no longer appear as active or inactive in normal user lists

#### Scenario: User has historical activity

- GIVEN a user is referenced by ingresos, lavados, baños, cierres, asistencias, print jobs, or audit records
- WHEN an authorized administrator requests deletion
- THEN the system MUST NOT remove historical references
- AND it MUST deactivate or soft-delete the user with a clear result message

### Requirement: Preserve deactivate behavior

Affected repos: Desktop, API.
The system MUST keep existing user activation and deactivation behavior available independently from deletion.

#### Scenario: Administrator deactivates a user

- GIVEN an active user exists
- WHEN an authorized administrator deactivates the user
- THEN the account MUST become unable to operate normally
- AND historical activity MUST remain visible in reports and audits

## MODIFIED Requirements

## REMOVED Requirements
