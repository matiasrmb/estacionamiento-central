# Apply Progress: Corrected Reporting Intelligence and Audit Roadmap

## Slice 0 Status

Status: completed for planning reconciliation; further implementation apply remains blocked until repo-scoped derivatives consume the unresolved rows below.

Scope boundary: planning-only. No application code, tests, canonical specs, versions, branches, commits, pushes, or PRs were changed.

Compared sources:
- Old roadmap: `openspec/changes/centro-inteligencia-reportes-auditoria-13-roadmap/`.
- Merged work readback: API `reporting_read_models.py`, Desktop `reportes_controller.py` / `views/reportes.py`, Mobile `reportes_api.dart` / `reportes_admin_screen.dart`.
- Corrected specs: this change's `specs/*/spec.md` files.

## Keep / Change / Remove / Defer Matrix

| Row | Area / behavior | Old roadmap / merged evidence | Corrected spec or design authority | Outcome | Owner repo | Derivative / follow-up | Verification | Rollback |
|---|---|---|---|---|---|---|---|---|
| 1 | API reporting endpoints and admin guard | Old roadmap kept `/reporting/*`; API endpoint tests include admin-only closed export coverage. | Design keeps API as canonical contract and preserves `/reporting/*` admin-only shape. | Keep | `estacionamiento-central-api` | API derivative handoff, Phase 2. | API focused endpoint tests for admin guard, unsupported filters as 422, bad closure/period IDs. | Revert API derivative endpoint/read-model changes only. |
| 2 | Metric names and revenue semantics | Merged API still exposes `operational_income_total`, `operational_net_total`, and `mensualidad_sales_total`. | Corrected API spec requires `collected_sources_total`, `operational_expense_total`, `net_revenue_total`, `monthly_payments_collected_total`, and `vehicle_movement_count`; net revenue is all collected sources minus expenses. | Change | `estacionamiento-central-api`, then Desktop/Mobile consumers | API derivative must add corrected catalog and compatibility mapping; Desktop/Mobile derivatives must render canonical API labels. | API catalog/read-model tests; Desktop controller/view tests; Mobile widget tests. | Revert repo-specific catalog/consumer derivative. |
| 3 | Period truth | Old roadmap used closure-to-closure operational days; merged API has closure period helpers but consumers still use current/open dashboard labels. | Corrected specs make closure/journey boundaries official truth and calendar grouping secondary. | Change | `estacionamiento-central-api` | API derivative defines period `{id,start,end,state,axis}` and `calendar_secondary`; Desktop/Mobile render it. | API journey-cross-midnight/current-journey tests; Desktop/Mobile label tests. | Revert period-contract derivative changes. |
| 4 | Capacity | Merged API has `TOTAL_PARKING_SPACES = 50` and capacity computed from active monthly customers. | Corrected API spec requires configurable current capacity with default/current 50 and historical periods labeled `historical-capacity-limited`. | Change | `estacionamiento-central-api` | API derivative chooses config source/key and emits corrected capacity metadata. | API capacity tests for configured 50 and historical-limited state. | Revert capacity config/read-model derivative. |
| 5 | Desktop local fallback dashboard | Merged Desktop marks fallback `source_state=local_fallback` and `completeness.state=incomplete`. | Corrected dashboard spec requires local fallback to be incomplete, local, non-official, and never closure truth. | Change | `estacionamiento-central` | Desktop derivative adds explicit non-official/official=false contract and UI warning. | Desktop controller/view tests for fallback labels and warning visibility. | Revert Desktop controller/view fallback derivative. |
| 6 | Desktop full Intelligence Center | Old roadmap made Desktop/API the full center; merged Desktop contains closed report load/export widgets. | Corrected specs keep Desktop as full center but exports may be deferred from 1.3.0. | Keep/change | `estacionamiento-central` | Keep full-center navigation; change export promises according to export row. | Desktop view tests for full-center navigation and deferred export state when applicable. | Revert Desktop derivative widgets/copy only. |
| 7 | Mobile reporting dashboard | Merged Mobile consumes `/reporting/metric-catalog` and `/reporting/dashboard`, and shows a deferral notice for closed reports/exports. | Corrected specs keep Mobile dashboard-only quick consultation and change labels to canonical API labels; no full-center/export flows. | Keep/change | `estacionamiento_central_mobile` | Mobile derivative keeps quick consultation but renames cards to corrected catalog and confirms no closed/export flows. | `flutter test` focused admin reporting tests and `flutter analyze` in Mobile derivative. | Revert Mobile reporting derivative files. |
| 8 | PDF/XLSX exports | Old roadmap made PDF/XLSX exports required; merged API/Desktop have PDF/XLSX export paths. | Corrected reproducible reports spec says PDF/XLSX may be deferred to 1.3.x and must not block 1.3.0. | Defer | `estacionamiento-central-api`, `estacionamiento-central`, later Installer only if packaging assets appear | Export derivative in 1.3.x; 1.3.0 derivative hides/removes blocking export promises. | API/Desktop tests prove exports do not block 1.3.0 readiness; later export tests verify metadata. | Revert export-specific derivative or hide export UI/route changes. |
| 9 | CSV spreadsheet compatibility | Merged API still defines `LEGACY_EXPORT_FORMATS = {"csv"}` and tests legacy CSV metadata. | Corrected spec removes CSV as canonical spreadsheet target and requires XLSX when spreadsheet export is offered. | Remove | `estacionamiento-central-api`, `estacionamiento-central`, `estacionamiento_central_mobile` | API derivative removes CSV from canonical contract or marks it non-advertised legacy-only; clients must not advertise CSV. | API endpoint/export tests; Desktop/Mobile UI tests assert no CSV promise. | Revert CSV-removal derivative if compatibility policy changes. |
| 10 | Audit slice | Old roadmap planned inventory/readiness and deferred transversal event log; merged API exposes audit inventory and unsupported event-sourcing behaviors. | Corrected admin spec requires a first serious audit slice covering closures, payments, expenses, users/sessions, prints, and deterministic anomalies without event sourcing. | Change | `estacionamiento-central-api`, then Desktop/Mobile display surfaces | API derivative defines audit coverage/anomalies; Desktop/Mobile surface limitations as quick/full-center appropriate. | API audit inventory/anomaly tests; client tests for limitation labels. | Revert audit derivative read-model/client changes. |

## Unresolved Rows Blocking Further Apply

| Row | Owner repo | Outcome | Derivative | Verification | Rollback |
|---|---|---|---|---|---|
| Capacity configuration source/key | `estacionamiento-central-api` | Change: replace immutable `TOTAL_PARKING_SPACES = 50` with configurable current capacity defaulting to 50; label missing historical capacity as `historical-capacity-limited`. | API derivative handoff, Phase 2. | API read-model/repository tests for configured current capacity and historical-limited metadata. | Revert API capacity config/read-model changes only. |
| Export treatment for already merged API/Desktop PDF/XLSX paths | `estacionamiento-central-api`, `estacionamiento-central` | Defer: decide in derivatives whether to hide, move, or keep non-blocking export paths; 1.3.0 readiness must not depend on them. | API derivative handoff and Desktop derivative. | API/Desktop tests prove export absence/defer state does not block reporting readiness; later 1.3.x export derivative tests metadata. | Revert or hide export-specific API/Desktop changes without touching reporting core. |
| CSV compatibility policy | `estacionamiento-central-api` with Desktop/Mobile consumers | Remove from canonical contract: CSV must not be advertised as spreadsheet output; legacy compatibility, if retained, must be non-canonical. | API derivative handoff, then client derivative assertions. | API export/endpoint tests and client UI tests assert no CSV promise. | Revert CSV policy derivative if product explicitly restores compatibility. |
| Corrected metric rename propagation | `estacionamiento-central-api`, `estacionamiento-central`, `estacionamiento_central_mobile` | Change: migrate from old `operational_*` / `mensualidad_sales_total` catalog to corrected names and labels, with compatibility mapping if needed. | API derivative first; Desktop second; Mobile third. | API catalog tests and Desktop/Mobile rendering tests use corrected labels. | Revert repo-specific catalog/label derivative changes. |

## Work Unit Evidence

| Evidence | Required value |
|---|---|
| Focused readback command and exact result | `python -c "from pathlib import Path; base=Path('openspec/changes/centro-inteligencia-reportes-auditoria-13-corrected-roadmap'); tasks=(base/'tasks.md').read_text(encoding='utf-8'); progress=(base/'apply-progress.md').read_text(encoding='utf-8'); checks={'tasks_1_1_checked':'- [x] 1.1' in tasks,'tasks_1_2_checked':'- [x] 1.2' in tasks,'tasks_1_3_checked':'- [x] 1.3' in tasks,'tasks_2_1_pending':'- [ ] 2.1' in tasks,'tasks_3_1_pending':'- [ ] 3.1' in tasks,'tasks_4_1_pending':'- [ ] 4.1' in tasks,'tasks_5_1_pending':'- [ ] 5.1' in tasks,'progress_exists':(base/'apply-progress.md').exists(),'matrix_present':'## Keep / Change / Remove / Defer Matrix' in progress,'evidence_present':'## Work Unit Evidence' in progress,'unresolved_present':'## Unresolved Rows Blocking Further Apply' in progress}; print('\\n'.join(f'{k}: {v}' for k,v in checks.items())); raise SystemExit(0 if all(checks.values()) else 1)"` from repo root. Result: exit 0; all checks printed `True` for tasks 1.1-1.3 checked, tasks 2.1/3.1/4.1/5.1 pending, `apply-progress.md` exists, matrix present, evidence present, and unresolved rows present. |
| Runtime harness command/scenario and exact result | N/A: Slice 0 is planning-only reconciliation. No runtime boundary exists because application code, tests, and executable paths are explicitly out of scope. |
| Rollback boundary | Remove `openspec/changes/centro-inteligencia-reportes-auditoria-13-corrected-roadmap/apply-progress.md` and revert only task checkboxes 1.1-1.3 in this change's `tasks.md`. |

## Phase 2 API Derivative Handoff Status

Status: completed for planning handoff only. The API repo remains read-only from this Desktop-root apply work unit; no sibling repository files, application code, tests, branches, commits, pushes, or PRs were changed.

Planning status update: the prior tasks artifact recorded `Delivery strategy: ask-on-risk` and `Chain strategy: pending`. The parent session already selected `auto-chain` with `stacked-to-main`, so `tasks.md` was updated to record that resolved planning status while preserving the high 400-line budget risk and chained review boundary.

Created artifact:
- `openspec/changes/centro-inteligencia-reportes-auditoria-13-corrected-roadmap/api-derivative-handoff.md`.

Completed Phase 2 tasks:
- [x] 2.1 Created the API repo-scoped derivative handoff for admin guard, filter 422, bad period IDs, net revenue, monthly-payment timing, solo lavado, capacity, and anomalies.
- [x] 2.2 Referenced `../estacionamiento-central-api/app/repositories/reporting_read_models.py` as read-only evidence for metric names, source/capacity/audit/anomaly contracts, and export deferral.
- [x] 2.3 Referenced `../estacionamiento-central-api/app/repositories/reporting_repo.py` as read-only evidence for closure/journey truth, current journey, `fecha_pago`, capacity default 50, and audit inventory.
- [x] 2.4 Referenced `../estacionamiento-central-api/app/api/v1/endpoints/reporting.py` as read-only evidence for route/admin contracts and required API derivative tests.

### Phase 2 Evidence Matrix

| Area | Read-only evidence | API derivative instruction |
|---|---|---|
| Admin guard and 422 behavior | `reporting.py` routes use `require_role("admin")`; unsupported dashboard filters and plate-history validation return 422. | Preserve admin-only route contracts and add focused API derivative tests for non-admin access, unsupported filters, malformed periods, and bad identifiers. |
| Corrected metrics and net revenue | `reporting_read_models.py` and `reporting_repo.py` still expose old `operational_*` / `mensualidad_sales_total` names. | Migrate canonical names to corrected spec names and compute net revenue from all collected sources minus expenses. |
| Monthly payments and solo lavado | `reporting_repo.py` reads monthly payment timing from `fecha_pago` and includes charged solo lavado via `operaciones_servicio`. | Keep collection-journey timing and include charged solo lavado in collected sources while excluding uncharged active washes. |
| Capacity | `reporting_read_models.py` and `reporting_repo.py` use hard-coded 50 capacity values. | Replace immutable capacity with configurable current capacity defaulting to 50 and historical-limited labels. |
| Audit and anomalies | `reporting_read_models.py` exposes deterministic discrepancy/anomaly and audit inventory helpers; `reporting_repo.py` inventories existing sources. | Keep deterministic existing-source audit/anomaly behavior without event sourcing or formal-accounting claims. |
| Export deferral and CSV policy | `reporting_read_models.py` keeps canonical PDF/XLSX formats and legacy CSV compatibility. | Do not let exports block 1.3.0; keep CSV non-canonical/legacy-only if retained. |

### Phase 2 TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 2.1 | N/A | Structural planning artifact | N/A: no runtime code modified | N/A: no production code behavior introduced | Structural readback required below | N/A: single planning artifact output | N/A |
| 2.2 | N/A | Structural evidence reference | N/A: read-only sibling evidence | N/A: no production code behavior introduced | Structural readback required below | N/A: evidence path presence check | N/A |
| 2.3 | N/A | Structural evidence reference | N/A: read-only sibling evidence | N/A: no production code behavior introduced | Structural readback required below | N/A: evidence path presence check | N/A |
| 2.4 | N/A | Structural evidence reference | N/A: read-only sibling evidence | N/A: no production code behavior introduced | Structural readback required below | N/A: evidence path presence check | N/A |

### Phase 2 Work Unit Evidence

| Evidence | Required value |
|---|---|
| Focused readback command and exact result | `python -c "from pathlib import Path; base=Path('openspec/changes/centro-inteligencia-reportes-auditoria-13-corrected-roadmap'); tasks=(base/'tasks.md').read_text(encoding='utf-8'); progress=(base/'apply-progress.md').read_text(encoding='utf-8'); handoff=(base/'api-derivative-handoff.md').read_text(encoding='utf-8'); checks={'tasks_2_1_checked':'- [x] 2.1' in tasks,'tasks_2_2_checked':'- [x] 2.2' in tasks,'tasks_2_3_checked':'- [x] 2.3' in tasks,'tasks_2_4_checked':'- [x] 2.4' in tasks,'tasks_3_1_pending':'- [ ] 3.1' in tasks,'handoff_exists':(base/'api-derivative-handoff.md').exists(),'read_models_ref':'../estacionamiento-central-api/app/repositories/reporting_read_models.py' in handoff,'repo_ref':'../estacionamiento-central-api/app/repositories/reporting_repo.py' in handoff,'endpoint_ref':'../estacionamiento-central-api/app/api/v1/endpoints/reporting.py' in handoff,'phase2_progress':'## Phase 2 API Derivative Handoff Status' in progress,'slice0_preserved':'## Keep / Change / Remove / Defer Matrix' in progress,'strategy_resolved':'auto-chain' in tasks and 'stacked-to-main' in tasks}; print('\\n'.join(f'{k}: {v}' for k,v in checks.items())); raise SystemExit(0 if all(checks.values()) else 1)"` from repo root. Result: exit 0; all checks printed `True` for tasks 2.1-2.4 checked, task 3.1 still pending, handoff file exists, all three API read-only evidence paths referenced, Phase 2 progress present, Slice 0 matrix preserved, and auto-chain/stacked-to-main strategy recorded. |
| Runtime harness command/scenario and exact result | N/A: Phase 2 is a planning-only API derivative handoff. No runtime boundary exists inside the Desktop repo; API runtime tests belong to the API derivative. |
| Rollback boundary | Remove `api-derivative-handoff.md`, revert only Phase 2 task checkboxes 2.1-2.4 in `tasks.md`, and remove only this Phase 2 section from `apply-progress.md`. |

## Phase 3 Desktop Derivative Status

Status: completed for the Desktop runtime derivative. Desktop remains the full administrative center consuming canonical API read models; local fallback is degraded consultation only and is labeled incomplete, local, and non-official.

Completed Phase 3 tasks:
- [x] 3.1 Added Desktop controller/view tests for corrected canonical labels, full-center navigation, state/capacity visibility, fallback warnings, and deferred exports.
- [x] 3.2 Updated `controllers/reportes_controller.py` to preserve normalized API metadata and mark local API fallback as `local_fallback`, incomplete, `official=false`, and non-official via warnings.
- [x] 3.3 Updated `views/reportes.py` to show the Desktop Intelligence Center label, render fallback warnings and capacity state, and hide 1.3.0 closed PDF/XLSX export buttons while noting 1.3.x deferral.

### Phase 3 TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 3.1 | `tests/test_reportes_controller.py`, `tests/test_reportes_view.py` | Unit/view with mocks | ✅ `python -m unittest tests.test_reportes_controller tests.test_reportes_view` ran 28 tests OK before edits. | ✅ New/updated tests failed first: 30 tests with 2 failures and 4 errors for missing `official`, warnings, full-center label, hidden exports, and capacity state. | ✅ Focused command later ran 30 tests OK. | ✅ Covered API labels, API metadata, fallback metadata, fallback UI warning, full-center navigation, capacity state, and export deferral. | ➖ None beyond minimal behavior additions. |
| 3.2 | `tests/test_reportes_controller.py` | Unit | ✅ Same focused safety net. | ✅ Controller tests required API metadata and non-official fallback fields not yet returned. | ✅ Focused command later ran 30 tests OK. | ✅ API success and API-unavailable fallback paths covered. | ➖ None needed. |
| 3.3 | `tests/test_reportes_view.py` | Unit/view with mocks | ✅ Same focused safety net. | ✅ View tests required full-center label, fallback warning text, capacity state, and hidden export buttons before implementation. | ✅ Focused command later ran 30 tests OK. | ✅ API dashboard, local fallback, capacity-state helper, closed-report load, and deferred-export UI paths covered. | ➖ None needed. |

### Phase 3 Work Unit Evidence

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `python -m unittest tests.test_reportes_controller tests.test_reportes_view` from repo root. Baseline before edits: exit 0, 28 tests OK. RED after test edits: exit 1, 30 tests with 2 failures and 4 errors. GREEN after implementation: exit 0, 30 tests OK. |
| Runtime harness command/scenario and exact result | `python -m unittest discover -s tests` from repo root. Result recorded in final apply response after Phase 3 updates. |
| Rollback boundary | Revert only Phase 3 changes in `controllers/reportes_controller.py`, `views/reportes.py`, `tests/test_reportes_controller.py`, `tests/test_reportes_view.py`; revert Phase 3 task checkboxes 3.1-3.3 in `tasks.md`; remove only this Phase 3 section from `apply-progress.md`. |

## Later Work Status

## Phase 4 Mobile Derivative Handoff Status

Status: completed for planning handoff only. The Mobile repo remains read-only from this Desktop-root apply work unit; no sibling repository files, application code, tests, branches, commits, pushes, or PRs were changed.

Created artifact:
- `openspec/changes/centro-inteligencia-reportes-auditoria-13-corrected-roadmap/mobile-derivative-handoff.md`.

Completed Phase 4 tasks:
- [x] 4.1 Created the Mobile repo-scoped derivative handoff for quick consultation, canonical labels, matched totals, and no full-center/export flows.
- [x] 4.2 Referenced `../estacionamiento_central_mobile/lib/features/admin/reportes/**` as read-only evidence for canonical payload consumption and quick-consultation UI boundaries.
- [x] 4.3 Defined Mobile verification expectations: `flutter test`, `flutter analyze`, and runtime harness availability in the Mobile derivative.

### Phase 4 Evidence Matrix

| Area | Read-only evidence | Mobile derivative instruction |
|---|---|---|
| Canonical payload consumption | `reportes_api.dart` calls `/reporting/metric-catalog` and `/reporting/dashboard`, then maps API metric names into dashboard cards. | Keep API-backed dashboard consumption, migrate from legacy metric names to corrected canonical names, and ensure Mobile card totals match API payload values without local financial recalculation. |
| Quick-consultation UI boundary | `reportes_admin_screen.dart` is admin-gated, shows current catalog/journey/cards, and displays a deferred closed-report/export notice without export buttons or full-center navigation. | Preserve Mobile as quick consultation only; do not add Desktop-equivalent full center, closed-report management, PDF/XLSX/CSV export flows, or audit-management workflows in the 1.3.0 Mobile derivative. |
| Verification expectations | `openspec/config.yaml` lists Mobile `flutter test`, `flutter analyze`, and Flutter widget/unit coverage. | The Mobile derivative must run `flutter test` and `flutter analyze`, and must explicitly record runtime harness availability or `N/A` with reason. |

### Phase 4 TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 4.1 | N/A | Structural planning artifact | N/A: no runtime code modified | N/A: no production behavior introduced | Structural readback required below | N/A: single planning artifact output | N/A |
| 4.2 | N/A | Structural evidence reference | N/A: read-only sibling evidence | N/A: no production behavior introduced | Structural readback required below | N/A: evidence path presence check | N/A |
| 4.3 | N/A | Structural verification plan | N/A: no runtime code modified | N/A: no production behavior introduced | Structural readback required below | N/A: verification expectation presence check | N/A |

### Phase 4 Work Unit Evidence

| Evidence | Required value |
|---|---|
| Focused readback command and exact result | `python -c "from pathlib import Path; base=Path('openspec/changes/centro-inteligencia-reportes-auditoria-13-corrected-roadmap'); tasks=(base/'tasks.md').read_text(encoding='utf-8'); progress=(base/'apply-progress.md').read_text(encoding='utf-8'); handoff=(base/'mobile-derivative-handoff.md').read_text(encoding='utf-8'); checks={'tasks_4_1_checked':'- [x] 4.1' in tasks,'tasks_4_2_checked':'- [x] 4.2' in tasks,'tasks_4_3_checked':'- [x] 4.3' in tasks,'tasks_5_1_pending':'- [ ] 5.1' in tasks,'handoff_exists':(base/'mobile-derivative-handoff.md').exists(),'api_ref':'../estacionamiento_central_mobile/lib/features/admin/reportes/data/reportes_api.dart' in handoff,'screen_ref':'../estacionamiento_central_mobile/lib/features/admin/reportes/presentation/reportes_admin_screen.dart' in handoff,'quick_consultation':'quick consultation' in handoff,'canonical_metrics':'collected_sources_total' in handoff and 'net_revenue_total' in handoff and 'monthly_payments_collected_total' in handoff,'verification':'flutter test' in handoff and 'flutter analyze' in handoff and 'runtime harness' in handoff,'phase4_progress':'## Phase 4 Mobile Derivative Handoff Status' in progress,'slice0_preserved':'## Keep / Change / Remove / Defer Matrix' in progress,'phase2_preserved':'## Phase 2 API Derivative Handoff Status' in progress,'phase3_preserved':'## Phase 3 Desktop Derivative Status' in progress}; print('\\n'.join(f'{k}: {v}' for k,v in checks.items())); raise SystemExit(0 if all(checks.values()) else 1)"` from repo root. Result: exit 0; all checks printed `True` for Phase 4 tasks checked, Phase 5 still pending, handoff file exists, both Mobile read-only evidence paths referenced, quick-consultation and canonical metric requirements present, `flutter test`/`flutter analyze`/runtime harness expectations present, and Slice 0/Phase 2/Phase 3 progress preserved. |
| Runtime harness command/scenario and exact result | N/A: Phase 4 is a planning-only Mobile derivative handoff. No runtime boundary exists inside the Desktop repo; Mobile runtime verification belongs to the later `estacionamiento_central_mobile` derivative. |
| Rollback boundary | Remove `mobile-derivative-handoff.md`, revert only Phase 4 task checkboxes 4.1-4.3 in `tasks.md`, and remove only this Phase 4 section from `apply-progress.md`. |

## Later Work Status

Phase 5 remains pending. Do not start Installer, version, branch, commit, push, or PR work from this Phase 4 artifact. Mobile application-code work must occur only in a repo-scoped Mobile derivative.
