# Tasks: Desktop Closed-Report Operation Drill-Down

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 300-430 |
| 400-line budget risk | Medium |
| Chained PRs recommended | No |
| Suggested split | Single PR; chain only if view diff grows over budget |
| Delivery strategy | auto-chain |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: stacked-to-main
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | API wrapper and controller model | PR 1 if chained | `python -m unittest tests.test_api_client_session tests.test_reportes_controller` | N/A; mocked unittest slice only | Revert `utils/api_client.py`, `controllers/reportes_controller.py`, and matching tests |
| 2 | Closed-report operations UI | PR 2 if chained | `python -m unittest tests.test_reportes_view` | N/A; PySide view tests cover behavior | Revert `views/reportes.py` and matching tests |

## Phase 1: RED API Client Tests

- [x] 1.1 Add `tests/test_api_client_session.py` coverage for `GET /reporting/reports/operations` with `period_id=closure:42`.
- [x] 1.2 Add `tests/test_api_client_session.py` coverage that only `category`, `operator`, `plate`, `sort`, `direction`, `limit`, and `offset` are sent.
- [x] 1.3 Add `tests/test_api_client_session.py` coverage that unsupported and blank params are omitted.

## Phase 2: RED Controller Tests

- [x] 2.1 Add `tests/test_reportes_controller.py` row normalization tests for category, amount, operator, plate, timestamp, filters, and `source=api`.
- [x] 2.2 Add `tests/test_reportes_controller.py` tests for empty/warning status while keeping closed-report data visible.
- [x] 2.3 Add `tests/test_reportes_controller.py` tests for explicit API error payloads and request failures.
- [x] 2.4 Add `tests/test_reportes_controller.py` tests for pagination metadata and no `obtener_reportes()` local fallback.

## Phase 3: RED View Tests

- [x] 3.1 Add `tests/test_reportes_view.py` coverage for operation rows rendering category, amount, operator, plate, and timestamp.
- [x] 3.2 Add `tests/test_reportes_view.py` coverage for operation filters, sorting controls, limit/offset navigation, and pagination status.
- [x] 3.3 Add `tests/test_reportes_view.py` coverage for empty, warning, and actionable error states without enabling exports.
- [x] 3.4 Add `tests/test_reportes_view.py` coverage that local calendar reports remain labeled legacy/local and separate.

## Phase 4: GREEN Implementation

- [x] 4.1 Add `ALLOWED_OPERATION_PARAMS` and `obtener_operaciones_reporte()` in `utils/api_client.py` with canonical path and query allow-listing.
- [x] 4.2 Add `obtener_operaciones_reporte_cerrado()` in `controllers/reportes_controller.py` to normalize rows, pagination, filters, warnings, status, and errors.
- [x] 4.3 Update `views/reportes.py` closed-report panel with operation controls, table, status, and pagination wiring.
- [x] 4.4 Preserve dashboard cards, hidden exports, local calendar query behavior, and no open/current operation rows in `views/reportes.py`.

## Phase 5: Verification

- [x] 5.1 Run `python -m unittest tests.test_api_client_session tests.test_reportes_controller tests.test_reportes_view` and fix failures.
- [x] 5.2 Run `python -m unittest discover -s tests` and record evidence for apply/verify.
