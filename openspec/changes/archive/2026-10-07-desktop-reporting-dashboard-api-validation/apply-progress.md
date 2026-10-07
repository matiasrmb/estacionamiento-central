# Apply Progress: Desktop Reporting Dashboard API Validation

## Mode

Strict TDD.

## Completed Tasks

- [x] 1.1 Update `tests/test_api_client_session.py` so dashboard request construction expects `GET /reporting/dashboard` with no query string or params.
- [x] 1.2 Keep or adjust `tests/test_api_client_session.py` metric catalog coverage for `GET /reporting/metric-catalog` and canonical metric keys.
- [x] 1.3 Update `tests/test_reportes_controller.py` mocked dashboard call assertions to fail if `period_id`, `state`, or other unowned args are passed.
- [x] 1.4 Extend `tests/test_reportes_controller.py` payload fixture/assertions to cover preservation of `period`, `catalog_version`, `filters`, `metrics`, and `pagination`.
- [x] 2.1 Modify `utils/api_client.py` so `obtener_dashboard_reporting(token)` calls `_request("GET", "/reporting/dashboard", token=token)` and removes unused query construction/imports.
- [x] 2.2 Modify `controllers/reportes_controller.py` so `obtener_resumen_dashboard_reportes` stops passing dashboard filters while preserving fallback and normalization behavior.
- [x] 2.3 Confirm `tests/test_reportes_view.py` still proves visible API metadata and compatible metric labels; adjust only assertions needed for canonical metadata.
- [x] 3.1 Run `python -m unittest tests.test_api_client_session tests.test_reportes_controller tests.test_reportes_view` and record results in apply evidence.
- [x] 3.2 Run `python -m unittest discover -s tests` before completion and record results.
- [x] 3.3 Verify no API, Mobile, Installer, operations drill-down, pagination UI, remote validation, or production-data probing changes were made.

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 1.1 | `tests/test_api_client_session.py` | Unit | ✅ `python -m unittest tests.test_api_client_session tests.test_reportes_controller tests.test_reportes_view` — 42 tests OK | ✅ Dashboard endpoint test expected `/reporting/dashboard` with no query string and failed against the old query URL | ✅ Focused command passed: 42 tests OK | ➖ Single endpoint-construction behavior | ✅ Removed unused query construction in adapter |
| 1.2 | `tests/test_api_client_session.py` | Unit | ✅ `python -m unittest tests.test_api_client_session tests.test_reportes_controller tests.test_reportes_view` — 42 tests OK | ✅ Metric catalog test asserted canonical metric keys through production adapter call | ✅ Focused command passed: 42 tests OK | ✅ Three canonical metric keys asserted | ➖ No production refactor needed |
| 1.3 | `tests/test_reportes_controller.py` | Unit | ✅ `python -m unittest tests.test_api_client_session tests.test_reportes_controller tests.test_reportes_view` — 42 tests OK | ✅ Controller tests expected dashboard API call with token only and failed against old `period_id`/`state` kwargs | ✅ Focused command passed: 42 tests OK | ✅ Two controller tests assert token-only dashboard API calls | ✅ Removed obsolete controller parameters |
| 1.4 | `tests/test_reportes_controller.py` | Unit | ✅ `python -m unittest tests.test_api_client_session tests.test_reportes_controller tests.test_reportes_view` — 42 tests OK | ✅ Payload compatibility assertions covered period, catalog version, filters, metrics, and pagination | ✅ Focused command passed: 42 tests OK | ✅ Metadata plus summary values cover non-empty payload preservation | ➖ Existing normalization already preserved metadata |
| 2.1 | `utils/api_client.py` | Unit | ✅ Covered by same baseline and RED adapter test | ✅ 1.1 RED test drove adapter change | ✅ Focused command passed: 42 tests OK | ➖ Single canonical request shape | ✅ Removed `urlencode` import and query construction |
| 2.2 | `controllers/reportes_controller.py` | Unit | ✅ Covered by same baseline and RED controller tests | ✅ 1.3 RED tests drove controller call path change | ✅ Focused command passed: 42 tests OK | ✅ Two controller call assertions cover the path | ✅ Removed obsolete default filter parameters |
| 2.3 | `tests/test_reportes_view.py` | UI unit | ✅ View tests included in baseline: 42 tests OK | ✅ Existing view assertions already proved visible API metadata and compatible labels | ✅ Focused command passed: 42 tests OK | ✅ View test asserts API source, catalog version, period, source state, and metric labels | ➖ No view changes needed |
| 3.1 | Focused command | Verification | ✅ Baseline available | N/A | ✅ `python -m unittest tests.test_api_client_session tests.test_reportes_controller tests.test_reportes_view` — 42 tests OK | N/A | N/A |
| 3.2 | Full suite | Verification | ✅ Focused command passed first | N/A | ✅ `python -m unittest discover -s tests` — 399 tests OK | N/A | N/A |
| 3.3 | Scope guard | Verification | ✅ Repository diff reviewed | N/A | ✅ Diff limited to Desktop adapter, controller, tests, and SDD artifacts | N/A | N/A |

## Work Unit Evidence

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `python -m unittest tests.test_api_client_session tests.test_reportes_controller tests.test_reportes_view`: Ran 42 tests in 0.289s, OK |
| Runtime harness command/scenario and exact result | N/A: mocked contract validation is the required gate; live API smoke is optional only when seeded auth exists and was not available/requested |
| Rollback boundary | Revert `utils/api_client.py`, `controllers/reportes_controller.py`, `tests/test_api_client_session.py`, `tests/test_reportes_controller.py`, and SDD progress/task artifacts for this change |

## Verification

- `python -m unittest tests.test_api_client_session tests.test_reportes_controller tests.test_reportes_view`: Ran 42 tests in 0.289s, OK.
- `python -m unittest discover -s tests`: Ran 399 tests in 5.341s, OK. The command also emitted existing warning/error log lines from mocked negative-path tests.

## Scope Guard

No API, Mobile, Installer, operations drill-down, pagination UI, remote validation, or production-data probing changes were made.
