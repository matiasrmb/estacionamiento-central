# Design: Desktop Closed Reports and Exports

## Technical Approach

Implement the Desktop side only. Keep local open-period reporting unchanged, and replace the two roadmap-boundary buttons in `views/reportes.py` with API-backed closed-report actions. `utils/api_client.py` will add thin authenticated calls for the archived API contracts: `GET /reporting/reports/closed/{closure_id}` and `GET /reporting/exports/{closure_id}.{format}`. `controllers/reportes_controller.py` will normalize closed-report and export payloads into view-friendly dictionaries, preserving API source, completeness, reproducibility metadata, warnings, and errors without fabricating local fallback totals.

## Architecture Decisions

| Decision | Choice | Alternatives considered | Rationale |
|---|---|---|---|
| API contract source | Consume the existing reporting endpoints through additive `api_client` helpers. | Add Desktop DB queries or new API endpoints. | The API archived contracts already define admin-only closed reports and PDF/XLSX exports; Desktop must remain a consumer. |
| Closed report selection | Prompt for a closure/report id from the existing reports window, then render metadata in a new closed-report panel. | Add a separate window or browse historical reports. | The spec requires selecting a closed report, not historical discovery UI; this keeps scope small. |
| Export handling | Request API export JSON and persist returned `content` to `reportes/closed_<closure_id>.<format>` with the API `content_type`/metadata surfaced to the user. | Reuse local `exportar_pdf` or open CSV behavior. | Local PDF generation would recompute client semantics; CSV is explicitly out of scope for Desktop. |
| Failure behavior | Show actionable API errors and keep closed-report totals empty/stale rather than local-fallback recomputation. | Fallback to `obtener_reportes`. | The spec forbids fabricated closed-report totals from Desktop local data. |

## Data Flow

```text
ReportesWindow button/input
  -> controllers.reportes_controller.obtener_reporte_cerrado(token, closure_id)
  -> utils.api_client.obtener_reporte_cerrado(token, closure_id)
  -> API /reporting/reports/closed/{closure_id}
  -> normalized closed payload -> metadata/cards/warnings in ReportesWindow

ReportesWindow export PDF/XLSX
  -> controllers.reportes_controller.exportar_reporte_cerrado(token, closure_id, format)
  -> utils.api_client.exportar_reporte_cerrado(token, closure_id, format)
  -> API /reporting/exports/{closure_id}.{format}
  -> write returned content under reportes/ and show result/error
```

## File Changes

| File | Action | Description |
|---|---|---|
| `utils/api_client.py` | Modify | Add `obtener_reporte_cerrado(token, closure_id)` and `exportar_reporte_cerrado(token, closure_id, formato)` using `_request`; validate Desktop only calls `pdf` or `xlsx`. |
| `controllers/reportes_controller.py` | Modify | Add normalization helpers for report id, period, closure reference, `operation_totals`, `capacity`, `historical_completeness`, `discrepancy`, `source_state`, and export metadata/file persistence. |
| `views/reportes.py` | Modify | Replace roadmap messages/buttons with operational closed-report load, PDF export, and XLSX export controls; render API warnings and errors. |
| `tests/test_api_client_session.py` | Modify | Assert exact endpoint paths for closed report and exports. |
| `tests/test_reportes_controller.py` | Modify | Cover normalization, incomplete/warning payloads, no local fallback on API failure, export formats, and file result handling. |
| `tests/test_reportes_view.py` | Modify | Cover button labels/actions, API-backed rendering, warning labels, PDF/XLSX export calls, and error dialogs. |

## Interfaces / Contracts

Desktop assumes API base URL already includes `/api/v1`.

```python
GET /reporting/reports/closed/{closure_id}
GET /reporting/exports/{closure_id}.pdf
GET /reporting/exports/{closure_id}.xlsx
```

Closed report payload fields consumed: `report_id`, `period`, `catalog_version`, `closure_reference`, `operation_totals`, `capacity`, `historical_completeness`, `discrepancy`, `source_state`. Export payload fields consumed: `format`, `content_type`, `metadata`, `content`.

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit | API client path construction and format validation | Patch `_request` in `tests/test_api_client_session.py`. |
| Unit | Controller normalization and error behavior | Patch API helpers and filesystem calls in `tests/test_reportes_controller.py`; strict TDD RED first. |
| View | Operational UI state and dialogs | Offscreen PySide tests in `tests/test_reportes_view.py` with controller patches. |
| E2E | Not applicable | No live API or database changes in this Desktop design. |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary is introduced. File writing is limited to API-returned export content under the existing `reportes/` output directory.

## Migration / Rollout

No migration required. Roll back by reverting Desktop client/controller/view/test changes; API, database, installer, and Mobile remain untouched.

## Open Questions

- [ ] Confirm whether API export `content` is plain text, base64, or already binary-safe JSON text before apply writes files.
