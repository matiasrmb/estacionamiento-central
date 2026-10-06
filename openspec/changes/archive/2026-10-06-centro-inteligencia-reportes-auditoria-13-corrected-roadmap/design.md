# Design: Corrected Reporting Intelligence and Audit Roadmap

## Technical Approach

Implement this roadmap as repo-scoped derivatives after Slice 0 reconciliation. API remains the canonical reporting contract; Desktop becomes the full administrative center consuming API read models; Mobile remains quick consultation; Installer only aligns packaged API/Desktop payloads and versions. Official reporting uses closure/journey periods first, with calendar dates only as secondary grouping.

## Architecture Decisions

| Area | Choice | Alternatives considered | Rationale |
|---|---|---|---|
| Slice 0 | Produce a keep/change/remove/defer matrix before tasks. | Continue from premature implementation. | Existing API/Desktop/Mobile already contain merged reporting work that conflicts with corrected semantics. |
| Metric contract | Rename semantics to `collected_sources_total`, `operational_expense_total`, `net_revenue_total`, `monthly_payments_collected_total`, `vehicle_movement_count`. | Keep current `operational_*`/`mensualidad_sales_total` names. | Specs define net revenue as all collected sources minus expenses; monthly payments count where collected. |
| Period truth | Model journeys from `cierres_diarios.fecha_inicio` to `fecha_cierre`; current journey starts at latest trusted closure. | Calendar-day truth. | Existing controllers and API already mix calendar ranges; corrected roadmap requires closure/journey authority. |
| Capacity | Read current capacity from configuration, default 50; label historical missing capacity as `historical-capacity-limited`. | Keep hard-coded `TOTAL_PARKING_SPACES = 50`. | Current API hard-codes 50 in `reporting_read_models.py`; specs require configurable metadata. |
| Exports | Remove 1.3.0 dependency on PDF/XLSX delivery; defer export endpoints/UI to 1.3.x. | Keep current API/Desktop export buttons as release-blocking. | Specs explicitly make exports non-blocking for 1.3.0. |
| Audit | Build an existing-source audit inventory and anomaly summary, not event sourcing. | Introduce append-only events. | Schema already has closures, payments, expenses, sessions, print jobs, and expense audit tables. |

## Slice 0 Reconciliation Outputs

| Existing behavior | Outcome | Follow-up |
|---|---|---|
| API reporting endpoints and admin guard | Keep | Preserve `/reporting/*` admin-only shape. |
| Hard-coded capacity 50 | Change | Move to configurable metadata with default 50. |
| `operational_income_total`/`mensualidad_sales_total` naming | Change | Migrate to corrected catalog names and compatibility mapping. |
| Desktop local fallback dashboard | Change | Label incomplete, local, non-official; never closure truth. |
| Mobile dashboard screen | Keep/change | Keep quick view, change labels to canonical API labels. |
| API/Desktop PDF/XLSX export implementation | Defer | Move to 1.3.x derivative or hide behind non-1.3.0 scope. |
| CSV compatibility | Remove | Do not advertise CSV as canonical spreadsheet output. |

## Data Flow

```text
MySQL closure/operation sources
  -> API reporting repositories/read models
  -> canonical metric/audit/dashboard payloads
  -> Desktop full center + Mobile quick consultation
  -> Installer bundles matched API/Desktop payloads
```

Closed reports replay `cierres_diarios` closure references; later operational recalculation appears only as discrepancy/anomaly metadata.

## File Changes

| File | Action | Description |
|---|---|---|
| `estacionamiento-central-api/app/api/v1/endpoints/reporting.py` | Modify | Align route parameters and admin-only contracts for canonical dashboard, closed reports, audit inventory, anomalies. |
| `estacionamiento-central-api/app/repositories/reporting_repo.py` | Modify | Query closure/journey sources, monthly payments by `fecha_pago`, capacity config, and audit coverage. |
| `estacionamiento-central-api/app/repositories/reporting_read_models.py` | Modify | Catalog names, capacity labels, anomaly payloads, export deferral. |
| `estacionamiento-central/controllers/reportes_controller.py` | Modify | Normalize canonical API payloads and degraded local fallback labels. |
| `estacionamiento-central/views/reportes.py` | Modify | Full-center Desktop UI; remove 1.3.0 export promises if deferred. |
| `estacionamiento_central_mobile/lib/features/admin/reportes/**` | Modify | Quick consultation only, canonical labels, no full-center flows. |
| `estacionamiento-central-installer/**` | Modify | Package aligned API/Desktop payloads and version manifests only after repo derivatives land. |

## Interfaces / Contracts

API payloads MUST expose: `period{id,start,end,state,axis}`, `calendar_secondary`, `metrics`, `capacity{configured,total,state}`, `completeness`, `source_state`, `anomalies[]`, and `audit_coverage[]`. Fallback Desktop payloads MUST use `source_state=local_fallback`, `completeness.state=incomplete`, and `official=false`.

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| API unit | metrics, net revenue, monthly payment timing, capacity labels, anomalies | `python -m unittest discover -s tests` in API repo. |
| Desktop unit/view | canonical rendering and non-official fallback labels | Existing `test_reportes_controller.py` and `test_reportes_view.py` patterns. |
| Mobile widget/unit | quick consultation labels and no full-center/export UI | `flutter test` plus focused admin reporting tests. |
| Installer/manual | payload manifest commit/version alignment | Checklist or script around `API_PAYLOAD_MANIFEST.json`. |

## Threat Matrix

Only API route contract changes are applicable. Documentation-like paths, Git repository selection, commit state, push state, and PR commands are N/A because this design does not classify executables or automate VCS/PR actions. RED tests: unsupported filters return 422; reporting routes reject non-admin access; malformed period/closure identifiers fail safely.

## Migration / Rollout

No runtime migration in this planning change. Implementation MUST be split into repo-scoped derivatives to avoid cross-common-dir blockers: API first, Desktop second, Mobile third, Installer last.

## Open Questions

- [ ] Exact configuration key/table shape for capacity is not yet chosen.
- [ ] Whether current export code is hidden, reverted, or moved into a 1.3.x derivative remains a Slice 0 outcome.
