# Apply Progress: Desktop Table Audit Search and Reports Accounting

## Change

- Name: `desktop-table-audit-search-and-reports-accounting`
- Mode: Strict TDD
- Artifact purpose: remediation of missing process evidence for an already implemented and functionally verified change.
- Evidence source: reconstructed from the completed `tasks.md`, the failed Strict TDD `verify-report.md`, current test files, and prior recorded phase evidence.

## Reconstruction Notice

This artifact reconstructs process evidence from the completed change and the current verification evidence. It is not a new implementation pass and does not claim that code or tests were changed during this remediation. The implementation is already complete; this file supplies the formal `TDD Cycle Evidence` table required by Strict TDD verification.

## Task Completion

| Metric | Value |
|--------|-------|
| Total tasks | 16 |
| Completed tasks | 16 |
| Incomplete tasks | 0 |
| Source of completion state | `openspec/changes/desktop-table-audit-search-and-reports-accounting/tasks.md` |

### Completed Tasks

- [x] 1.1 Add failing typed value sort tests in `tests/test_table_filters.py` for money, dates/times, numbers, IDs, and normalized text.
- [x] 1.2 Add failing protected-row/action-cell/search tests in `tests/test_table_filters.py` for totals, widgets, match, and clear scenarios.
- [x] 2.1 Extend `utils/table_filters.py` with typed `Qt.UserRole` item helpers, normalized text keys, and backward-compatible filtering.
- [x] 2.2 Wire typed sorting/search in `views/registro.py`, preserving the appended total row outside sorted data.
- [x] 2.3 Wire typed sorting/search in `views/asistencias.py`, `views/gastos.py`, `views/mensuales.py`, and `views/usuarios.py`, keeping action columns safe.
- [x] 2.4 Refactor `utils/table_filters.py` and affected views only after RED tests pass.
- [x] 3.1 Add failing filter tests in `tests/test_reportes_controller.py` for plate, min/max time, and user semantics across categories.
- [x] 3.2 Add failing metadata/no-result tests in `tests/test_reportes_controller.py` for category labels, user context, and explicit empty payloads.
- [x] 3.3 Add failing totals tests in `tests/test_accounting_report_contracts.py` for bathrooms, solo wash, monthly payments, nights, expenses, gross, net, and movement count.
- [x] 4.1 Update `controllers/accounting_contracts.py` to build Desktop report totals with gross, expenses, net, and full movement count.
- [x] 4.2 Update `controllers/reportes_controller.py` to return `{items, totals}` with category rows, effective event times, plate/time/user filters, and documented exclusion semantics.
- [x] 4.3 Update `views/reportes.py` with time filters, category/user columns, accounting cards, typed sortable rows, and existing-user dropdown filter; no free-text user input.
- [x] 4.4 Adapt `views/reportes.py` PDF/export calls to consume the structured report payload without recalculating totals.
- [x] 5.1 Run `python -m unittest tests.test_table_filters` after Phase 2 and fix only table-control regressions.
- [x] 5.2 Run `python -m unittest tests.test_reportes_controller tests.test_accounting_report_contracts` after Phase 4 and fix only report regressions.
- [x] 5.3 Run `python -m unittest discover -s tests` before handoff and document any unrelated pre-existing failures.

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 1.1 | `tests/test_table_filters.py` | Unit / PySide offscreen widget | Existing table-filter tests were the baseline for shared helper behavior. | RED table-control tests were added first for formatted money, dates/times, numbers, IDs, and normalized text sorting; prior recorded evidence notes failures because `create_sortable_item` and typed sort support were not implemented yet. | GREEN confirmed by `python -m unittest tests.test_table_filters` passing in verify with 14 tests. | Covered multiple value types: money, dates/times, numbers, IDs, and normalized text. | Table helper cleanup was completed in task 2.4 with the focused table suite green. |
| 1.2 | `tests/test_table_filters.py` | Unit / PySide offscreen widget | Existing normalized filter behavior was preserved as the baseline. | RED table-control tests were added first for protected total rows, action widgets, normalized search, action-column exclusion, and clear behavior; prior recorded evidence notes expected failures on missing `protected_rows` and `action_columns` support. | GREEN confirmed by `python -m unittest tests.test_table_filters` passing in verify with 14 tests. | Covered protected rows, action widgets, matching, action-column exclusion, clearing search, and header-click sort behavior. | Table helper and view wiring refactors were validated with the focused table suite green. |
| 2.1 | `tests/test_table_filters.py` | Unit / PySide offscreen widget | Safety net inherited from RED tasks 1.1 and 1.2. | RED already existed before implementation through tasks 1.1 and 1.2 for missing typed item helpers, normalized text keys, and compatible filtering options. | GREEN implementation added typed `Qt.UserRole` sort/search helpers and passed `python -m unittest tests.test_table_filters`. | Triangulated by the same table suite across semantic numeric, date/time, ID, text, protected-row, and action-column paths. | Refactor completed under task 2.4; focused tests remained green. |
| 2.2 | `tests/test_table_filters.py` plus `views/registro.py` behavior | Unit / PySide offscreen widget | Safety net inherited from table-control RED coverage. | RED already existed for the total-row protection behavior before `views/registro.py` wiring. | GREEN implementation preserved the appended total row outside sorted data; verify confirms `python -m unittest tests.test_table_filters` passed. | Triangulated with total-row sorting plus other typed data-row sorting scenarios. | View wiring retained existing refresh behavior and relied on shared helpers. |
| 2.3 | `tests/test_table_filters.py` plus affected views | Unit / PySide offscreen widget | Safety net inherited from table-control RED coverage. | RED already existed for action-widget preservation and search/sort safety before wiring `views/asistencias.py`, `views/gastos.py`, `views/mensuales.py`, and `views/usuarios.py`. | GREEN implementation kept action columns safe and passed the focused table suite. | Triangulated with action-widget attachment, action-column search exclusion, and normalized matching scenarios. | Refactor centralized table behavior in `utils/table_filters.py` instead of duplicating per-view logic. |
| 2.4 | `tests/test_table_filters.py` | Unit / PySide offscreen widget | Safety net: focused table suite after Phase 2. | RED was the accumulated table-control RED suite from tasks 1.1 and 1.2. | GREEN confirmed by `python -m unittest tests.test_table_filters` passing in verify with 14 tests. | Triangulation remained the full table-control suite. | Refactor completed with shared helper cleanup and affected-view usage while preserving passing tests. |
| 3.1 | `tests/test_reportes_controller.py` | Unit / mocked controller cursor | Existing report-controller tests were the baseline for local report behavior. | RED report filter tests were added first for plate, min/max time, and user semantics across categories; prior recorded evidence notes planned failures because `obtener_reportes` lacked `hora_inicio`, `hora_fin`, `usuario`, and structured filtering support. | GREEN confirmed by `python -m unittest tests.test_reportes_controller tests.test_accounting_report_contracts` passing in verify with 25 tests. | Covered plate, time bounds, user filtering, category-specific include/exclude behavior, and existing report modes. | Controller query/filter refactor was validated by the focused report suite. |
| 3.2 | `tests/test_reportes_controller.py` | Unit / mocked controller cursor | Existing report-controller tests were the baseline. | RED metadata/no-result tests were added first for category labels, user context, and explicit empty payloads. | GREEN confirmed by the focused reports command passing with 25 tests. | Triangulated with non-empty category/user metadata and explicit empty-payload behavior. | Structured payload behavior was centralized so UI/export consumers do not recalculate totals. |
| 3.3 | `tests/test_accounting_report_contracts.py` | Unit / pure accounting contract | Existing accounting contract tests were the baseline for prior dashboard/report total semantics. | RED totals tests were added first for bathrooms, solo wash, monthly payments, nights, expenses, gross, net, and movement count; prior recorded evidence notes failures because `build_report_totals` lacked those full report semantics. | GREEN confirmed by the focused reports/accounting command passing with 25 tests. | Triangulated by category-specific accounting contract tests and the aggregate movement-count test. | Totals logic was kept in `controllers/accounting_contracts.py` rather than recalculated in the view. |
| 4.1 | `tests/test_accounting_report_contracts.py` | Unit / pure accounting contract | Safety net inherited from RED accounting contract tests. | RED already existed from task 3.3 for missing gross, expense, net, and full movement-count semantics. | GREEN implementation passed `python -m unittest tests.test_reportes_controller tests.test_accounting_report_contracts`. | Triangulated across bathrooms, solo wash, monthly payments, nights, expenses, gross, net, and movement count. | Refactor kept report totals in the accounting contract layer. |
| 4.2 | `tests/test_reportes_controller.py` | Unit / mocked controller cursor | Safety net inherited from RED report-controller tests. | RED already existed from tasks 3.1 and 3.2 for structured `{items, totals}`, category rows, event times, and filter semantics. | GREEN implementation passed the focused report/controller command. | Triangulated across plate/time/user filtering, explicit empty payloads, category labels, and user context. | Controller behavior was structured without changing API, Mobile, installer, or DB contracts. |
| 4.3 | `tests/test_reportes_controller.py`, `tests/test_table_filters.py` | Unit / controller and PySide table helper coverage | Safety net inherited from report and table RED suites. | RED already existed for report user/time semantics and typed report/table sorting before `views/reportes.py` wiring. | GREEN confirmed by both focused commands passing in verify. | Triangulated with controller filter tests and typed table helper tests used by the report table. | UI uses existing-user dropdown and shared typed table helpers; no free-text user input was introduced. |
| 4.4 | `tests/test_reportes_controller.py` | Unit / mocked controller-export behavior | Existing PDF/export report tests were the baseline. | RED coverage existed for structured payload totals and export/report total consistency before adapting PDF/export callers. | GREEN confirmed by focused reports/accounting command passing in verify. | Triangulated by report totals, category payloads, and export-related controller tests. | Export/PDF callers consume the structured payload rather than recalculating totals. |
| 5.1 | `tests/test_table_filters.py` | Unit / PySide offscreen widget | N/A (verification task). | RED source was the Phase 1 table-control tests. | `python -m unittest tests.test_table_filters` passed in verify. | 14 table tests exercised typed sorting, protected rows, action cells, and normalized search. | No additional refactor during remediation. |
| 5.2 | `tests/test_reportes_controller.py`, `tests/test_accounting_report_contracts.py` | Unit / mocked controller cursor and pure contract | N/A (verification task). | RED source was the Phase 3 report/accounting tests. | `python -m unittest tests.test_reportes_controller tests.test_accounting_report_contracts` passed in verify. | 25 focused report/accounting tests exercised filters, metadata, totals, and export-related behavior. | No additional refactor during remediation. |
| 5.3 | All Desktop unittest tests | Unit suite | N/A (handoff verification task). | RED sources were the completed table-control and report/accounting RED suites. | `python -m unittest discover -s tests` passed in verify. | Full suite ran 380 tests, covering the completed change plus regression safety. | No additional refactor during remediation. |

## Verification Commands Observed

| Command | Exit Code | Observed Result | Output Hash | Evidence Source |
|---------|-----------|-----------------|-------------|-----------------|
| `python -m unittest tests.test_table_filters` | 0 | Ran 14 tests in 0.020s; OK. | `sha256:5be74f1d9d36e9c176bd4964a6fb59731b3bd8590c73d28fba492bac5fb260cb` | `verify-report.md` |
| `python -m unittest tests.test_reportes_controller tests.test_accounting_report_contracts` | 0 | Ran 25 tests in 0.010s; OK. | `sha256:dd1fc661cde864c330a026631874344dd16b5151c3de86e03622387cec262cb9` | `verify-report.md` |
| `python -m unittest discover -s tests` | 0 | Ran 380 tests in 2.068s; OK. Non-failing warning/error log lines were printed by existing tests. | `sha256:29bccce06957ed7114e656104a370284fecd1daa4e841c739c6503083d858d95` | `verify-report.md` |

## Work Unit Evidence

| Work Unit | Focused Test Command and Exact Result | Runtime Harness Command / Scenario and Exact Result | Rollback Boundary |
|-----------|----------------------------------------|-----------------------------------------------------|-------------------|
| Typed sort/search table foundation | `python -m unittest tests.test_table_filters` → exit code 0; Ran 14 tests in 0.020s; OK. | PySide offscreen `QTableWidget` scenarios in `tests/test_table_filters.py` cover typed sorting, normalized search, protected rows, and action widgets; exit code 0 under the focused command. | `utils/table_filters.py`, `views/registro.py`, `views/asistencias.py`, `views/gastos.py`, `views/mensuales.py`, `views/usuarios.py`, `tests/test_table_filters.py`. |
| Reports accounting, dropdown user filter, export adaptation | `python -m unittest tests.test_reportes_controller tests.test_accounting_report_contracts` → exit code 0; Ran 25 tests in 0.010s; OK. | Runtime UI harness: N/A — project has no Desktop integration/E2E runner configured; controller/report behavior is verified through mocked cursor unit tests and report accounting contract tests. Manual scenario represented: Open Reports, filter by date/time/plate/user dropdown, inspect category/user rows and accounting totals. | `controllers/reportes_controller.py`, `controllers/accounting_contracts.py`, `views/reportes.py`, `tests/test_reportes_controller.py`, `tests/test_accounting_report_contracts.py`. |
| Full Desktop regression handoff | `python -m unittest discover -s tests` → exit code 0; Ran 380 tests in 2.068s; OK. | Runtime harness: N/A — no configured Desktop integration/E2E runner; full unittest suite is the configured verify boundary. | Entire Desktop change set for `desktop-table-audit-search-and-reports-accounting`. |

## Deviations and Issues

- No application code was changed during this remediation.
- No new test execution was performed during this remediation; exact command results are copied from `verify-report.md`.
- The previous Strict TDD failure was a process-evidence gap only: functional verification passed, all 16 tasks were complete, and all focused/full unittest commands passed.
- Full unittest output included non-failing warning/error log lines from existing tests, but the command exit code was 0.

## Status

The change has 16/16 tasks complete. This apply-progress artifact supplies the missing formal Strict TDD evidence table and is ready for independent SDD verification.
