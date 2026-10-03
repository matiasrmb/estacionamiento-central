# Delta for Canonical Reporting API

## ADDED Requirements

### Requirement: Desktop Canonical Dashboard Normalization

Desktop MUST normalize dashboard responses into a view model that preserves canonical reporting fields and exposes fallback metadata. Local fallback summaries MUST be marked incomplete and local. Affected repos: Desktop.

#### Scenario: API dashboard fields are preserved

- GIVEN the API returns metric labels, period state, source state, completeness, and capacity metadata
- WHEN Desktop normalizes the dashboard response
- THEN the normalized result preserves those fields for the view
- AND metric labels remain the canonical API labels

#### Scenario: Local fallback is marked incomplete

- GIVEN the API dashboard cannot be obtained and Desktop uses a local fallback summary
- WHEN Desktop normalizes the fallback summary
- THEN the normalized result sets completeness to incomplete
- AND source state identifies the data as local fallback

#### Scenario: Unit tests remain payload-driven

- GIVEN Desktop controller tests provide canonical dashboard payloads directly
- WHEN the tests verify normalization behavior
- THEN they do not require a live API containing PR #80, #81, or #82 fields
- AND live runtime verification may still list that API chain as a prerequisite
