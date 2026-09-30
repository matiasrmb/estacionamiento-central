# Design: Centro de Inteligencia, Reportes y Auditoría

## Technical Approach

Implement an incremental hybrid reporting architecture: the API owns canonical read models, metric formulas, authorization, exports, closed-report replay, and audit inventory; Desktop and Mobile consume those contracts while Desktop keeps existing local reports until parity is proven. This maps to `canonical-reporting-api`, `operational-dashboard`, `reproducible-closed-reports`, and `admin-reporting-access`.

## Architecture Decisions

| Decision | Choice | Alternatives considered | Rationale |
|---|---|---|---|
| Canonical authority | API read models in `app/repositories/reporting_read_models.py` behind `/api/v1/reporting/*` routes | Desktop-owned reports; full rewrite | One contract prevents Desktop/Mobile semantic drift while preserving current Desktop screens. |
| Period model | Operational day = closure-to-closure period; missing next closure is `open`; cross-midnight stays one period. `asistencias` login→logout rows are operator sessions inside the operational day. | Calendar day filters; login/logout as operational day | Approved clarification: two operators in one business day must not split the operational day. |
| Closed reports | Use `cierres_diarios` snapshot as closure reference plus linked operation rows for drill-down/discrepancy | Recalculate closed totals only | Closed exports must reproduce exactly, while later operational edits must be visible separately. |
| Schema scope | Prefer existing tables; add migration only for reproducibility metadata if existing `cierres_diarios` cannot store `metric_catalog_version`, `source_state`, and export/template metadata | Event sourcing | Specs exclude full event sourcing; existing closure links cover the first audit inventory. |

## Data Flow

```text
Desktop/Mobile ──JWT(admin)──> API reporting endpoints ──> MySQL read queries
                               │
                               ├─ open: operational rows since last daily closure
                               └─ closed: cierre snapshot + linked operations + discrepancy diff
Installer ──packages──> API/Desktop payloads + migrations only when metadata/indexes are required
```

## File Changes

| File | Action | Description |
|---|---|---|
| `estacionamiento-central-api/app/api/v1/endpoints/reporting.py` | Create | Dashboard, reports, exports, closed replay, audit inventory routes. |
| `estacionamiento-central-api/app/repositories/reporting_read_models.py` | Create | Canonical formulas and source-of-truth selection. |
| `estacionamiento-central-api/app/repositories/reportes_repo.py` | Modify | Keep legacy route stable or adapt through canonical mapper. |
| `estacionamiento-central/controllers/reportes_controller.py` | Modify | Add API-backed adapter while preserving local report fallback/parity views. |
| `estacionamiento_central_mobile/lib/features/admin/reportes/...` | Modify | Consume canonical 1.3.0 resources and align version to `1.3.0`. |
| `estacionamiento-central-installer/scripts/*` / `EstacionamientoCentral.iss` | Modify if needed | Package migration/config assets only for new metadata/indexes. |

## Interfaces / Contracts

Recommended resources:
- `GET /api/v1/reporting/metric-catalog` → canonical names and signs: `operational_income_total`, `operational_expense_total`, `operational_net_total`, `mensualidad_sales_total`, `vehicle_movement_count`.
- `GET /api/v1/reporting/dashboard?period_id=current|{cierre_id|operational_day_id}&state=open|closed` → summary, closure-derived period bounds, state, catalog version.
- `GET /api/v1/reporting/reports/operations` → filters: operational day, movement type, plate, user, operator session; stable pagination/sorting.
- `GET /api/v1/reporting/reports/closed/{id}` → closure reference, operation-derived totals, discrepancies, drill-down links.
- `GET /api/v1/reporting/exports/{report_id}.{pdf|csv}` → export with metadata.
- `GET /api/v1/reporting/audit-inventory` → available source coverage and unavailable history markers.

Exports must include report id, period bounds, closure reference id, generated timestamp, metric catalog version, filters, source state, and template/export version.

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| API unit | formulas, signs, open vs closed source, discrepancies | `unittest` repository tests with fixture rows. |
| API endpoint | admin-only, validation, pagination, export metadata | FastAPI endpoint tests, including non-admin denial. |
| Desktop | API adapter mapping and local report preservation | Controller tests using mocked API responses and legacy payloads. |
| Mobile | canonical parsing, admin error handling, 1.3.0 UI summaries | Flutter tests with mocked Dio client. |
| Installer | migrations packaged only when required | Script/manual verification per installer convention. |

## Threat Matrix

| Boundary | Applicability | Design response | Planned RED tests |
|---|---|---|---|
| Documentation-like paths | N/A — no executable file classification. | None. | None. |
| Git repository selection | N/A — no VCS automation. | None. | None. |
| Commit state | N/A — no commit automation. | None. | None. |
| Push state | N/A — no push automation. | None. | None. |
| PR commands | N/A — no PR automation. | None. | None. |

## Migration / Rollout

Phase API contracts first behind new routes, then Desktop adapters, then Mobile 1.3.0. Keep `/reportes/movimientos` and current Desktop reports until parity tests pass. Add indexes on closure/date/operator/filter columns if query plans need them for ~400 vehicles/day; paginate operations, never summaries. Roll back by disabling new consumers without mutating operational data or closure snapshots.

## Non-Goals / Deferred Decisions

No ledger accounting, taxes, commissions, payment-method accounting, auditor role, ML anomaly scoring, or event sourcing. Deferred: exact export layout, discrepancy threshold wording, and whether metadata needs a new table or columns.

## Open Questions / Risks

- [ ] Existing `cierres_diarios` may not contain enough reproducibility metadata without migration.
- [ ] API/Desktop currently diverge on item names (`mensualidad` vs `pago_mensual`); adapters must normalize explicitly.
- [ ] Operator-session ownership for operations relies on user/time windows because many rows do not persist `session_id`; this must not define operational-day boundaries.
