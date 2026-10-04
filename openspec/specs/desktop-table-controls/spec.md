# Desktop Table Controls Specification

## Purpose

Define Desktop-only table sorting and search behavior for relevant `QTableWidget` screens without changing API, Mobile, installer, or database contracts.

## Requirements

### Requirement: Typed Column Sorting

Affected repo: Desktop. Relevant Desktop tables MUST support column sorting using each column's semantic value, not its formatted display text. Supported value types MUST include dates/times, numbers, currency, identifiers, and text where present.

#### Scenario: Sort formatted values by semantic value

- GIVEN a relevant Desktop table displays formatted money, dates, or numbers
- WHEN the operator sorts that column ascending or descending
- THEN rows MUST be ordered by the underlying semantic value
- AND display formatting MUST remain unchanged

#### Scenario: Sort text consistently

- GIVEN a relevant Desktop table displays text values with mixed case or accents
- WHEN the operator sorts a text column
- THEN rows SHOULD sort predictably by normalized text

### Requirement: Protected Rows and Action Cells

Affected repo: Desktop. Table sorting MUST NOT move synthetic totals, summaries, placeholders, or action-only rows into data results. Action-widget columns MAY remain unsortable when sorting would not produce meaningful order.

#### Scenario: Total row remains protected

- GIVEN a table contains data rows and a synthetic total row
- WHEN the operator sorts any sortable column
- THEN the total row MUST remain outside the sorted data set

#### Scenario: Action column is safe

- GIVEN a table contains edit/delete/action controls
- WHEN sorting is enabled for the table
- THEN action controls MUST remain attached to their original records

### Requirement: Normalized Table Search

Affected repo: Desktop. Relevant Desktop tables MUST provide normalized text search where a search box exists or is introduced by this change. Search MUST filter visible data rows without corrupting typed sorting behavior.

#### Scenario: Search filters matching rows

- GIVEN a table contains visible rows with plate, user, or descriptive text
- WHEN the operator enters a search term
- THEN matching data rows MUST remain visible
- AND nonmatching data rows MUST be hidden

#### Scenario: Clearing search restores rows

- GIVEN a table has hidden rows due to search
- WHEN the operator clears the search term
- THEN all eligible data rows MUST be visible again
