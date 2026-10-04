# Tasks: Desktop Table Audit Search and Reports Accounting

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 650-900 authored lines |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | Single PR with maintainer-approved size:exception |
| Delivery strategy | exception-ok |
| Chain strategy | size-exception |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: size-exception
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Typed sort/search table foundation | PR 1 | `python -m unittest tests.test_table_filters` | Desktop offscreen `QTableWidget` scenarios | `utils/table_filters.py`, affected non-report views |
| 2 | Reports accounting, dropdown user filter, export adaptation | PR 2 | `python -m unittest tests.test_reportes_controller tests.test_accounting_report_contracts` | Open Reports, filter by date/time/plate/user dropdown | `controllers/reportes_controller.py`, `controllers/accounting_contracts.py`, `views/reportes.py` |

## Phase 1: Table Controls RED Tests

- [x] 1.1 Add failing typed value sort tests in `tests/test_table_filters.py` for money, dates/times, numbers, IDs, and normalized text.
- [x] 1.2 Add failing protected-row/action-cell/search tests in `tests/test_table_filters.py` for totals, widgets, match, and clear scenarios.

## Phase 2: Table Controls GREEN Implementation

- [x] 2.1 Extend `utils/table_filters.py` with typed `Qt.UserRole` item helpers, normalized text keys, and backward-compatible filtering.
- [x] 2.2 Wire typed sorting/search in `views/registro.py`, preserving the appended total row outside sorted data.
- [x] 2.3 Wire typed sorting/search in `views/asistencias.py`, `views/gastos.py`, `views/mensuales.py`, and `views/usuarios.py`, keeping action columns safe.
- [x] 2.4 Refactor `utils/table_filters.py` and affected views only after RED tests pass.

## Phase 3: Reports RED Tests

- [x] 3.1 Add failing filter tests in `tests/test_reportes_controller.py` for plate, min/max time, and user semantics across categories.
- [x] 3.2 Add failing metadata/no-result tests in `tests/test_reportes_controller.py` for category labels, user context, and explicit empty payloads.
- [x] 3.3 Add failing totals tests in `tests/test_accounting_report_contracts.py` for bathrooms, solo wash, monthly payments, nights, expenses, gross, net, and movement count.

## Phase 4: Reports GREEN Implementation

- [x] 4.1 Update `controllers/accounting_contracts.py` to build Desktop report totals with gross, expenses, net, and full movement count.
- [x] 4.2 Update `controllers/reportes_controller.py` to return `{items, totals}` with category rows, effective event times, plate/time/user filters, and documented exclusion semantics.
- [x] 4.3 Update `views/reportes.py` with time filters, category/user columns, accounting cards, typed sortable rows, and existing-user dropdown filter; no free-text user input.
- [x] 4.4 Adapt `views/reportes.py` PDF/export calls to consume the structured report payload without recalculating totals.

## Phase 5: Verification

- [x] 5.1 Run `python -m unittest tests.test_table_filters` after Phase 2 and fix only table-control regressions.
- [x] 5.2 Run `python -m unittest tests.test_reportes_controller tests.test_accounting_report_contracts` after Phase 4 and fix only report regressions.
- [x] 5.3 Run `python -m unittest discover -s tests` before handoff and document any unrelated pre-existing failures.
