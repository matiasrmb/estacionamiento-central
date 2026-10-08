# Design: Desktop Report Audit Visibility

## Technical Approach

Use the existing `GET /reporting/dashboard` path already consumed by `obtener_resumen_dashboard_reportes`. Desktop will preserve `audit_coverage`, normalize only the small display contract needed by `views/reportes.py`, and render one compact metadata line in the existing Intelligence Center dashboard metadata area. Local fallback remains degraded consultation data: incomplete, local, non-official, and audit-unavailable. No API, Mobile, Installer, database, migration, or new endpoint work is included.

## Architecture Decisions

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Normalize in controller vs parse every variant in the view | Controller normalization keeps the PySide view simple and testable, but must not invent data. | Add `_normalizar_audit_coverage_dashboard(value)` only if implementation needs stable keys. It returns a dict with `state`, `available`, `gaps`, `unavailable`, and `notes`; unknown/missing values become `state: not_provided`. |
| Dedicated panel vs existing metadata area | A panel adds review/UI weight for a tiny visibility slice. | Add one QLabel beside completeness/capacity/warnings in the dashboard group, e.g. `label_dashboard_auditoria`, placed after capacity and before warnings. |
| Hide missing audit data vs explicit unavailable text | Hiding makes limitations invisible and can imply official coverage. | Always render explicit compact text for missing/empty/local states. |
| Continue Desktop if payload is unusable | Desktop can only display supplied truth; fabricating audit inventory is harmful. | Stop implementation and recommend `api-report-audit-inventory` if current dashboard payload cannot provide meaningful status/limitations. |

## Data Flow

    reporting API dashboard
        -> controllers/reportes_controller._normalizar_dashboard_reporting_api
        -> payload["audit_coverage"] normalized/preserved
        -> views/reportes._actualizar_metadata_dashboard
        -> compact QLabel in Intelligence Center metadata

Local fallback follows the same view path with `audit_coverage: []`, `official: False`, and `source_state: local_fallback`.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `controllers/reportes_controller.py` | Modify | Preserve current `audit_coverage`; add minimal normalization helper only if tests require variants to produce stable UI fields. Keep local fallback empty. |
| `views/reportes.py` | Modify | Add and populate compact audit metadata label in the dashboard group after capacity and before warnings. |
| `tests/test_reportes_controller.py` | Modify | Cover API preservation/normalization and prove local fallback never fabricates audit coverage. |
| `tests/test_reportes_view.py` | Modify | Cover available coverage, known gaps, unavailable/not-provided, and local non-official audit-unavailable rendering. |
| `utils/api_client.py` | No change | Existing dashboard API client is sufficient unless the stop condition is reached. |

## Interfaces / Contracts

Preferred normalized shape, only if needed:

```python
{
    "state": "available" | "gap" | "unavailable" | "not_provided",
    "available": ["operations", "closures"],
    "gaps": ["payments"],
    "unavailable": ["legacy_history"],
    "notes": ["Backfill pending"],
}
```

Compact rendering rules:
- `available`: `Audit: available - <available sources>`; append `Gaps: <gaps>` when present.
- `gap`: `Audit: gaps - <gaps>`; include available sources only if supplied.
- `unavailable`: `Audit: unavailable - <reason/source list if supplied>`.
- `not_provided`: `Audit: not provided by reporting dashboard`.
- local fallback: `Audit: unavailable - local non-official fallback; API audit coverage unavailable`.

Do not label any missing source as covered. Truncate long lists to a compact first few entries plus count, matching the existing metadata-line style.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Controller unit | API payload preserves/normalizes audit coverage variants without fabrication. | Add focused unittest cases around `obtener_resumen_dashboard_reportes`. |
| Controller unit | API error fallback is local/non-official and audit-empty. | Extend existing fallback test assertions. |
| View unit | Metadata label renders available, gap, unavailable, and not-provided states. | Instantiate `ReportesWindow` offscreen and call dashboard update paths. |
| View unit | Local fallback text includes local, non-official, audit-unavailable. | Extend existing local fallback rendering test. |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration / Rollout

No migration required. Rollout is a Desktop-only display change over the existing dashboard payload.

## Stop Condition

If sampled/current dashboard payloads only provide empty, unstable, or non-semantic `audit_coverage`, stop Desktop implementation and recommend API change `api-report-audit-inventory` rather than adding a fabricated Desktop inventory.

## Out of Scope

API, Mobile, Installer, database, migrations, new endpoints, rich audit workbench, event sourcing, ledger UI, anomaly UI, and formal accounting/auditor workflows.

## Review Workload Forecast

Estimated changed lines: 90-160 authored lines. 400-line budget risk: Low. Chained PRs recommended: No. Decision needed before apply: No, unless the stop condition is reached.

## Open Questions

- [ ] None blocking; implementation should validate actual dashboard sample shapes before adding normalization breadth.
