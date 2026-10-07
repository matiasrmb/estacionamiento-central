# Design: Desktop Reporting Dashboard API Validation

## Technical Approach

Use validation-first Desktop-only alignment. The production change is limited to making the Desktop reporting dashboard client request `GET /reporting/dashboard` without undeclared query parameters, then updating mocked tests to prove endpoint construction, metric catalog compatibility, dashboard metadata preservation, and existing rendering behavior. Optional local API smoke can be recorded as evidence only when an authenticated seeded local API is already available; mocked tests remain the gate.

## Architecture Decisions

| Decision | Choice | Alternatives considered | Rationale |
|---|---|---|---|
| Dashboard request ownership | Desktop calls `/reporting/dashboard` with no `period_id`, `state`, or other dashboard query parameters. | Keep ignored query params for UI intent; add API support for current/open params. | The API contract does not declare these params, so sending them creates drift and false confidence. API changes are out of scope. |
| Adapter surface | Simplify `utils.api_client.obtener_dashboard_reporting(token)` and remove unused query construction. | Keep optional arguments but ignore them. | Ignored arguments preserve the wrong mental model; tests should fail if callers try to pass unowned filters. |
| Controller/view scope | Update only the dashboard API call path and tests; preserve normalization, fallback, local table flows, and rendering. | Rework dashboard widgets or add operations pagination/drill-down. | The archived dashboard already exists; this change validates and aligns the contract, not product behavior. |
| Live smoke | Treat local API smoke as optional evidence, not a blocker. | Require live API validation for delivery. | Availability of seeded auth/local API is environmental; mocked contract tests provide deterministic coverage. |

## Data Flow

```text
ReportesWindow.filtrar
  ├─ obtener_reportes(...)                  -> local table/totals remain unchanged
  └─ obtener_resumen_dashboard_reportes(token)
       ├─ obtener_catalogo_metricas_reporting(token) -> GET /reporting/metric-catalog
       ├─ obtener_dashboard_reporting(token)          -> GET /reporting/dashboard
       └─ _normalizar_dashboard_reporting_api(...)    -> view metadata/cards
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `utils/api_client.py` | Modify | Remove `urlencode` import if unused, change `obtener_dashboard_reporting` to accept only `token`, and call `_request("GET", "/reporting/dashboard", token=token)`. |
| `controllers/reportes_controller.py` | Modify | Remove `period_id`/`state` defaults from `obtener_resumen_dashboard_reportes` and call `obtener_dashboard_reporting_api(token)` with no dashboard filters. Keep fallback and normalization logic intact. |
| `tests/test_api_client_session.py` | Modify | Replace the current/open dashboard endpoint test with a canonical no-query assertion for `/reporting/dashboard`; keep metric catalog endpoint coverage. |
| `tests/test_reportes_controller.py` | Modify | Update mocked dashboard call assertions to no `period_id`/`state`; extend one payload test to include `filters` and `pagination` preservation. |
| `tests/test_reportes_view.py` | Modify | Keep rendering coverage for API metadata and compatible metric labels; add or update assertions only if needed to prove preserved canonical metadata remains visible. |

## Interfaces / Contracts

```python
def obtener_dashboard_reporting(token):
    return _request("GET", "/reporting/dashboard", token=token)
```

The accepted dashboard contract for this change is the API-owned response shape already consumed by Desktop: `period`, `catalog_version`, `filters`, `metrics`, and `pagination`. Future dashboard parameters may be added only after the API contract declares them.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | API adapter endpoint construction | Mock `_request` in `tests/test_api_client_session.py` and assert no query string. |
| Unit | Controller dashboard contract compatibility | Mock catalog/dashboard API calls in `tests/test_reportes_controller.py`; assert canonical metric keys, metadata preservation, and no unowned request args. |
| UI unit | View rendering compatibility | Use existing offscreen `ReportesWindow` tests to assert API source/version/period labels and metric cards still render. |
| Smoke | Local API metric catalog/dashboard | Optional manual evidence only when authenticated seeded local API is available; not required for pass/fail. |

## Threat Matrix

N/A — no application routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary is changed. This change only adjusts Desktop HTTP adapter endpoint construction for an already configured API base URL.

## Migration / Rollout

No migration required. Rollout is a Desktop code/test change only, with no API, Mobile, Installer, database, or bundled-asset impact.

## Open Questions

None.
