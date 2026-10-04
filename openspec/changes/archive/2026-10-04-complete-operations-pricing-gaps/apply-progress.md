# Apply Progress: Complete Operations Pricing Gaps

## Status

- Change: `complete-operations-pricing-gaps`
- Phase: Apply
- Mode: Strict TDD
- Slice: 1 — schema ensure and one-time charged solo lavado closure marking; 2 — reporting and closed replay
- Delivery: chained PR slice, feature-branch-chain
- Result: Apply implementation complete for assigned Desktop slice 2 and verification tasks.

## Completed Tasks

- [x] 1.1 Added failing schema ensure tests for missing `operaciones_servicio.id_cierre` support and idempotent execution.
- [x] 1.2 Added failing closure tests for charged solo lavado inclusion, local closure reference persistence, `cerrado/id_cierre` marking, and API-failure no-mark.
- [x] 1.3 Added failing accounting contract test proving closed solo lavados are excluded from pending closure totals.
- [x] 2.1 Updated `schema.sql` with additive `operaciones_servicio.id_cierre`, closure index, and FK reference to `cierres_diarios`.
- [x] 2.2 Added closure schema/query/mark helpers in `controllers/operaciones_servicio_controller.py`.
- [x] 2.3 Wired successful Desktop daily close to persist a local closure reference, include charged solo lavado totals, and mark selected rows once.
- [x] 2.4 Ensured current caja summary prepares solo-lavado closure schema before reading closure fields.
- [x] 2.5 Ran the focused GREEN command successfully.
- [x] 3.1 Added failing report tests for open charged solo lavado inclusion and open-report exclusion filters for active, converted, closed, and linked rows.
- [x] 3.2 Added failing closed local replay test proving persisted `cierres_diarios` totals and synthetic closure items are used without recounting `operaciones_servicio` rows.
- [x] 3.3 Updated `controllers/reportes_controller.py` to ensure solo-lavado closure schema before report wash queries, filter open charged rows by `cerrado = FALSE` and `id_cierre IS NULL`, and replay closed local closure references for `state="closed"`.
- [x] 3.4 Confirmed no production update was needed in `controllers/accounting_contracts.py`; existing report totals normalization already supports the slice 2 payload.
- [x] 3.5 Ran the focused GREEN command successfully.
- [x] 4.1 Refactored closed replay into small helpers without changing API or Mobile behavior.
- [x] 4.2 Ran the full Desktop unittest suite successfully.
- [x] 4.3 Recorded rollback notes for the complete Desktop controller/helper/test slice.

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 1.1 | `tests/test_cierres_controller.py` | Unit | ✅ `python -m unittest tests.test_cierres_controller tests.test_accounting_report_contracts` → 17 tests OK | ✅ Missing helper and schema assertions failed with `AttributeError` / missing index | ✅ Focused command passed: 22 tests OK | ✅ Missing-column and idempotent-existing-column cases | ✅ Helper kept small and idempotent |
| 1.2 | `tests/test_cierres_controller.py` | Unit | ✅ Same safety net | ✅ Daily close local persistence failed because `db_cursor` and marking flow did not exist | ✅ Focused command passed: 22 tests OK | ✅ Success path plus API-failure no-mark path | ✅ Local merge/persist helpers extracted in `cierres_controller.py` |
| 1.3 | `tests/test_accounting_report_contracts.py` | Unit | ✅ Same safety net | ✅ Closed charged wash counted as pending (`2 != 1`) | ✅ Focused command passed: 22 tests OK | ✅ Closed charged, pending charged, and active rows in one contract case | ✅ Shared `_charged_wash_only` filter reused by summaries/reports |
| 2.1 | `schema.sql` via `tests/test_cierres_controller.py` | Unit | ✅ Same safety net | ✅ Schema assertions failed before DDL update | ✅ Focused command passed: 22 tests OK | ✅ Column, index, and FK reference asserted | ➖ Structural schema update; no further refactor needed |
| 2.2 | `tests/test_cierres_controller.py` | Unit | ✅ Same safety net | ✅ Helper contract failed before implementation | ✅ Focused command passed: 22 tests OK | ✅ Ensure, pending selection, and mark behavior exercised through closure path | ✅ Shared cursor helpers avoid duplicate row-shape parsing |
| 2.3 | `tests/test_cierres_controller.py` | Unit | ✅ Same safety net | ✅ Closure success test failed before local persistence/marking existed | ✅ Focused command passed: 22 tests OK | ✅ API success and API failure paths | ✅ Local closure merge/persist isolated from API error mapping |
| 2.4 | `tests/test_cierres_controller.py` / existing caja summary path | Unit | ✅ Same safety net | ✅ Covered by schema-helper RED before caja summary wiring | ✅ Relevant command with caja/report path passed: 38 tests OK | ✅ Caja summary uses the same idempotent helper as closure | ➖ Minimal import/call only |
| 2.5 | Command execution | Unit | ✅ Same safety net | ✅ RED command failed before implementation: 22 tests run, 2 failures, 4 errors | ✅ `python -m unittest tests.test_cierres_controller tests.test_accounting_report_contracts` → 22 tests OK | ✅ Additional relevant command with reportes passed: 38 tests OK | ➖ No refactor after final command |
| 3.1 | `tests/test_reportes_controller.py` | Unit | ✅ `python -m unittest tests.test_reportes_controller tests.test_accounting_report_contracts` → 26 tests OK | ✅ Focused RED failed because `reportes_controller` did not expose/call `asegurar_schema_operaciones_servicio_cierre` and open wash queries lacked `cerrado/id_cierre` filters | ✅ Focused command passed: 29 tests OK | ✅ Non-plate and plate-filter report paths both assert charged-only open wash filters | ✅ Shared report query additions kept alongside existing wash query structure |
| 3.2 | `tests/test_reportes_controller.py` | Unit | ✅ Same safety net | ✅ Focused RED failed: closed local dashboard path ran six open-period queries instead of one `cierres_diarios` replay query | ✅ Focused command passed: 29 tests OK | ✅ Saved closure totals and synthetic replay item assert persisted values win without `operaciones_servicio` recount | ✅ Closed replay split into `_normalizar_period_id_cierre`, `_totales_desde_cierre`, and `_items_desde_cierre` |
| 3.3 | `controllers/reportes_controller.py` via `tests/test_reportes_controller.py` | Unit | ✅ Same safety net | ✅ RED failures from 3.1 and 3.2 described the missing behavior before production changes | ✅ Focused command passed: 29 tests OK | ✅ Open-period wash query, plate-filter wash query, and closed-period replay path covered | ✅ Minimal helper extraction; API token path left unchanged |
| 3.4 | `tests/test_accounting_report_contracts.py` | Unit | ✅ Same safety net | ➖ No new failing accounting-contract test required because existing `build_report_totals` behavior already supported the report payload | ✅ Focused command passed: 29 tests OK | ✅ Existing report-total contract still covers charged-only solo lavado totals | ➖ No production refactor needed |
| 3.5 | Command execution | Unit | ✅ Same safety net | ✅ RED command failed before implementation: 29 tests run, 1 failure, 2 errors | ✅ `python -m unittest tests.test_reportes_controller tests.test_accounting_report_contracts` → 29 tests OK | ✅ Same focused command includes both new open-report and closed-replay cases | ➖ No further refactor after focused GREEN |
| 4.1 | `controllers/reportes_controller.py` / test harnesses | Unit | ✅ Focused GREEN already passed | ✅ Full suite exposed two report-adjacent fake cursor schema-result regressions in `tests/test_registro_controller.py` after the report ensure pattern | ✅ `python -m unittest tests.test_reportes_controller tests.test_accounting_report_contracts tests.test_registro_controller` → 141 tests OK | ✅ Report and caja fake cursor schema paths both preserve queued business rows | ✅ Shared fake schema behavior mirrors idempotent ensure without touching production API/Mobile code |
| 4.2 | Full suite | Unit | ✅ Focused commands passed before full suite | ✅ First full suite run failed: `Ran 388 tests`, 2 failures in caja summary tests due fake cursor schema-result consumption | ✅ Final `python -m unittest discover -s tests` → 388 tests OK | ✅ Full suite covered report, cierre, caja, and unrelated Desktop tests | ➖ Verification only after harness fix |
| 4.3 | Apply-progress rollback notes | Process | ✅ Tasks/progress read before merge | ✅ Rollback notes were pending before this progress update | ✅ Rollback notes recorded below | ➖ Process artifact only | ➖ No code refactor needed |

## Test Summary

- Total tests written: 9 across slice 1 and slice 2; slice 2 added 3 report-controller tests and updated test harness support for schema ensure calls.
- Total tests passing: 29 in the required focused slice 2 command; 388 in the full Desktop suite.
- Layers used: Unit (9), Integration (0), E2E (0).
- Approval tests: None — behavior changed under new SDD requirements.
- Pure functions created: 4 (`_fusionar_cierre_con_lavados_solos`, `_normalizar_period_id_cierre`, `_totales_desde_cierre`, `_items_desde_cierre`).

## Work Unit Evidence

### Slice 1 — Schema Ensure and One-Time Close

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `python -m unittest tests.test_cierres_controller tests.test_accounting_report_contracts` → exit 0, `Ran 22 tests in 0.216s`, `OK` |
| Runtime harness command/scenario and exact result | Scenario exercised by unit harness: daily close with one `FINALIZADO_COBRADO` solo lavado after API success persists a local closure reference, includes `$8000` in solo-lavado totals, and marks `id_operacion_servicio=11` with `id_cierre=91`; relevant touched-path command `python -m unittest tests.test_cierres_controller tests.test_accounting_report_contracts tests.test_reportes_controller` → exit 0, `Ran 38 tests in 0.126s`, `OK` |
| Rollback boundary | Revert `schema.sql`, `controllers/operaciones_servicio_controller.py`, `controllers/cierres_controller.py`, `controllers/registro_controller.py`, `controllers/accounting_contracts.py`, `tests/test_cierres_controller.py`, `tests/test_accounting_report_contracts.py`, and this slice's task/progress artifact updates. Additive DB columns may remain unused after rollback. |

### Slice 2 — Reporting and Closed Replay

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `python -m unittest tests.test_reportes_controller tests.test_accounting_report_contracts` → exit 0, `Ran 29 tests in 0.016s`, `OK` |
| Runtime harness command/scenario and exact result | Scenario exercised by unit harness: open local reports include one open `FINALIZADO_COBRADO` solo lavado worth `$8000`, apply `cerrado = FALSE`, `id_cierre IS NULL`, and `id_ingreso_generado IS NULL` filters, and closed local replay for `period_id="91"` reads one `cierres_diarios` row without querying `operaciones_servicio`, preserving `$8000` solo-lavado and `$11000` general totals. Full Desktop command `python -m unittest discover -s tests` → exit 0, `Ran 388 tests in 1.992s`, `OK` |
| Rollback boundary | Revert `controllers/reportes_controller.py`, `tests/test_reportes_controller.py`, `tests/test_registro_controller.py` fake cursor support, and this slice's task/progress artifact updates. Slice 1 additive schema columns and helpers may remain unused after rollback. |

## Command Results

| Command | Result |
|---|---|
| `python -m unittest tests.test_cierres_controller tests.test_accounting_report_contracts` (slice 1 safety net) | Exit 0; `Ran 17 tests in 0.003s`; `OK` |
| `python -m unittest tests.test_cierres_controller tests.test_accounting_report_contracts` (slice 1 RED) | Exit 1; `Ran 22 tests in 0.035s`; failures: missing helper/schema/index and closed-wash exclusion; errors: missing helper and `db_cursor` wiring |
| `python -m unittest tests.test_cierres_controller tests.test_accounting_report_contracts` (slice 1 GREEN) | Exit 0; `Ran 22 tests in 0.216s`; `OK` |
| `python -m unittest tests.test_cierres_controller tests.test_accounting_report_contracts tests.test_reportes_controller` (slice 1 touched path) | Exit 0; `Ran 38 tests in 0.126s`; `OK` |
| `python -m unittest tests.test_reportes_controller tests.test_accounting_report_contracts` (slice 2 safety net) | Exit 0; `Ran 26 tests in 0.008s`; `OK` |
| `python -m unittest tests.test_reportes_controller tests.test_accounting_report_contracts` (slice 2 RED) | Exit 1; `Ran 29 tests in 0.039s`; failures/errors: closed local replay used open queries, and report controller lacked schema ensure hook/open closure filters |
| `python -m unittest tests.test_reportes_controller tests.test_accounting_report_contracts` (slice 2 GREEN) | Exit 0; `Ran 29 tests in 0.016s`; `OK` |
| `python -m unittest discover -s tests` (first full verification) | Exit 1; `Ran 388 tests in 2.722s`; 2 failures in caja summary tests because fake cursor schema ensure support consumed queued business rows |
| `python -m unittest tests.test_reportes_controller tests.test_accounting_report_contracts tests.test_registro_controller` (post-harness fix) | Exit 0; `Ran 141 tests in 0.254s`; `OK` |
| `python -m unittest discover -s tests` (final full verification) | Exit 0; `Ran 388 tests in 1.992s`; `OK` |

## Deviations from Design

- `controllers.cierres_controller.realizar_cierre_diario` preserves the successful API close response if local persistence raises an exception, logging a warning instead of turning an already-successful authoritative API close into a Desktop failure. This preserves the pre-existing API-authority behavior but means a local DB failure can leave solo lavado rows unmarked until the local issue is corrected.
- Closed Desktop replay has no stored per-operation report item snapshot in the current `cierres_diarios` schema, so `controllers.reportes_controller` replays persisted totals exactly and emits a synthetic `lavado_solo` closure item for saved solo-lavado income instead of recalculating row-level `operaciones_servicio` details.

## Remaining Tasks

- [x] No assigned Desktop apply tasks remain for `complete-operations-pricing-gaps` slice 2.

## Rollback Notes

- Slice 2 rollback can revert `controllers/reportes_controller.py`, `tests/test_reportes_controller.py`, `tests/test_registro_controller.py`, `openspec/changes/complete-operations-pricing-gaps/tasks.md`, and this `apply-progress.md` update.
- Slice 1 rollback can additionally revert `schema.sql`, `controllers/operaciones_servicio_controller.py`, `controllers/cierres_controller.py`, `controllers/registro_controller.py`, `controllers/accounting_contracts.py`, `tests/test_cierres_controller.py`, and `tests/test_accounting_report_contracts.py`.
- Additive database columns/indexes/FK for solo-lavado closure state are non-destructive and may remain unused if code is rolled back.
