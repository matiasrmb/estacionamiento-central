# Tasks: Desktop Report Audit Inventory Panel

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 300-390 |
| 400-line budget risk | Medium |
| Chained PRs recommended | No |
| Suggested split | Single PR: client, controller, compact view, tests |
| Delivery strategy | auto-chain |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Deliver Desktop audit inventory panel from API contract only | PR 1 | `python -m unittest tests.test_api_client_session tests.test_reportes_controller tests.test_reportes_view` | `python -m unittest tests.test_reportes_view` | Revert `utils/api_client.py`, `controllers/reportes_controller.py`, `views/reportes.py`, and related tests |

## Phase 1: RED Contract Tests

- [x] 1.1 Add failing endpoint tests in `tests/test_api_client_session.py` for `GET /reporting/audit-inventory` with no query and with only non-blank `period_id`.
- [x] 1.2 Add failing controller tests in `tests/test_reportes_controller.py` for success normalization of validated fields and missing-field/API-error unavailable states.
- [x] 1.3 Add failing no-fallback assertion in `tests/test_reportes_controller.py` proving inventory errors never call local report/dashboard fallback helpers.
- [x] 1.4 Add failing view tests in `tests/test_reportes_view.py` for compact readiness rendering, limitations, error/unavailable text, and existing flow preservation.

## Phase 2: Client and Controller GREEN

- [x] 2.1 Add `obtener_inventario_auditoria_reporting(token, period_id=None)` in `utils/api_client.py`, encoding only non-blank `period_id`.
- [x] 2.2 Import the client wrapper in `controllers/reportes_controller.py` and add `obtener_inventario_auditoria(token, period_id=None)`.
- [x] 2.3 Add private normalization helpers in `controllers/reportes_controller.py` for `period_id`, `coverage[].state`, source groups, affected scopes, history, booleans, and unsupported behaviors.
- [x] 2.4 Return explicit `ok: False`, `source: "api"`, `source_state: "unavailable"|"api_error"`, empty lists, and no fabricated fields for invalid/error payloads.

## Phase 3: Compact View GREEN

- [x] 3.1 Import `obtener_inventario_auditoria` in `views/reportes.py` and load inventory during the existing dashboard refresh path without new API/database dependencies.
- [x] 3.2 Add compact label-based inventory/readiness rendering in `views/reportes.py`, reusing metadata style and avoiding totals/counts/freshness timestamps.
- [x] 3.3 Preserve dashboard, closed reports, operations, exports, and local table behavior in `views/reportes.py` while rendering inventory unavailable/error states safely.

## Phase 4: Verification and Cleanup

- [x] 4.1 Run focused tests: `python -m unittest tests.test_api_client_session tests.test_reportes_controller tests.test_reportes_view`.
- [x] 4.2 Run final verification: `python -m unittest discover -s tests`.
- [x] 4.3 Mark completed tasks in `openspec/changes/desktop-report-audit-inventory-panel/tasks.md` only after verification evidence exists.
