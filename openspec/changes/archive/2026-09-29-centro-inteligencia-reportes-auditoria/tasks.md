# Tasks: Centro de Inteligencia, Reportes y Auditoría

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 900-1,400 authored lines across API, Desktop, Mobile, exports, tests |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR1 API contracts/periods → PR2 closed reports/exports/access → PR3 Desktop adapter → PR4 Mobile/version → PR5 installer packaging if needed |
| Delivery strategy | ask-on-risk |
| Chain strategy | stacked-to-main |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Canonical API read models and closure-to-closure periods | PR1 | `python -m unittest tests.test_reporting_read_models tests.test_reporting_endpoints` | `uvicorn app.main:app --reload`; call `/api/v1/reporting/dashboard` | Revert `app/api/v1/endpoints/reporting.py`, `app/repositories/reporting_read_models.py`, router/tests |
| 2 | Admin-only closed replay, discrepancies, PDF/CSV metadata | PR2 | `python -m unittest tests.test_reporting_closed_reports tests.test_reporting_exports` | Admin/non-admin API calls to closed report/export endpoints | Revert reporting closed/export routes, metadata migration if added |
| 3 | Desktop API adapter with legacy fallback | PR3 | `python -m unittest tests.test_reportes_controller` | Open Desktop reports as admin with mocked API outage | Revert reportes controller/adapter changes only |
| 4 | Mobile API-backed report widgets and 1.3.0 alignment | PR4 | `flutter test test/features/admin/reportes` | Run admin reports screen against mocked Dio fixtures | Revert reportes feature/version files only |
| 5 | Installer packages migrations/config only if required | PR5 | Manual: `ISCC EstacionamientoCentral.iss` | Install package validates migration assets present | Revert installer script/package entries |

## Phase 1: API RED Contracts and Period Model

- [x] 1.1 API: add failing tests in `estacionamiento-central-api/tests/test_reporting_read_models.py`; dep: approved specs; verify `python -m unittest tests.test_reporting_read_models`; rollback: test file only.
- [x] 1.2 API: create `estacionamiento-central-api/app/repositories/reporting_read_models.py` for metric catalog, signs, 400-row summaries, and closure-to-closure periods; dep: 1.1; verify same; rollback: repository file.
- [x] 1.3 API: add operator-session filter tests for `asistencias` as attribution only, not period boundary; dep: 1.2; verify same; rollback: tests/read-model filter changes.

## Phase 2: API Routes, Access, Closed Replay, Exports

- [x] 2.1 API: add failing endpoint tests in `tests/test_reporting_endpoints.py` for admin-only dashboard, unsupported filters, no auditor role; dep: Phase 1; verify `python -m unittest tests.test_reporting_endpoints`; rollback: endpoint tests.
- [x] 2.2 API: create `app/api/v1/endpoints/reporting.py` and wire `app/api/v1/router.py`; dep: 2.1; verify endpoint command; rollback: route/router files.
- [x] 2.3 API: add closed-report tests for closure reference, operation drill-down, discrepancy `none`/delta behavior; dep: 2.2; verify `python -m unittest tests.test_reporting_closed_reports`; rollback: closed tests/read-model methods.
- [x] 2.4 API: implement closed replay and audit inventory using existing sources; dep: 2.3; verify closed tests; rollback: reporting read-model closed paths.
- [x] 2.5 API: add PDF/CSV export tests for reproducibility metadata and stable closed content; dep: 2.4; verify `python -m unittest tests.test_reporting_exports`; rollback: export tests/renderers.
- [x] 2.6 API/Installer: add migration metadata/indexes only if `cierres_diarios` cannot store catalog/source/export metadata; dep: 2.5; verify schema migration tests or manual `ISCC`; rollback: migration and installer entries.

## Phase 3: Desktop Parity Adapter

- [x] 3.1 Desktop: add failing adapter tests in `estacionamiento-central/tests/test_reportes_controller.py` for canonical labels, API fallback, and local report preservation; dep: PR1 API contract; verify `python -m unittest tests.test_reportes_controller`; rollback: tests only.
- [x] 3.2 Desktop: update `controllers/reportes_controller.py` and API client area to consume `/api/v1/reporting/*` while preserving current reports; dep: 3.1; verify same plus `python -m unittest discover -s tests`; rollback: controller/client changes.

## Phase 4: Mobile Consumption and Version Alignment

- [x] 4.1 Mobile: add failing `test/features/admin/reportes` client/widget tests for canonical dashboard, admin denial, and 1.3.0 labels; dep: API contract; verify `flutter test test/features/admin/reportes`; rollback: tests only.
- [x] 4.2 Mobile: update `lib/features/admin/reportes/...` and version metadata to consume API-backed resources; dep: 4.1; verify `flutter test` and `flutter analyze`; rollback: reportes/version files.

## Phase 5: Final Cross-Repo Verification

- [x] 5.1 Run API, Desktop, Mobile, and installer-if-needed verification commands; dep: Phases 1-4; evidence: command logs and manual installer note; rollback: revert failed PR slice.
