# Design: Complete Operations Pricing Gaps

## Technical Approach

Keep the Desktop slice local and additive. Reuse `controllers.accounting_contracts` as the accounting authority, add idempotent `operaciones_servicio` closure support before any solo-lavado closure query, and make Desktop daily close persist a local closure reference that includes charged solo lavados once. API and Mobile remain unchanged; API responses still drive remote close success, while Desktop augments/persists only its local operational rows.

## Architecture Decisions

| Decision | Choice | Alternatives considered | Rationale |
|---|---|---|---|
| Schema support | Keep `cerrado` and add nullable `id_cierre` plus index/FK in `operaciones_servicio`; provide `asegurar_schema_operaciones_servicio_cierre(cursor)` using `SHOW COLUMNS/SHOW INDEX` guarded `ALTER TABLE`. | Rely only on `cerrado`; destructive migration; installer parity. | `cerrado` prevents recounting, `id_cierre` gives replay linkage, additive ensure satisfies old DBs without resetting data, installer is out of scope. |
| Ensure point | Call the ensure helper inside local DB transactions before selecting/marking charged solo lavados: `registro_controller.obtener_resumen_caja_actual`, `cierres_controller` local close persistence, and report queries that read closure state. | Startup migration; schema repair in unrelated controllers. | The spec requires readiness before accounting uses the fields; focused call sites limit runtime schema work. |
| Closure marking | After `crear_cierre_api(token)` succeeds, Desktop opens one local transaction, ensures schema, inserts/updates a `cierres_diarios` local reference with totals including pending charged solo lavados, then updates matching rows to `cerrado = TRUE, id_cierre = <local id>`. | Mark before API success; no local persistence. | Post-API marking avoids closing local rows when the authoritative close fails; local reference enables exact Desktop replay. |
| Exclusions | Select solo lavados for immediate close/report only when `estado = 'FINALIZADO_COBRADO'`, `cerrado = FALSE`, `id_ingreso_generado IS NULL`, and `fecha_hora_fin IS NOT NULL`; active and converted rows remain excluded. | Filter only by status. | Converted rows defer to parking exit; active rows are not collected income. |
| Reports | Open local reports keep normalized `lavado_solo` items and `build_report_totals`; closed report replay must prefer persisted `cierres_diarios` totals/items by `id_cierre` and never recalculate from open-period rows. | Recalculate closed periods. | Reproducibility requires saved closure bytes/totals to win over later edits. |

## Data Flow

```text
API close success -> Desktop DB transaction
  -> ensure operaciones_servicio close columns
  -> read pending FINALIZADO_COBRADO solo lavados
  -> build_accounting_summary + API/local totals
  -> persist cierres_diarios local reference
  -> mark selected solo lavados cerrado/id_cierre
Reports: open period reads rows; closed period replays cierres_diarios reference.
```

## File Changes

| File | Action | Description |
|---|---|---|
| `schema.sql` | Modify | Add `operaciones_servicio.id_cierre`, index, and FK to `cierres_diarios`; keep `cerrado`. |
| `controllers/operaciones_servicio_controller.py` | Modify | Add idempotent schema ensure and helpers to list/mark charged pending solo lavados. |
| `controllers/cierres_controller.py` | Modify | Persist Desktop local close reference after API success and include solo-lavado totals in PDF/message data. |
| `controllers/registro_controller.py` | Modify | Ensure schema before caja summary solo-lavado query. |
| `controllers/reportes_controller.py` | Modify | Keep open report inclusion/exclusion and add closed-reference replay path if period state/id is supplied. |
| `controllers/accounting_contracts.py` | Modify | Reuse existing charged-only filters; add small item/totals helpers only if tests require shared normalization. |
| `tests/test_cierres_controller.py` | Modify | RED/GREEN tests for schema ensure, charged inclusion, marking once, and API-failure no-mark. |
| `tests/test_reportes_controller.py` | Modify | Tests for active/converted exclusion and closed replay not recounting. |
| `tests/test_accounting_report_contracts.py` | Modify | Contract tests for `cerrado` exclusion and charged-only totals. |

## Interfaces / Contracts

New helper contracts:

```python
asegurar_schema_operaciones_servicio_cierre(cursor) -> None
obtener_lavados_solos_pendientes_cierre(cursor) -> list[dict]
marcar_lavados_solos_cerrados(cursor, ids: list[int], id_cierre: int) -> None
```

All helpers must be idempotent and transaction-safe at caller level.

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit | Schema ensure emits guarded ALTER only when columns/index are missing and can run twice. | `python -m unittest tests.test_cierres_controller` |
| Unit | Charged solo lavado is included, marked, and excluded from a later close. | `python -m unittest tests.test_cierres_controller tests.test_accounting_report_contracts` |
| Unit | `ACTIVO` and `CONVERTIDO_ESTADIA` are excluded from closure and reports. | `python -m unittest tests.test_reportes_controller tests.test_accounting_report_contracts` |
| Regression | Local reporting API fallback remains unchanged for API/Mobile contracts. | `python -m unittest tests.test_reportes_controller` |
| Full Desktop | All unittest coverage. | `python -m unittest discover -s tests` |

Strict TDD: write the focused failing tests first, then implement the minimal helpers/controller changes, then run focused commands before the full suite.

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary is introduced.

## Migration / Rollout

No destructive migration required. Existing databases receive `id_cierre`/index/FK additively at the accounting ensure point; rollback reverts controller/test/schema reads and leaves additive columns unused.

## Open Questions

- [ ] None.
