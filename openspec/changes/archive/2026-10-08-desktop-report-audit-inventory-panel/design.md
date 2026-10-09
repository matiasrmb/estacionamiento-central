# Design: Desktop Report Audit Inventory Panel

## Technical Approach

Add a Desktop-only reporting path that requests `GET /reporting/audit-inventory` through the existing `utils.api_client` request helper, normalizes only the validated readiness contract in `controllers.reportes_controller`, and renders a compact read-only panel inside the current reporting/Intelligence Center view. The panel must expose API-supplied coverage, gaps, and limitations without deriving totals, freshness, event streams, persisted anomalies, or local fallback coverage.

## Architecture Decisions

| Decision | Choice | Alternatives considered | Rationale |
|---|---|---|---|
| API wrapper scope | Add `obtener_inventario_auditoria_reporting(token, period_id=None)` in `utils/api_client.py`. | Reuse dashboard calls or add generic query helper. | Keeps the endpoint explicit and testable while allowing only optional `period_id`. |
| Controller contract | Add `obtener_inventario_auditoria(token, period_id=None)` and private normalization helpers. | Let the view consume raw payloads. | Existing reporting code centralizes API error handling and payload shaping in the controller. |
| Error and invalid payload handling | Return `ok: False`, `source: "api"`, `source_state: "api_error"` or `"unavailable"`, plus empty contract lists/flags. | Fabricate local availability from `obtener_reportes` or dashboard metadata. | The spec forbids local fallback fabrication for inventory readiness. |
| UI placement | Add a small label-based panel near the Intelligence Center metadata. | Add a new large table or separate window. | `views/reportes.py` is already large; labels preserve compactness and review budget. |

## Data Flow

```text
ReportesWindow
  └─ load/refresh audit inventory
       └─ controllers.reportes_controller.obtener_inventario_auditoria
            └─ utils.api_client.obtener_inventario_auditoria_reporting
                 └─ GET /reporting/audit-inventory[?period_id=...]
```

The view passes no period by default, or a supported `period_id` when explicitly available from current reporting context. Controller normalization preserves only: `period_id`, `coverage[]` with per-source `state`, `available_sources`, `partial_sources`, `unavailable_sources`, `affected_scopes`, `unavailable_history`, `requires_event_sourcing`, `supports_persisted_anomalies`, and `unsupported_behaviors`.

## File Changes

| File | Action | Description |
|---|---|---|
| `utils/api_client.py` | Modify | Add the audit inventory wrapper and encode only non-blank `period_id`. |
| `controllers/reportes_controller.py` | Modify | Import the wrapper, add controller function, validate required shape, normalize lists/booleans, and expose explicit unavailable/error states. |
| `views/reportes.py` | Modify | Import controller function, add compact labels/buttons or refresh hook, render coverage groups and limitations, and keep existing dashboard/closed-report/local flows intact. |
| `tests/test_api_client_session.py` | Modify | Assert canonical endpoint path with and without `period_id`, and no undeclared query parameters. |
| `tests/test_reportes_controller.py` | Modify | Cover successful normalization, missing fields, API errors, and no calls to local report fallback. |
| `tests/test_reportes_view.py` | Modify | Cover compact rendering of available/partial/unavailable sources, limitations, error/unavailable states, and preserved existing flows. |

## Interfaces / Contracts

Controller output shape:

```python
{
    "ok": bool,
    "source": "api",
    "source_state": "api" | "unavailable" | "api_error",
    "period_id": str | None,
    "coverage": [{"source": str, "state": str, ...}],
    "available_sources": list[str],
    "partial_sources": list[str],
    "unavailable_sources": list[str],
    "affected_scopes": list[str],
    "unavailable_history": list[str],
    "requires_event_sourcing": bool,
    "supports_persisted_anomalies": bool,
    "unsupported_behaviors": list[str],
    "api_error": str | None,
}
```

No API, Mobile, Installer, database, migration, event-sourcing, persisted-anomaly storage, totals/counts, or freshness timestamp contract is introduced.

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit | Endpoint construction and optional query | Mock `_request` in `tests/test_api_client_session.py`. |
| Unit | Normalization and error states | Mock API wrapper in `tests/test_reportes_controller.py`; assert no local fallback. |
| UI unit | Rendering and flow preservation | PySide offscreen tests in `tests/test_reportes_view.py`. |

Use `python -m unittest` conventions; focused runs can target the three affected test modules, with final verification through `python -m unittest discover -s tests`.

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration / Rollout

No migration required. Rollback removes the wrapper, controller normalization, compact view panel, and tests.

## Open Questions

None.
