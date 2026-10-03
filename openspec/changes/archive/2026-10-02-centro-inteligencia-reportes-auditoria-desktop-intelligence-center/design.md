# Design: Desktop Intelligence Center Reporting and Audit Slice

## Technical Approach

Keep the slice inside the Desktop repo and extend the existing `obtener_resumen_dashboard_reportes()` boundary. The controller will normalize canonical dashboard payloads into a stable view model, while `ReportesWindow` renders that model without inventing API labels or calling future closed/export endpoints. Tests stay payload-driven by patching Desktop controller/API functions, so PR #80/#81/#82 are runtime prerequisites only, not unit-test dependencies.

## Architecture Decisions

| Decision | Choice | Alternatives considered | Rationale |
|---|---|---|---|
| Controller normalization | Extend `_normalizar_dashboard_reporting_api()` and add a small fallback metadata helper. | Move normalization into the view. | The controller already owns the API/local boundary and tests can verify payload contracts without PySide. |
| Canonical labels | Preserve API/catalog `label`/`meaning` in `summary`; view only falls back when a label is absent. | Override known metric names with Desktop strings. | Specs require canonical labels to remain visible; local fallback may still use Desktop labels. |
| Fallback state | Represent local fallback as `source: local_fallback`, `source_state: local_fallback`, `completeness: {state: incomplete, reason: ...}`. | Reuse only legacy `source` and `api_error`. | Machine-readable incompleteness lets the view show warnings without parsing errors. |
| Closed/export roadmap | Add visible non-operational boundary controls/copy that open information messages only. | Add API client methods or generate PDF/CSV output. | This slice must expose prerequisites without implementing closed-report retrieval or export generation. |

## Data Flow

```text
API catalog + dashboard payload ──→ controller normalization ──→ ReportesWindow dashboard renderer
                                      │
Local report fallback ────────────────┘ marked incomplete/local
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `controllers/reportes_controller.py` | Modify | Preserve `period_state`, `source_state`, `completeness`, `capacity`, canonical metric labels, and add local fallback metadata. |
| `views/reportes.py` | Modify | Render period/source/completeness/capacity metadata, preserve canonical labels, and add closed/export roadmap boundary UI with no endpoint/output side effects. |
| `tests/test_reportes_controller.py` | Modify | Add payload-driven RED tests for canonical fields and incomplete/local fallback. |
| `tests/test_reportes_view.py` | Modify | Add PySide tests for labels, warning state, capacity text, period/source state, and non-calling roadmap boundaries. |

## Interfaces / Contracts

Controller normalized dashboard payload:

```python
{
    "source": "api" | "local" | "local_fallback",
    "source_state": "api" | "operations" | "closure" | "local_fallback",
    "period": {"id": str, "state": str},
    "period_state": "open" | "closed" | str,
    "completeness": {"state": "complete" | "incomplete", "reason": str | None},
    "capacity": dict | None,
    "catalog_version": str | None,
    "summary": [{"metric": str, "label": str, "sign": str | None, "value": object}],
}
```

Local fallback MUST keep existing `items`/`totals` compatibility and add the same state fields where meaningful.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | API normalization preserves canonical labels, period/source/completeness/capacity. | Patch `obtener_catalogo_metricas_reporting_api` and `obtener_dashboard_reporting_api` with in-memory payloads. |
| Unit | API unavailable fallback is incomplete/local and keeps legacy totals/items. | Patch API calls to raise `ApiClientError` and patch `db_cursor`; no live API required. |
| View unit | Dashboard renders canonical labels, warnings, capacity, and period/source state. | Instantiate `ReportesWindow` offscreen and patch controller functions. |
| View unit | Closed/export boundaries are visible but non-calling/non-generating. | Patch future API/output candidates with assertions that they are not called; assert informational copy. |
| Integration/E2E | Runtime compatibility with live canonical API. | Out of scope for unit tests; verify later when PR #80/#81/#82 or equivalent API work is available. |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration / Rollout

No migration required. This is a Desktop-only controller/view/test change with no database, installer, API, Mobile, printer agent, or output format mutation.

## Open Questions

- [ ] None.
