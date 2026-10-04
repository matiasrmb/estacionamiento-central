# Delta for Reproducible Closed Reports

## MODIFIED Requirements

### Requirement: PDF and CSV Export Reproducibility

Closed-period PDF and XLSX exports MUST include closure-linked reproducibility metadata sufficient to reproduce the exact report. CSV MUST NOT be the required future export format for this roadmap. Affected repos: API, Desktop, Mobile, Installer if packaging assets are required.
(Previously: required export formats were PDF and CSV with general reproducibility metadata.)

#### Scenario: Export includes reproducibility metadata

- GIVEN an admin exports a closed report
- WHEN PDF or XLSX is generated
- THEN it includes report id, period bounds, closure reference id, generated timestamp, metric catalog version, filters, source state, and export template version

#### Scenario: Same closed export content

- GIVEN the same closed report and same export format are requested twice
- WHEN no export template version changes
- THEN report data content is identical

#### Scenario: CSV is not a required future export

- GIVEN the future export roadmap is evaluated
- WHEN required formats are listed
- THEN PDF and XLSX are required
- AND CSV is not required by this roadmap
