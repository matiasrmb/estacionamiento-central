# Design: Desktop Closed Report Exports

## Technical Approach

Enable the existing Desktop closed-report export controls only after the view holds an API-backed closed-report payload with `closure_reference.id`. The UI will call the existing `exportar_reporte_cerrado` controller path for PDF/XLSX, render success/error details in the closed-report status area, and preserve the loaded report for retry. This maps directly to the reproducible closed-report requirements without adding API, Mobile, Installer, CSV, local fallback, or destination-selection behavior.

## Architecture Decisions

| Decision | Choice | Alternatives considered | Rationale |
|---|---|---|---|
| Export ownership | Keep export orchestration in `views/reportes.py`, routed through `controllers.reportes_controller.exportar_reporte_cerrado`. | Add a new API client call from the view; add a new controller API. | Existing MVC-style code already imports the controller function; reusing it avoids API churn and keeps file writing centralized. |
| Valid export state | Derive visibility/enabled state from `reporte_cerrado_actual` plus `closure_reference.id`. | Enable based on operation rows, local calendar filters, or token only. | The spec requires API-backed closure truth; operation rows may be empty and local calendar results must not unlock closed exports. |
| Status rendering | Reuse closed-report labels/message boxes: success updates the deferred/status label with saved path; errors show detail/status and leave report state intact. | Add a new destination dialog or modal-only feedback. | Smallest UI delta; visible inline status supports retry and avoids broad destination scope. |
| Controller hardening | Add only focused result hardening if tests expose a gap, such as returning status/detail for invalid export content. | Change controller signature or API contract. | Current controller already preserves API errors and writes to `reportes/`; no contract change is needed. |

## Data Flow

```text
Admin loads closed report
  -> ReportesWindow.cargar_reporte_cerrado
  -> controllers.obtener_reporte_cerrado
  -> API client /reporting/reports/closed/{closure_id}
  -> view stores reporte_cerrado_actual and enables PDF/XLSX if closure_reference.id exists

Admin clicks PDF/XLSX
  -> ReportesWindow.exportar_reporte_cerrado_api(format)
  -> controllers.exportar_reporte_cerrado(token, closure_id, format)
  -> API client /reporting/exports/{closure_id}.{format}
  -> controller writes reportes/closed_{closure_id}.{format}
  -> view renders saved path or actionable error
```

## File Changes

| File | Action | Description |
|---|---|---|
| `views/reportes.py` | Modify | Add a small export-state helper, show PDF/XLSX buttons only for valid API closed reports, remove/hide deferred copy after enablement, and update success/error status without clearing the loaded report. |
| `controllers/reportes_controller.py` | Modify if needed | Preserve existing signature; optionally harden invalid content errors into the same `{ok: False, status, api_error}` result shape. |
| `tests/test_reportes_view.py` | Modify | Replace deferred assertions with RED/GREEN tests for hidden/disabled initial state, enabled valid state, local-calendar isolation, PDF/XLSX click routing, success path text, error text, and retry preservation. |
| `tests/test_reportes_controller.py` | Modify if needed | Add focused regression only for any controller hardening gap discovered during apply. |
| `tests/test_api_client_session.py` | No change expected | Existing endpoint and CSV rejection coverage is sufficient unless regressions appear. |

## Interfaces / Contracts

No public API changes. The view consumes the existing controller result contract:

```python
{"ok": True, "format": "pdf|xlsx", "path": "reportes/closed_<closure>.<format>", "metadata": {...}}
{"ok": False, "format": "pdf|xlsx", "status": 500, "api_error": "EXPORT_FAILED"}
```

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| View unit | Export buttons are hidden/disabled before a valid closed report, visible/enabled after `closure_reference.id`, and never enabled by local calendar reports. | PySide unittest with patched controller functions. |
| View unit | PDF/XLSX clicks call `exportar_reporte_cerrado(token, closure_id, format)`, render saved path on success, render detail/status on error, and allow retry. | Mock controller return values and message boxes; assert `reporte_cerrado_actual` remains set. |
| Controller unit | Only if hardening changes are made: invalid/missing export content returns actionable error shape without API changes. | Focused `tests/test_reportes_controller.py` regression. |
| API client unit | Existing PDF/XLSX endpoint and CSV rejection tests remain. | No new tests expected. |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary is changed.

## Migration / Rollout

No migration required. The change is Desktop-only and uses the existing `reportes/` folder convention.

## Review Workload Forecast

Expected implementation is low risk and likely under 180 authored changed lines: mostly `views/reportes.py` plus view tests, with optional small controller regression. Decision needed before apply: No. Chained PRs recommended: No. 400-line budget risk: Low.

## Open Questions

- None.
