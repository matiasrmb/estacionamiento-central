# Apply Progress: Centro de Inteligencia, Reportes y Auditoría

## Slice

- Work unit: PR1 API contracts, PR2 API reporting endpoints, closed replay and exports, PR3 Desktop API adapter with legacy fallback, PR4 Mobile API-backed reporting widgets/version alignment, and PR5 conditional migration decision/final verification
- Scope: tasks 1.1-1.3, 2.1-2.6, 3.1-3.2, 4.1-4.2, and 5.1
- Mode: Strict TDD
- Boundary: API repository read models/routes from PR1/PR2 plus Desktop report controller/API-client adapter and tests from PR3 plus Mobile reportes client/widget/version changes from PR4; PR5 only updates OpenSpec evidence and task state after proving no installer/migration work is needed.

## Completed Tasks

- [x] 1.1 API read-model tests for canonical metric catalog, signs, summary totals, 400-row completeness, and closure periods.
- [x] 1.2 API read-model implementation in `app/repositories/reporting_read_models.py`.
- [x] 1.3 Operator-session filter tests and implementation proving attendance sessions attribute rows without splitting operational periods.
- [x] 2.1 Endpoint tests for admin-only dashboard access, unsupported filter rejection, and no auditor-role access.
- [x] 2.2 Reporting endpoint module and `/api/v1/reporting/*` router wiring.
- [x] 2.3 Closed-report tests for closure reference, operation drill-down, no discrepancy, and delta discrepancy.
- [x] 2.4 Closed replay and audit inventory using existing source categories; no event sourcing or migration added.
- [x] 2.5 PDF/CSV export tests and renderer metadata for reproducible closed report content.
- [x] 2.6 Migration/installer decision resolved by evidence: no new schema metadata, indexes, or installer packaging are required for 1.3.0 reporting.
- [x] 3.1 Desktop adapter tests for canonical API labels, API outage fallback, and existing local report preservation.
- [x] 3.2 Desktop report adapter and API client helpers for `/api/v1/reporting/metric-catalog` and `/api/v1/reporting/dashboard` while preserving local reports.
- [x] 4.1 Mobile client/widget tests for canonical dashboard consumption, non-admin denial, and 1.3.0 labels.
- [x] 4.2 Mobile reportes client/screen and version metadata updated to consume `/reporting/metric-catalog` and `/reporting/dashboard`.
- [x] 5.1 Final API, Desktop, Mobile, and installer-if-needed verification completed.

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 1.1 | `tests/test_reporting_read_models.py` | Unit | N/A (new file) | ✅ Import failed before implementation: `ModuleNotFoundError` | ✅ `python -m unittest tests.test_reporting_read_models` passed | ✅ 3 behaviors covered before production implementation | ✅ Production code kept pure and small |
| 1.2 | `tests/test_reporting_read_models.py` | Unit | N/A (new file) | ✅ Tests referenced missing read-model module/functions | ✅ `python -m unittest tests.test_reporting_read_models` passed | ✅ Catalog, net, 400-row, closed, and open period cases | ✅ Shared helpers extracted for filtering, sums, and ISO serialization |
| 1.3 | `tests/test_reporting_read_models.py` | Unit | N/A (new file) | ✅ Operator-session test written before implementation | ✅ `python -m unittest tests.test_reporting_read_models` passed | ✅ Multi-session period plus session filter attribution case | ✅ Session filtering isolated from period boundary construction |
| 2.1 | `tests/test_reporting_endpoints.py` | Unit | ✅ `python -m unittest tests.test_reporting_read_models` passed, 4 tests | ✅ Import failed before `reporting` endpoint existed | ✅ `python -m unittest tests.test_reporting_endpoints` passed | ✅ Admin-only, unsupported filter, and auditor-denial cases | ✅ Endpoint validation kept explicit and small |
| 2.2 | `tests/test_reporting_endpoints.py` | Unit | ✅ Endpoint RED from 2.1 | ✅ Tests referenced missing endpoint/router implementation | ✅ `python -m unittest tests.test_reporting_endpoints` passed | ✅ Metric catalog plus dashboard route surface created | ✅ Router wiring limited to one include |
| 2.3 | `tests/test_reporting_closed_reports.py` | Unit | ✅ `python -m unittest tests.test_reporting_endpoints` passed, 3 tests | ✅ Import failed before closed-report functions existed | ✅ `python -m unittest tests.test_reporting_closed_reports` passed | ✅ Closure reference/drill-down, no-delta, delta, and inventory cases | ✅ Closed replay isolated in pure read-model helpers |
| 2.4 | `tests/test_reporting_closed_reports.py` | Unit | ✅ Closed RED from 2.3 | ✅ Tests referenced missing closed replay and audit inventory | ✅ `python -m unittest tests.test_reporting_closed_reports` passed | ✅ Existing-source inventory verifies no event sourcing | ✅ No schema or installer changes needed |
| 2.5 | `tests/test_reporting_exports.py` | Unit | ✅ `python -m unittest tests.test_reporting_closed_reports` passed, 3 tests | ✅ Import failed before export renderer existed | ✅ `python -m unittest tests.test_reporting_exports` passed | ✅ CSV metadata, stable PDF content, and unsupported format cases | ✅ Export rendering kept deterministic and metadata-driven |
| 3.1 | `tests/test_reportes_controller.py` | Unit | ✅ `python -m unittest tests.test_reportes_controller` passed, 11 tests | ✅ Tests failed before adapter/client symbols existed: 3 `AttributeError` failures | ✅ `python -m unittest tests.test_reportes_controller` passed, 14 tests | ✅ Canonical labels, API outage fallback, and local preservation covered | ✅ Adapter mapping extracted into `_normalizar_dashboard_reporting_api` |
| 3.2 | `tests/test_api_client_session.py`, `tests/test_reportes_controller.py` | Unit | ✅ Controller RED from 3.1 plus API-client RED | ✅ API-client tests failed before reporting helpers existed: 2 `AttributeError` failures | ✅ `python -m unittest tests.test_reportes_controller` and `python -m unittest tests.test_api_client_session` passed | ✅ Metric catalog and dashboard endpoint paths plus controller fallback path covered | ✅ API helpers kept as thin wrappers over existing `_request` |
| 4.1 | `test/features/admin/reportes/reporting_dashboard_test.dart` | Unit/widget | ✅ `flutter test test/features/admin/reportes` passed, 2 tests | ✅ New tests failed before `ReportesApi.dashboard()` existed | ✅ `flutter test test/features/admin/reportes/reporting_dashboard_test.dart` passed, 3 tests | ✅ Client canonical payload, non-admin denial, and admin widget labels covered | ✅ Test fixtures isolated with mocked Dio adapter and secure storage roles |
| 4.2 | `test/features/admin/reportes/reporting_dashboard_test.dart`, `test/features/admin/reportes/reportes_mensualidades_test.dart` | Unit/widget | ✅ RED from 4.1 plus existing reportes test safety net | ✅ Existing reportes test failed after switching to admin-only API-backed dashboard until fixture was aligned to `/reporting/*` | ✅ `flutter test test/features/admin/reportes` passed, 5 tests; `flutter test` passed, 65 tests; `flutter analyze` found no issues | ✅ Full mobile suite and analyzer covered reportes/version integration | ✅ `dart format` applied to modified Dart files |
| 2.6 | Existing API reporting tests and source review | Decision | ✅ PR1-PR4 tests already covered reporting metadata/export behavior | N/A — conditional decision only; no migration was needed | ✅ Source evidence and final API/Desktop/Mobile verification passed | ✅ Existing closure fields and in-payload export metadata satisfy the specs | ✅ Installer work avoided because there are no migration/config/package assets to ship |
| 5.1 | Cross-repo verification commands | Verification | ✅ PR1-PR4 focused and broader suites existed before final verification | N/A — verification-only task | ✅ Required API, Desktop, Mobile test/analyze commands passed; broader Desktop/Mobile suites also passed | ✅ Installer verification marked N/A by the 2.6 evidence decision | ✅ No code changes required |

## Work Unit Evidence

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `python -m unittest tests.test_reporting_read_models` → `Ran 4 tests in 0.001s` / `OK` |
| Focused test command and exact result | `python -m unittest tests.test_reporting_endpoints` → `Ran 3 tests in 0.002s` / `OK`; `python -m unittest tests.test_reporting_closed_reports` → `Ran 3 tests in 0.000s` / `OK`; `python -m unittest tests.test_reporting_exports` → `Ran 3 tests in 0.000s` / `OK`; PR1 safety `python -m unittest tests.test_reporting_read_models` → `Ran 4 tests in 0.001s` / `OK` |
| Focused test command and exact result | `python -m unittest tests.test_reportes_controller` → `Ran 14 tests in 0.008s` / `OK`; supporting API client command `python -m unittest tests.test_api_client_session` → `Ran 8 tests in 0.018s` / `OK` |
| Full Desktop regression command and exact result | `python -m unittest discover -s tests` → `Ran 374 tests in 4.092s` / `OK` |
| Focused test command and exact result | `flutter test test/features/admin/reportes` → `All tests passed!` / 5 tests |
| Full Mobile regression command and exact result | `flutter test` → `All tests passed!` / 65 tests |
| Mobile analyzer command and exact result | `flutter analyze` → `No issues found!` |
| Final API verification command and exact result | `python -m unittest tests.test_reporting_read_models tests.test_reporting_endpoints tests.test_reporting_closed_reports tests.test_reporting_exports` → `Ran 17 tests in 0.004s` / `OK` |
| Final Desktop verification command and exact result | `python -m unittest tests.test_reportes_controller tests.test_api_client_session` → `Ran 22 tests in 0.043s` / `OK` |
| Final Desktop broader regression command and exact result | `python -m unittest discover -s tests` → `Ran 374 tests in 4.566s` / `OK`; emitted expected test-harness warning/error log lines without failing the suite. |
| Final Mobile focused verification command and exact result | `flutter test test/features/admin/reportes` → `All tests passed!` / 5 tests; dependency resolution reported 33 newer incompatible package versions. |
| Final Mobile analyzer command and exact result | `flutter analyze` → `No issues found! (ran in 6.5s)`; dependency resolution reported 33 newer incompatible package versions. |
| Final Mobile broader regression command and exact result | `flutter test` → `All tests passed!` / 65 tests; dependency resolution reported 33 newer incompatible package versions. |
| Installer verification command and exact result | N/A — task 2.6 evidence shows no migration metadata, indexes, config, template, or installer packaging asset was added or required, so `ISCC EstacionamientoCentral.iss` is not applicable for this slice. |
| Runtime harness command/scenario and exact result | N/A — no live DB/server credentials were required or authorized for this apply slice; route/runtime boundary is covered by endpoint functions and router wiring tests, with full runtime verification deferred to SDD verify. |
| Runtime harness command/scenario and exact result | Desktop runtime simulated by controller/unit harness with mocked API outage and local DB cursor fallback; no live Desktop UI launch was required or authorized for this apply slice. |
| Runtime harness command/scenario and exact result | Mobile runtime boundary simulated with widget tests using mocked Dio fixtures and secure-storage roles; no live API/server/device runtime was required or authorized for this apply slice. |
| Rollback boundary | Revert `estacionamiento-central-api/tests/test_reporting_endpoints.py`, `tests/test_reporting_closed_reports.py`, `tests/test_reporting_exports.py`, `app/api/v1/endpoints/reporting.py`, PR2 additions in `app/repositories/reporting_read_models.py`, `app/api/v1/router.py`, Desktop PR3 changes in `controllers/reportes_controller.py`, `utils/api_client.py`, `tests/test_reportes_controller.py`, `tests/test_api_client_session.py`, Mobile PR4 changes in `lib/features/admin/reportes/data/reportes_api.dart`, `lib/features/admin/reportes/presentation/reportes_admin_screen.dart`, `test/features/admin/reportes/reporting_dashboard_test.dart`, `test/features/admin/reportes/reportes_mensualidades_test.dart`, `pubspec.yaml`, this apply-progress file, and tasks checkbox updates for 2.1-4.2. |

## Verification

```text
python -m unittest tests.test_reporting_read_models
....
----------------------------------------------------------------------
Ran 4 tests in 0.001s

OK

python -m unittest tests.test_reporting_endpoints
...
----------------------------------------------------------------------
Ran 3 tests in 0.002s

OK

python -m unittest tests.test_reporting_closed_reports
...
----------------------------------------------------------------------
Ran 3 tests in 0.000s

OK

python -m unittest tests.test_reporting_exports
...
----------------------------------------------------------------------
Ran 3 tests in 0.000s

OK

python -m unittest tests.test_reportes_controller
..............
----------------------------------------------------------------------
Ran 14 tests in 0.008s

OK

python -m unittest tests.test_api_client_session
........
----------------------------------------------------------------------
Ran 8 tests in 0.018s

OK

python -m unittest discover -s tests
...............................................................................................................................................................slow_operation area=desktop operation=table_refresh duration_ms=1031.24 threshold_ms=1000 function=obtener_vehiculos_activos
.......................................................................................................................................................................................................................
----------------------------------------------------------------------
Ran 374 tests in 4.092s

OK

flutter test test/features/admin/reportes
All tests passed! (5 tests)

flutter test
All tests passed! (65 tests)

flutter analyze
No issues found! (ran in 57.8s)

Final PR5 verification:

python -m unittest tests.test_reporting_read_models tests.test_reporting_endpoints tests.test_reporting_closed_reports tests.test_reporting_exports
.................
----------------------------------------------------------------------
Ran 17 tests in 0.004s

OK

python -m unittest tests.test_reportes_controller tests.test_api_client_session
......................
----------------------------------------------------------------------
Ran 22 tests in 0.043s

OK

python -m unittest discover -s tests
......................................................................................................................................................................................................................................................................................................................................................................................
----------------------------------------------------------------------
Ran 374 tests in 4.566s

OK

flutter test test/features/admin/reportes
All tests passed! (5 tests)

flutter analyze
No issues found! (ran in 6.5s)

flutter test
All tests passed! (65 tests)
```

## Deviations

The initial PR2 endpoint implementation was reopened after validation found it passed `None` period bounds to the dashboard read model and fabricated closed-report data. The correction adds repository-backed reads: open dashboard totals come from pending operational sources with the latest closure as the boundary; closed reports load the persisted closure snapshot and operational-source totals, exposing a discrepancy when they differ. Task 2.6 is complete by evidence: no schema migration or installer packaging is required for tasks 2.1-2.5 or final PR5 verification.

PR3 kept Desktop reports hybrid by adding a new dashboard adapter entrypoint instead of replacing `obtener_reportes`. Existing local reports do not call the reporting API, while API-backed dashboard summaries consume canonical catalog labels and fall back to local report totals on API unavailability when a local date range is available.

PR4 replaced the Mobile reportes screen's legacy movement-list dashboard with an admin-only API-backed operational reporting dashboard. Mobile now consumes `/reporting/metric-catalog` and `/reporting/dashboard`, maps canonical metrics to 1.3.0 mobile labels, displays catalog/version state, and keeps the older `movimientos` client method only for compatibility with any remaining callers.

## PR2 Correction Evidence

| Evidence | Result |
|---|---|
| Root cause | `/dashboard` passed `None` period boundaries and `/reports/closed/{id}` constructed `utcnow()` placeholder closures. |
| Fix | Added `app/repositories/reporting_repo.py`; reporting routes now delegate to persisted-source repository queries. |
| Endpoint tests | Added successful dashboard and closed-report delegation coverage plus missing-closure `404` coverage. |
| Repository test | Added open-dashboard test proving the latest closure, not an operator session, sets the open period boundary. |
| Focused verification | `python -m unittest tests.test_reporting_read_models tests.test_reporting_endpoints tests.test_reporting_closed_reports tests.test_reporting_exports` → `Ran 17 tests in 0.004s` / `OK`. |
| Rollback boundary | Revert `app/repositories/reporting_repo.py`, PR2 reporting-route/test changes, and this correction evidence; no schema, installer, Desktop, or Mobile changes are involved. |

## Migration / Installer Decision Evidence

| Evidence | Result |
|---|---|
| Schema metadata requirement | No new persisted columns are required. `reporting_read_models.py` emits `catalog_version`, `source_state`, and export `template_version` as deterministic read-model/export payload metadata. |
| Closure snapshot requirement | Existing `cierres_diarios` fields are sufficient for closure reference replay: `reporting_repo.py` reads `id_cierre`, `fecha_inicio`, `fecha_cierre`, `total_general`, `total_mensualidades_monto`, `total_gastos`, and `total_neto`. |
| Existing-source audit requirement | `build_audit_inventory()` reports existing source categories and explicitly sets `requires_event_sourcing` to `False`; no event stream or new audit table is required. |
| Index requirement | Final focused and broader verification passed without adding indexes. The 1.3.0 implementation uses existing closure/date/source lookups and summary-level payloads; no new query-plan evidence required installer/schema changes for this work unit. |
| Installer packaging requirement | No migration, config, export template file, or packaged asset was created. Installer verification is therefore N/A for PR5; no `EstacionamientoCentral.iss` change or `ISCC` run is required. |

## PR5 Final Verification Evidence

| Evidence | Result |
|---|---|
| Focused API command | `python -m unittest tests.test_reporting_read_models tests.test_reporting_endpoints tests.test_reporting_closed_reports tests.test_reporting_exports` → `Ran 17 tests in 0.004s` / `OK`. |
| Focused Desktop command | `python -m unittest tests.test_reportes_controller tests.test_api_client_session` → `Ran 22 tests in 0.043s` / `OK`. |
| Desktop broader suite | `python -m unittest discover -s tests` → `Ran 374 tests in 4.566s` / `OK`; suite emitted expected harness diagnostic lines after the OK result. |
| Focused Mobile command | `flutter test test/features/admin/reportes` → `All tests passed!` / 5 tests. |
| Mobile analyzer | `flutter analyze` → `No issues found! (ran in 6.5s)`. |
| Mobile broader suite | `flutter test` → `All tests passed!` / 65 tests. |
| Runtime harness | N/A — this final slice changed only OpenSpec planning evidence and task state; repo runtime boundaries were verified by unit/widget/analyzer suites. |
| Rollback boundary | Revert only this OpenSpec `tasks.md` checkbox update and the PR5 sections in `apply-progress.md`; no API, Desktop, Mobile, installer, schema, branch, tag, PR, or version files were changed. |

## Remaining Tasks

- None for apply. The change is ready for independent SDD verification/archive routing.
