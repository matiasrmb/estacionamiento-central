# Tasks: Desktop Closed Report Exports

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 140-220 |
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
| 1 | Enable valid closed-report PDF/XLSX exports in Desktop | PR 1 | `python -m unittest tests.test_reportes_view tests.test_reportes_controller` | N/A: PySide unit tests cover view/controller boundary; no new runtime integration surface | Revert `views/reportes.py`, optional controller hardening, and related tests |

## Phase 1: RED View Tests

- [x] 1.1 In `tests/test_reportes_view.py`, add failing initial-state assertions that PDF/XLSX are hidden or disabled and CSV is absent.
- [x] 1.2 In `tests/test_reportes_view.py`, add a failing local-calendar isolation test proving local reports cannot enable closed-report export controls.
- [x] 1.3 In `tests/test_reportes_view.py`, add a failing valid API-backed closed-report test where `closure_reference.id` makes PDF/XLSX visible and enabled.
- [x] 1.4 In `tests/test_reportes_view.py`, add failing click-routing tests proving PDF and XLSX call `exportar_reporte_cerrado(token, closure_id, format)`.
- [x] 1.5 In `tests/test_reportes_view.py`, add failing success/error tests for saved path/status rendering, actionable error detail, and preserved loaded report for retry.

## Phase 2: Optional RED Controller Regression

- [x] 2.1 Inspect `controllers/reportes_controller.py`; only if a hardening gap is found, add a focused failing regression in `tests/test_reportes_controller.py` for consistent `{ok: False, status, api_error}` export errors.

## Phase 3: GREEN Implementation

- [x] 3.1 In `views/reportes.py`, add a small helper that treats only `reporte_cerrado_actual` with `closure_reference.id` as exportable.
- [x] 3.2 In `views/reportes.py`, wire PDF/XLSX visibility and enabled state to the exportable helper, keeping CSV absent and local calendar reports isolated.
- [x] 3.3 In `views/reportes.py`, route PDF/XLSX clicks through `exportar_reporte_cerrado_api(format)` and call `exportar_reporte_cerrado` with the loaded closure id.
- [x] 3.4 In `views/reportes.py`, render saved path/status on success and actionable status/API detail on failure without clearing `reporte_cerrado_actual`.
- [x] 3.5 In `controllers/reportes_controller.py`, apply only tiny result-shape hardening if task 2.1 proves it necessary; preserve the existing signature.

## Phase 4: Verification

- [x] 4.1 Run `python -m unittest tests.test_reportes_view` and confirm the new view scenarios pass.
- [x] 4.2 Run `python -m unittest tests.test_reportes_view tests.test_reportes_controller` and confirm focused report coverage passes.
- [x] 4.3 Run `python -m unittest discover -s tests` and record any unrelated failures separately from this change.
