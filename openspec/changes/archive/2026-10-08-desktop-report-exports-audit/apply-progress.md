# Apply Progress: Desktop Closed Report Exports

## Change

- Name: `desktop-report-exports-audit`
- Work unit: `desktop-closed-report-export-enable`
- Mode: Strict TDD
- Delivery strategy: auto-chain
- PR boundary: Single low-risk stacked-to-main work unit under the 400-line review budget

## Completed Tasks

- [x] 1.1 Added initial-state assertions that closed-report PDF/XLSX controls are hidden or disabled and CSV is absent.
- [x] 1.2 Added local-calendar isolation coverage proving local reports cannot enable closed-report exports.
- [x] 1.3 Added valid API-backed closed-report coverage proving `closure_reference.id` enables PDF/XLSX controls.
- [x] 1.4 Added click-routing coverage proving PDF and XLSX call `exportar_reporte_cerrado(token, closure_id, format)`.
- [x] 1.5 Added success/error coverage for saved path/status rendering, actionable error detail, and retry preservation.
- [x] 2.1 Inspected controller export behavior; no controller hardening was required because existing error shape already preserves `ok`, `status`, and `api_error`.
- [x] 3.1 Added a closed-report exportability helper in `views/reportes.py`.
- [x] 3.2 Wired PDF/XLSX visibility and enabled state to API-backed closure state while keeping CSV absent.
- [x] 3.3 Routed PDF/XLSX clicks through the existing `exportar_reporte_cerrado` controller path with loaded closure id and format.
- [x] 3.4 Rendered saved path/status on success and actionable API/controller details on failure without clearing the loaded report.
- [x] 3.5 Left `controllers/reportes_controller.py` unchanged after confirming no result-shape hardening gap.
- [x] 4.1 Ran `python -m unittest tests.test_reportes_view`: 14 tests passed.
- [x] 4.2 Ran `python -m unittest tests.test_reportes_view tests.test_reportes_controller`: 40 tests passed.
- [x] 4.3 Ran `python -m unittest discover -s tests`: 412 tests passed.

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 1.1 | `tests/test_reportes_view.py` | Unit/PySide view | ✅ `python -m unittest tests.test_reportes_view tests.test_reportes_controller`: 38/38 passed | ✅ Initial-state expectations failed against deferred UI | ✅ `python -m unittest tests.test_reportes_view`: 14/14 passed | ✅ CSV absence plus hidden/disabled PDF/XLSX assertions | ✅ Shared API closed-report payload helper added |
| 1.2 | `tests/test_reportes_view.py` | Unit/PySide view | ✅ 38/38 baseline passed | ✅ Missing `_actualizar_estado_exportaciones_cerradas` helper failed local isolation test | ✅ `python -m unittest tests.test_reportes_view`: 14/14 passed | ✅ Local `source` payload with fabricated closure remains disabled while API payload enables | ✅ Exportability logic centralized |
| 1.3 | `tests/test_reportes_view.py` | Unit/PySide view | ✅ 38/38 baseline passed | ✅ Valid API-backed report did not make controls visible/enabled | ✅ `python -m unittest tests.test_reportes_view`: 14/14 passed | ✅ Missing closure reference remains disabled | ✅ Export state update called from closed-report render path |
| 1.4 | `tests/test_reportes_view.py` | Unit/PySide view | ✅ 38/38 baseline passed | ✅ Hidden controls did not route PDF/XLSX clicks to controller | ✅ `python -m unittest tests.test_reportes_view`: 14/14 passed | ✅ PDF and XLSX formats both asserted with same closure id | ✅ Existing `exportar_reporte_cerrado_api(format)` path preserved |
| 1.5 | `tests/test_reportes_view.py` | Unit/PySide view | ✅ 38/38 baseline passed | ✅ Error path did not render status/detail or preserve retry-enabled controls | ✅ `python -m unittest tests.test_reportes_view`: 14/14 passed | ✅ Success path renders saved XLSX path and error path renders API detail/status | ✅ Status rendering uses the existing closed export label |
| 2.1 | `tests/test_reportes_controller.py` | Unit/controller | ✅ 38/38 baseline passed | ➖ No RED test added because inspection found existing controller error shape already satisfies the task | ✅ `python -m unittest tests.test_reportes_view tests.test_reportes_controller`: 40/40 passed | ➖ Not applicable; optional task required no code change | ➖ None needed |
| 3.1-3.5 | `views/reportes.py` | Unit/PySide view | ✅ 38/38 baseline passed | ✅ Covered by tasks 1.1-1.5 RED tests | ✅ `python -m unittest tests.test_reportes_view`: 14/14 passed | ✅ API/local/no-closure/success/error paths covered | ✅ Helper isolates exportability state and keeps controller signature unchanged |

## Work Unit Evidence

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `python -m unittest tests.test_reportes_view`: 14 tests passed; `python -m unittest tests.test_reportes_view tests.test_reportes_controller`: 40 tests passed |
| Runtime harness command/scenario and exact result | N/A: PySide unit tests cover the view/controller boundary and this slice adds no new runtime integration surface |
| Rollback boundary | Revert `views/reportes.py`, `tests/test_reportes_view.py`, `openspec/changes/desktop-report-exports-audit/tasks.md`, and this apply-progress artifact |

## Verification

- ✅ `python -m unittest tests.test_reportes_view` — 14 tests passed.
- ✅ `python -m unittest tests.test_reportes_view tests.test_reportes_controller` — 40 tests passed.
- ✅ `python -m unittest discover -s tests` — 412 tests passed.

## Deviations

- `controllers/reportes_controller.py` was not changed because the existing controller export path already returns actionable `{ok: False, status, api_error}` details for API/content failures.

## Risks

- None identified.
