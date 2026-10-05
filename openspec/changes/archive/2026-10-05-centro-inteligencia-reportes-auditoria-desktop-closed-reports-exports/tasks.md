# Tasks: Desktop Closed Reports and Exports

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 450-650 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 API/client + controller exports -> PR 2 closed-report view wiring |
| Delivery strategy | ask-on-risk |
| Chain strategy | feature-branch-chain |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | API helpers and controller normalization/export persistence | PR 1 | `python -m unittest tests.test_api_client_session tests.test_reportes_controller` | N/A: no live API in Desktop tests | Revert `utils/api_client.py`, controller export/closed helpers, and matching tests |
| 2 | Reportes UI closed-report load and PDF/XLSX actions | PR 2 | `python -m unittest tests.test_reportes_view` | N/A: offscreen PySide controller-patched tests only | Revert `views/reportes.py` closed-report UI and matching tests |

## Phase 1: API Client RED/GREEN/REFACTOR

- [x] 1.1 RED: add `tests/test_api_client_session.py` cases for closed report path, PDF/XLSX export paths, and rejecting non-`pdf`/`xlsx` formats.
- [x] 1.2 GREEN: add `obtener_reporte_cerrado` and `exportar_reporte_cerrado` to `utils/api_client.py` using `_request` against `/reporting/reports/closed/{closure_id}` and `/reporting/exports/{closure_id}.{format}`.
- [x] 1.3 REFACTOR: keep API helpers thin and additive; do not change existing open-period report calls.

## Phase 2: Controller RED/GREEN/REFACTOR

- [x] 2.1 RED: add `tests/test_reportes_controller.py` coverage for normal closed payload metadata, incomplete/warning payloads, API errors with no local fallback, PDF/XLSX export results, and export error preservation.
- [x] 2.2 GREEN: add closed-report normalization in `controllers/reportes_controller.py` for report id, period, closure reference, totals, capacity, completeness, discrepancy, source state, warnings, and errors.
- [x] 2.3 GREEN: add export handling in `controllers/reportes_controller.py`, persisting returned API content to `reportes/closed_<closure_id>.<format>` and surfacing content type/metadata.
- [x] 2.4 REFACTOR: isolate export content handling after confirming whether API `content` is text, base64, or binary-safe JSON text.

## Phase 3: View RED/GREEN/REFACTOR

- [x] 3.1 RED: add `tests/test_reportes_view.py` cases for operational closed-report controls, rendered metadata/source/completeness, warning labels, actionable error dialogs, PDF export, and XLSX replacing CSV copy.
- [x] 3.2 GREEN: update `views/reportes.py` to prompt for closure id, call controller closed-report retrieval, and render metadata, totals, source, completeness, warnings, and errors.
- [x] 3.3 GREEN: update `views/reportes.py` export controls to call PDF/XLSX controller export paths and remove CSV promise labels for this flow.
- [x] 3.4 REFACTOR: keep local open-period reporting UI behavior unchanged and avoid historical/anomaly UI expansion.

## Phase 4: Verification

- [x] 4.1 Run focused client/controller tests: `python -m unittest tests.test_api_client_session tests.test_reportes_controller`.
- [x] 4.2 Run focused view tests: `python -m unittest tests.test_reportes_view`.
- [x] 4.3 Run Desktop regression suite: `python -m unittest discover -s tests`.
