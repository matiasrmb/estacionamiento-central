# Design: Desktop Closed-Report Operation Drill-Down

## Technical Approach

Extend the existing Desktop reporting stack in place: `utils/api_client.py` builds the canonical operations request, `controllers/reportes_controller.py` normalizes the API response into a stable view model, and `views/reportes.py` adds a small operation table/control strip inside the current closed-report panel. This maps to `reproducible-closed-reports` by loading only `period_id=closure:{id}`, preserving API-owned pagination/status/warnings/errors, and keeping the local calendar report table visibly legacy/local.

## Architecture Decisions

| Option | Tradeoff | Decision |
|---|---|---|
| Add `obtener_operaciones_reporte(token, closure_id, **filters)` in `utils/api_client.py` | Small wrapper, but must prevent accidental query growth. | Use an allow-list for `category`, `operator`, `plate`, `sort`, `direction`, `limit`, `offset`; always derive `period_id=closure:{closure_id}` and omit unsupported/blank values. |
| Normalize operations in controller before the view | Adds controller code, but keeps PySide rendering simple and testable. | Add `obtener_operaciones_reporte_cerrado(...)` returning rows, pagination, filters, source/status, warnings, and explicit API error fields. |
| Add a second table in the closed-report panel | Increases `views/reportes.py`, but avoids dashboard or local-table rewrites. | Add a narrow operation table and controls below closed-report metadata; leave dashboard cards, local results table, and hidden export buttons unchanged. |
| Single PR vs chain | Client/controller/view tests may approach the 400-line review budget. | Single PR is likely if tasks stay focused; chain if view changes exceed forecast, splitting API/controller first and view second. |

## Data Flow

    Closed report loaded ──→ closure_reference.id
          │
          ▼
    View controls ──→ Controller normalization ──→ API client wrapper
          ▲                    │                         │
          └──── rows/status/pagination/errors ←──────────┘

No local `obtener_reportes()` fallback is allowed for API-owned operation rows.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `utils/api_client.py` | Modify | Add operations wrapper and query encoder using only allowed params. |
| `controllers/reportes_controller.py` | Modify | Import wrapper; normalize operation rows, pagination, filters, warnings, status, and errors. |
| `views/reportes.py` | Modify | Add closed-report operation controls/table/status while preserving existing dashboard, exports-hidden, and local report flows. |
| `tests/test_api_client_session.py` | Modify | Assert canonical endpoint, `period_id=closure:42`, supported params, and unsupported omission. |
| `tests/test_reportes_controller.py` | Modify | Cover row normalization, empty/warning states, API errors, pagination, and no local fallback. |
| `tests/test_reportes_view.py` | Modify | Cover operation row rendering, pagination/status/error labels, controls, and local legacy boundary. |

## Interfaces / Contracts

```python
ALLOWED_OPERATION_PARAMS = {"category", "operator", "plate", "sort", "direction", "limit", "offset"}

{
    "ok": True,
    "source": "api",
    "period_id": "closure:42",
    "rows": [{"category": str, "amount": number, "operator": str, "plate": str, "timestamp": str}],
    "pagination": {"limit": int, "offset": int, "total": int},
    "filters": {...},
    "warnings": [],
    "api_error": None,
}
```

API/Mobile/Installer contracts are consumed as-is; no sibling repo changes, schema changes, or installer impacts.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | API wrapper path/query allow-list | Mock `_request` in `tests/test_api_client_session.py`. |
| Unit | Controller normalization/errors | Mock API wrapper and local report function in `tests/test_reportes_controller.py`. |
| View | Rendering and controls | Patch controller calls in `tests/test_reportes_view.py`; assert table/status without enabling exports. |
| E2E | N/A | Existing desktop suite is unittest-only; run `python -m unittest discover -s tests`. |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration / Rollout

No migration required. Roll back by reverting Desktop client/controller/view/test changes; closed reports, dashboard, hidden exports, and local calendar consultation remain unchanged.

## Explicit Boundaries

- No dashboard reimplementation, export delivery, API/Mobile/Installer changes, open/current operation rows, audit inventory UI, ledger, or event sourcing.
- The local calendar table remains legacy/local consultation and must not fabricate canonical operation rows.

## Open Questions

- None.
