# Delta for Reproducible Closed Reports

## MODIFIED Requirements

### Requirement: Exact Closed Report Reproduction

Closed reports MUST be exactly reproducible from their persisted closure reference and reproducibility metadata. Desktop closure references MUST preserve charged solo lavado totals and item inclusion exactly as saved. Affected repos: API, Desktop, Mobile.
(Previously: closed reports had to replay persisted closure references, but solo lavado closure totals were not explicit.)

#### Scenario: Replaying a closed report

- GIVEN a report was closed with a stored reference
- WHEN the same closed report is requested later
- THEN totals, period bounds, and exported values match the original closure reference exactly

#### Scenario: Later operational edits do not rewrite closure reference

- GIVEN a closed period has a stored reference
- WHEN operational rows are corrected later
- THEN the closure reference remains unchanged
- AND discrepancies are shown separately

#### Scenario: Charged solo lavado is replayed from closure reference

- GIVEN Desktop saved a closure containing charged solo lavado income
- WHEN that closed report is requested later
- THEN solo-lavado totals and general totals MUST match the saved closure reference
- AND the solo lavado MUST NOT be recounted from a later open-period calculation
