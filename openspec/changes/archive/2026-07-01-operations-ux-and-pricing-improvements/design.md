# Design: Operations UX and Pricing Improvements

## Technical Approach

Implement this as additive contracts across Desktop, API, Mobile, DB, and Installer docs. Keep current `ingresos`/`salidas` and parking-linked `lavados` behavior unchanged; add explicit wash-only records, quote services, dynamic wash pricing, safe delete guards, mobile unified operation, and printer diagnostics around the existing patterns.

## Architecture Overview

```text
Desktop PySide controllers/views ─┐
Mobile Dio APIs + state screens ──┼─> FastAPI endpoints -> repository/service -> MySQL
Desktop direct MySQL controllers ─┘                         -> print_jobs/FPDF/ReportLab
Installer docs/scripts -------------------------------------> setup + diagnostics guidance
```

## Decisions

| Area | Decision | Rationale |
|------|----------|-----------|
| Solo lavado data | Add `operaciones_servicio` for wash-only; do not make `lavados.id_ingreso` nullable in the first migration. Add nullable `id_operacion_servicio_origen`/snapshot fields to link wash-only converted to stay. | `lavados.id_ingreso NOT NULL` is used by existing parking wash billing; additive records avoid fake parking rows and preserve regressions. |
| Additive migration | Create `tipos_lavado`, `tipos_vehiculo_lavado`, `operaciones_servicio`; seed wash types from `configuracion.lavado_*`; backfill only type references/snapshots where safe. | Historical tickets/reports remain readable and rollback can ignore new tables. |
| Wash-only state machine | `ACTIVO -> FINALIZADO_COBRADO -> CERRADO` or `ACTIVO -> CONVERTIDO_ESTADIA -> COBRADO_EN_SALIDA -> CERRADO`; cancellation only admin/audited if added later. | Matches charge-now vs continue-as-stay without double charging. |
| Wash + stay ticket model | Store wash start/end/duration/amount snapshots in `operaciones_servicio`; generated `ingresos` starts at wash end and links back. Ticket detail renders wash section, stay section, total. | Stay billing remains normal while showing required temporal detail. |
| Cierre/report metric names | Keep `total_ingresos`/`total_salidas` for parking only. Add `total_lavados_solos`, `total_lavados_solos_monto`, and include in `total_general`. Reports expose the same names. | Prevents operational metrics from lying; solo lavado is service revenue, not parking movement. |
| Monthly fallback formula | Quote monthly uses entered amount first, then `vehiculos.tarifa_mensual`, then `tipos_vehiculo_lavado.valor_mensual_default`; if all are missing/zero, return `requires_amount=true` and no amount for that vehicle. Daily cost is `monthly_amount / 30`, rounded to nearest peso. | Satisfies missing-amount spec safely without inventing money. |
| Pricing config | Vehicle/wash type configuration applies only to wash pricing. Parking quotes/salidas call existing parking tariff code and ignore vehicle size. | Explicit non-goal: no parking tariff by vehicle size. |
| Safe user deletion | API/Desktop hard-delete only if username has no references in `ingresos`, `lavados`, `usos_bano`, `cierres_diarios`, `asistencias`, `print_jobs` payload/audit fields, or future service ops; otherwise deactivate. Block current user and last admin deletion. | Existing history references usernames as text, so FK-only checks are insufficient. |
| Printer support | Supported path is SumatraPDF plus configured Windows printer using validated vendor/thermal driver. Diagnostics show Sumatra path, printer name/existence/offline state, queue count, last print error, and test-print result. | Code already depends on Sumatra and Windows printer APIs; guidance must not promise generic drivers. |

## Contracts and Boundaries

| Layer | Boundary |
|------|----------|
| API | Add routers/services for `/cotizaciones/preview`, `/tipos-lavado`, `/tipos-vehiculo-lavado`, `/lavados/solo/*`, `/operacion-diaria`, `/impresion/diagnostico`, and `DELETE /usuarios/{usuario}`. Keep existing `/ingresos`, `/activos`, `/salidas`, `/lavados/iniciar|finalizar`, `/banos`. Repositories own SQL; services own pricing/ticket composition. |
| Desktop | Controllers mirror API service rules because Desktop uses direct MySQL. `views/registro.py` adds quote and solo-wash actions; config/users/printer screens add CRUD, delete, diagnostics. `utils/ticket.py` accepts optional detail sections. |
| Mobile | Add a unified operation feature with API/model/state files. Preserve `Ingreso`, `Activos / Salida`, and `Lavados / Baño`; existing module gains plate search and solo-wash hooks. |
| Installer/docs | Update print-agent README/setup/diagnostics guidance; schema import remains create-only for fresh installs, while migrations handle existing DBs. |

## Quote Service

Stateless quote payload supports items: `estadia`, `lavado`, `mensualidad`, and combinations. Estadía uses existing tariff calculation; lavado uses active wash config snapshot; monthly returns per-vehicle monthly amount, per-vehicle daily amount, combined monthly total, and combined daily total. Quote writes no billable rows.

## Migration, Backfill, Rollback, Safety

Use idempotent migrations: create new tables/columns, seed active wash config, add indexes on state/date/plate/closed. Do not rewrite historical `lavados` except optional nullable type reference. Existing installs must backup first; rollback disables new endpoints/UI and leaves new tables unused. Finalized wash-only rows are closed exactly once by `cerrado` flags.

## Testing Matrix

| Repo | Tests |
|------|-------|
| Desktop | Unit tests for quote formulas, solo-wash transitions, cierre totals, safe delete, ticket detail; run `python -m unittest discover -s tests`. |
| API | Endpoint/repository tests for additive contracts, cierre/report names, print diagnostics; run `python -m unittest discover -s tests`. |
| Mobile | API parsing/state/widget tests for unified screen and preserved modules; run `flutter test` and `flutter analyze`. |
| Installer | Manual fresh install + existing DB migration + diagnostics bundle validation. |

## Chained PR Slicing

Keep each slice under 400 changed lines: 1) quote service/API+Desktop preview, 2) wash pricing type tables/config, 3) wash-only DB/API/accounting, 4) Desktop wash/tickets, 5) Mobile unified operation, 6) safe user deletion, 7) printer diagnostics/docs. Use stacked/feature-chain strategy before apply; no `size:exception` assumed.

## Risks

- Accounting regressions if solo-wash close flags are not tested first.
- Desktop direct-DB logic and API logic can diverge; duplicate rules must share fixtures/expected examples.
- Print diagnostics can identify unsupported setup, not guarantee unreliable generic drivers.
