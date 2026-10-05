# Apply Progress: Desktop Closed Reports and Exports

## Work Unit

- Change: `centro-inteligencia-reportes-auditoria-desktop-closed-reports-exports`
- Current slice: PR 2 closed-report view wiring
- Delivery mode: feature-branch-chain
- Boundary: cumulative PR 1 API/client/controller foundation plus PR 2 Reportes UI closed-report load/export wiring and view tests.
- Out of scope for this slice: API endpoint changes, Mobile, installer, database changes, historical plate/anomaly UI, and local fallback recomputation of closed-report totals.

## Completed Tasks

- [x] 1.1 RED: add `tests/test_api_client_session.py` cases for closed report path, PDF/XLSX export paths, and rejecting non-`pdf`/`xlsx` formats.
- [x] 1.2 GREEN: add `obtener_reporte_cerrado` and `exportar_reporte_cerrado` to `utils/api_client.py` using `_request` against `/reporting/reports/closed/{closure_id}` and `/reporting/exports/{closure_id}.{format}`.
- [x] 1.3 REFACTOR: keep API helpers thin and additive; do not change existing open-period report calls.
- [x] 2.1 RED: add `tests/test_reportes_controller.py` coverage for normal closed payload metadata, incomplete/warning payloads, API errors with no local fallback, PDF/XLSX export results, and export error preservation.
- [x] 2.2 GREEN: add closed-report normalization in `controllers/reportes_controller.py` for report id, period, closure reference, totals, capacity, completeness, discrepancy, source state, warnings, and errors.
- [x] 2.3 GREEN: add export handling in `controllers/reportes_controller.py`, persisting returned API content to `reportes/closed_<closure_id>.<format>` and surfacing content type/metadata.
- [x] 2.4 REFACTOR: isolate export content handling after confirming whether API `content` is text, base64, or binary-safe JSON text.
- [x] 4.1 Run focused client/controller tests: `python -m unittest tests.test_api_client_session tests.test_reportes_controller`.
- [x] 3.1 RED: add `tests/test_reportes_view.py` cases for operational closed-report controls, rendered metadata/source/completeness, warning labels, actionable error dialogs, PDF export, and XLSX replacing CSV copy.
- [x] 3.2 GREEN: update `views/reportes.py` to prompt for closure id, call controller closed-report retrieval, and render metadata, totals, source, completeness, warnings, and errors.
- [x] 3.3 GREEN: update `views/reportes.py` export controls to call PDF/XLSX controller export paths and remove CSV promise labels for this flow.
- [x] 3.4 REFACTOR: keep local open-period reporting UI behavior unchanged and avoid historical/anomaly UI expansion.
- [x] 4.2 Run focused view tests: `python -m unittest tests.test_reportes_view`.
- [x] 4.3 Run Desktop regression suite: `python -m unittest discover -s tests`.

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 1.1 | `tests/test_api_client_session.py` | Unit | ✅ 24/24 baseline focused tests passed | ✅ 4 API client tests written first and failed on missing helpers | ✅ Focused tests passed after API helpers | ✅ Closed report, PDF, XLSX, invalid format cases | ✅ Helpers kept thin and additive |
| 1.2 | `utils/api_client.py` | Unit | ✅ Covered by same baseline | ✅ Covered by 1.1 failing tests | ✅ `python -m unittest tests.test_api_client_session tests.test_reportes_controller` passed 34/34 | ✅ Endpoint and format branches covered | ✅ No existing open-period API calls changed |
| 1.3 | `utils/api_client.py` | Unit | ✅ Covered by same baseline | ✅ Existing dashboard tests protected open-period behavior | ✅ Focused tests passed 34/34 | ✅ Existing and new endpoint tests both passed | ✅ No further refactor needed |
| 2.1 | `tests/test_reportes_controller.py` | Unit | ✅ 24/24 baseline focused tests passed | ✅ 6 controller tests written first and failed on missing imports/helpers | ✅ Focused tests passed after controller implementation | ✅ Normal, incomplete, API error, PDF, XLSX, export error cases | ✅ Tests isolate API/filesystem with mocks and temp directories |
| 2.2 | `controllers/reportes_controller.py` | Unit | ✅ Covered by same baseline | ✅ Covered by 2.1 failing metadata/error tests | ✅ Focused tests passed 34/34 | ✅ Complete and incomplete report payloads covered | ✅ Normalization isolated in `_normalizar_reporte_cerrado` |
| 2.3 | `controllers/reportes_controller.py` | Unit | ✅ Covered by same baseline | ✅ Covered by 2.1 failing export tests | ✅ Focused tests passed 34/34 | ✅ PDF base64 and XLSX text content covered | ✅ File output isolated under configurable `output_dir`, defaulting to `reportes` |
| 2.4 | `controllers/reportes_controller.py` | Unit | ✅ Covered by same baseline | ✅ Ambiguous content handling covered by explicit base64 and text tests | ✅ Focused tests passed 34/34 | ✅ Encoding-aware and content-type fallback branches covered | ✅ Export content decoding isolated in helper functions |
| 4.1 | Focused unittest command | Unit | ✅ Previous baseline available | ✅ N/A verification task | ✅ `python -m unittest tests.test_api_client_session tests.test_reportes_controller` passed 34/34 | ➖ Command verification only | ➖ No code refactor |
| 3.1 | `tests/test_reportes_view.py` | View unit | ✅ `python -m unittest tests.test_reportes_view` passed 4/4 before edits | ✅ 3 view tests written first and failed on missing operational closed-report UI/imports | ✅ Focused view tests passed 6/6 after view wiring | ✅ Load/render, incomplete warning/API error, PDF/XLSX export success and failure paths covered | ✅ Tests patch controllers and dialogs only; no live API |
| 3.2 | `views/reportes.py` | View unit | ✅ Covered by 3.1 baseline | ✅ Covered by failing closed-report load/render tests | ✅ Focused view tests passed 6/6 | ✅ Complete and incomplete closed reports covered | ✅ Rendering isolated in `_renderizar_reporte_cerrado` helpers |
| 3.3 | `views/reportes.py` | View unit | ✅ Covered by 3.1 baseline | ✅ Covered by failing export tests requiring PDF/XLSX and no CSV label | ✅ Focused view tests passed 6/6 | ✅ PDF success, XLSX success, and API export error covered | ✅ Export action isolated in `exportar_reporte_cerrado_api` |
| 3.4 | `views/reportes.py` | View unit | ✅ Existing local report tests remain in focused view suite | ✅ Existing open-period assertions preserved while closed-report tests failed before implementation | ✅ Focused view tests passed 6/6 and full suite passed 397/397 | ✅ Open-period table/dashboard tests plus closed-report tests covered | ✅ Local open-period export and dashboard behavior unchanged |
| 4.2 | Focused unittest command | Unit | ✅ Previous baseline available | ✅ N/A verification task | ✅ `python -m unittest tests.test_reportes_view` passed 6/6 | ➖ Command verification only | ➖ No code refactor |
| 4.3 | Full Desktop unittest discovery | Unit | ✅ Focused suites green before full run | ✅ N/A verification task | ✅ `python -m unittest discover -s tests` passed 397/397 | ➖ Command verification only | ➖ No code refactor |

## Work Unit Evidence

| Evidence | Required value |
|---|---|
| Focused test command and exact result | PR 1: `python -m unittest tests.test_api_client_session tests.test_reportes_controller` → exit 0, Ran 34 tests, OK. PR 2: `python -m unittest tests.test_reportes_view` → exit 0, Ran 6 tests, OK |
| Runtime harness command/scenario and exact result | N/A: PR 2 has no live API/runtime boundary; offscreen PySide view tests patch controller API helpers and dialogs. Final regression: `python -m unittest discover -s tests` → exit 0, Ran 397 tests, OK |
| Rollback boundary | PR 2 rollback can revert `views/reportes.py`, `tests/test_reportes_view.py`, and this PR2 progress/tasks update without removing PR 1 API client/controller foundation |

## Deviations

- None from the assigned PR 2 boundary.
- Export content encoding remains API-shape sensitive; implementation supports explicit `content_encoding`/`encoding`, base64 for binary content types, bytes/bytearray, and UTF-8 text fallback.

## Remaining Tasks

- None. All apply tasks are complete for this change.
