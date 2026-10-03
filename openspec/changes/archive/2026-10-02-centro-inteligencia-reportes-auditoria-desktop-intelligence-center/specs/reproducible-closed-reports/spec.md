# Delta for Reproducible Closed Reports

## ADDED Requirements

### Requirement: Desktop Closed and Export Roadmap Boundaries

Desktop MUST expose closed-report and export entry points as roadmap boundaries only in this slice. It MUST NOT implement API-backed closed-report retrieval or export generation flows here. Affected repos: Desktop.

#### Scenario: Closed report boundary is visible but non-calling

- GIVEN an admin opens Desktop reporting
- WHEN the closed-report action is shown
- THEN Desktop labels it as a future API-backed capability
- AND activating it does not call a closed-report API endpoint

#### Scenario: Export boundary is visible but non-generating

- GIVEN an admin opens Desktop reporting
- WHEN the export action is shown
- THEN Desktop labels PDF/CSV export as a future API-backed capability
- AND activating it does not generate PDF or CSV output

#### Scenario: Boundary copy states prerequisites

- GIVEN Desktop renders closed/export roadmap boundaries
- WHEN the user reads the boundary text
- THEN it states that API-backed closed/export support is required before the flow becomes operational
