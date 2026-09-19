# Desktop Report Accounting Specification

## Purpose

Define Desktop Reports audit filters and dashboard-like accounting semantics while keeping API, Mobile, installer, and database changes out of scope unless later design proves a contract gap.

## Requirements

### Requirement: Audit Report Filters

Affected repo: Desktop. Reports MUST support audit-oriented filtering by license plate text, optional minimum and maximum time range, and user where the underlying category records expose meaningful user data.

#### Scenario: Filter by plate and time range

- GIVEN report rows exist for multiple plates and times
- WHEN the operator applies a plate text and min/max time filter
- THEN the report MUST include only rows matching the plate and time bounds

#### Scenario: User filter applies only where meaningful

- GIVEN report rows span categories with and without user metadata
- WHEN the operator applies a user filter
- THEN categories with user data MUST be filtered by that user
- AND categories without meaningful user data MUST use documented include/exclude semantics

### Requirement: Cash-Register Accounting Totals

Affected repo: Desktop. Reports MUST expose dashboard-like accounting totals with clear category semantics, including vehicle income, bathroom income, solo-wash income, monthly payments, night charges, expenses, gross total, and net total.

#### Scenario: Totals include all report categories

- GIVEN a report period contains income and expense categories
- WHEN the report is generated
- THEN totals MUST show each supported category separately
- AND gross and net totals MUST be calculated from those categories

#### Scenario: Empty period is explicit

- GIVEN no rows match the report filters
- WHEN the report is generated
- THEN category totals MUST be zero
- AND the report MUST clearly indicate no matching movements

### Requirement: Report Row Metadata and Sorting

Affected repo: Desktop. Report rows MUST include category metadata sufficient for audit review and MUST support typed sorting for displayed report columns.

#### Scenario: Rows identify category and user context

- GIVEN a report includes vehicle, bathroom, monthly, night, solo-wash, or expense rows
- WHEN rows are displayed
- THEN each row MUST expose a clear category label
- AND user/operator metadata MUST be shown when available

#### Scenario: Report table sorts typed columns

- GIVEN the report table displays dates, durations, currency, category, plate, or user columns
- WHEN the operator sorts a report column
- THEN rows MUST sort by semantic value while preserving formatted display text
