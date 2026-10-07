# Tasks: Desktop Reporting Dashboard API Validation

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 80-160 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | auto-chain |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: stacked-to-main
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Align Desktop dashboard request contract and mocked compatibility tests | PR 1 | `python -m unittest tests.test_api_client_session tests.test_reportes_controller tests.test_reportes_view` | N/A: mocked contract validation is the required gate; live API smoke is optional only when seeded auth exists | Revert `utils/api_client.py`, `controllers/reportes_controller.py`, and related test assertions |

## Phase 1: RED Contract Tests

- [x] 1.1 Update `tests/test_api_client_session.py` so dashboard request construction expects `GET /reporting/dashboard` with no query string or params.
- [x] 1.2 Keep or adjust `tests/test_api_client_session.py` metric catalog coverage for `GET /reporting/metric-catalog` and canonical metric keys.
- [x] 1.3 Update `tests/test_reportes_controller.py` mocked dashboard call assertions to fail if `period_id`, `state`, or other unowned args are passed.
- [x] 1.4 Extend `tests/test_reportes_controller.py` payload fixture/assertions to cover preservation of `period`, `catalog_version`, `filters`, `metrics`, and `pagination`.

## Phase 2: GREEN Adapter Alignment

- [x] 2.1 Modify `utils/api_client.py` so `obtener_dashboard_reporting(token)` calls `_request("GET", "/reporting/dashboard", token=token)` and removes unused query construction/imports.
- [x] 2.2 Modify `controllers/reportes_controller.py` so `obtener_resumen_dashboard_reportes` stops passing dashboard filters while preserving fallback and normalization behavior.
- [x] 2.3 Confirm `tests/test_reportes_view.py` still proves visible API metadata and compatible metric labels; adjust only assertions needed for canonical metadata.

## Phase 3: Verification and Scope Guard

- [x] 3.1 Run `python -m unittest tests.test_api_client_session tests.test_reportes_controller tests.test_reportes_view` and record results in apply evidence.
- [x] 3.2 Run `python -m unittest discover -s tests` before completion and record results.
- [x] 3.3 Verify no API, Mobile, Installer, operations drill-down, pagination UI, remote validation, or production-data probing changes were made.
