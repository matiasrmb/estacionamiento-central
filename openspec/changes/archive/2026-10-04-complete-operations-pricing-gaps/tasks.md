# Tasks: Complete Operations Pricing Gaps

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 420-620 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 schema/closure marking -> PR 2 reporting/closed replay |
| Delivery strategy | ask-on-risk; resolved by parent as chained PR delivery |
| Chain strategy | feature-branch-chain |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Add closure schema ensure and one-time solo-lavado close marking | PR 1 | `python -m unittest tests.test_cierres_controller tests.test_accounting_report_contracts` | Daily close with one `FINALIZADO_COBRADO` solo lavado after API success | Revert `schema.sql`, `controllers/operaciones_servicio_controller.py`, `controllers/cierres_controller.py`, related tests |
| 2 | Add report inclusion/exclusion and closed-reference replay | PR 2 | `python -m unittest tests.test_reportes_controller tests.test_accounting_report_contracts` | Open local report and closed replay for saved closure containing solo lavado | Revert `controllers/reportes_controller.py`, optional `controllers/accounting_contracts.py`, related tests |

## Phase 1: RED - Schema and Closure Marking

- [x] 1.1 Add failing schema ensure tests in `tests/test_cierres_controller.py` for missing `operaciones_servicio.id_cierre` support and idempotent repeat execution.
- [x] 1.2 Add failing closure tests in `tests/test_cierres_controller.py` for charged solo lavado inclusion, `cerrado/id_cierre` marking, later-close exclusion, and API-failure no-mark.
- [x] 1.3 Add failing contract test in `tests/test_accounting_report_contracts.py` proving `cerrado` solo lavados are excluded from pending closure totals.

## Phase 2: GREEN - Schema Ensure and One-Time Close

- [x] 2.1 Update `schema.sql` with additive `operaciones_servicio.id_cierre`, index, and FK to `cierres_diarios`; keep rollback non-destructive.
- [x] 2.2 Add `asegurar_schema_operaciones_servicio_cierre`, `obtener_lavados_solos_pendientes_cierre`, and `marcar_lavados_solos_cerrados` in `controllers/operaciones_servicio_controller.py`.
- [x] 2.3 Wire `controllers/cierres_controller.py` after successful `crear_cierre_api(token)` to persist a local closure reference, include solo-lavado totals, and mark selected rows once.
- [x] 2.4 Ensure `controllers/registro_controller.py` prepares solo-lavado closure state before caja summary reads new closure fields.
- [x] 2.5 Run focused GREEN command: `python -m unittest tests.test_cierres_controller tests.test_accounting_report_contracts`.

## Phase 3: RED/GREEN - Reporting and Closed Replay

- [x] 3.1 Add failing report tests in `tests/test_reportes_controller.py` for charged solo lavado inclusion and `ACTIVO`/`CONVERTIDO_ESTADIA` exclusion.
- [x] 3.2 Add failing closed replay test in `tests/test_reportes_controller.py` proving saved closure totals/items win over later operational row edits.
- [x] 3.3 Update `controllers/reportes_controller.py` to ensure schema before solo-lavado queries, filter pending/open rows correctly, and replay closed references when period state/id is supplied.
- [x] 3.4 Update `controllers/accounting_contracts.py` only if shared normalization is needed by the new tests. No production change was needed; existing totals normalization already satisfied the new report path.
- [x] 3.5 Run focused GREEN command: `python -m unittest tests.test_reportes_controller tests.test_accounting_report_contracts`.

## Phase 4: REFACTOR and Verification

- [x] 4.1 Refactor duplicated solo-lavado filters without changing tested behavior; keep API and Mobile untouched.
- [x] 4.2 Run full Desktop suite: `python -m unittest discover -s tests`.
- [x] 4.3 Record rollback notes: controller/helper/test changes revert cleanly; additive schema columns may remain unused.
