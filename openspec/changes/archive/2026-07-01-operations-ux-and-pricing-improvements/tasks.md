# Tasks: Operations UX and Pricing Improvements

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~1,750-2,600 total; slices ~160-380 each |
| Estimated by slice | PR1 quote 220-320; PR2 wash pricing 260-380; PR3 wash-only accounting 350-400; PR4 Desktop wash/tickets 280-380; PR5 Mobile unified 320-400; PR6 safe user delete 180-280; PR7 printer diagnostics/docs 160-260 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | Feature Branch Chain: tracker branch, then PR1 -> PR2 -> PR3 -> PR4 -> PR5 -> PR6 -> PR7 |
| Delivery strategy | ask-always |
| Chain strategy | feature-branch-chain |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Stateless quote contracts | PR1 base = tracker | No billable rows; rollback disables quote UI/API. |
| 2 | Wash pricing foundation | PR2 base = PR1 | Separate wash pricing from parking tariffs. |
| 3 | Wash-only accounting | PR3 base = PR2 | Tests for cierre/caja/report before UI. |
| 4 | Desktop solo lavado/tickets | PR4 base = PR3 | Preserve ingreso+lavado; additive UI. |
| 5 | Mobile unified operation | PR5 base = PR4 | Flutter tests/analyze required. |
| 6 | Safe user delete | PR6 base = PR5 | Deactivate fallback; no history loss. |
| 7 | Printer diagnostics guidance | PR7 base = PR6 | Docs/diagnostics follow-up if code budget is tight. |

## Phase 1: Domain, Data, and Test Foundations

- [x] 1.1 Goal: add RED quote tests; Files: Desktop `tests/`, API `tests/`; Deps: none; Validation: estadía ignores vehicle size, monthly missing amount requires input; Rollback: remove quote endpoints/UI only; Areas: Desktop/API.
- [x] 1.2 Goal: create additive wash pricing migration/contracts; Files: Desktop `schema.sql`, API migrations/schemas/repos; Deps: 1.1; Validation: active type snapshots price, referenced type deactivates; Rollback: leave unused tables; Areas: DB/API/Desktop.
- [x] 1.3 Goal: add RED accounting/report tests before UI; Files: Desktop/API `tests/`; Deps: 1.2; Validation: ingreso+lavado unchanged, solo lavado revenue separate, `total_general` includes it; Rollback: tests guard revert; Areas: Desktop/API/DB.
- [x] 1.4 Goal: add `operaciones_servicio` state model; Files: DB migrations, API schemas/repos, Desktop controller helpers; Deps: 1.2-1.3; Validation: ACTIVO -> FINALIZADO_COBRADO or CONVERTIDO_ESTADIA; Rollback: disable new routes; Areas: DB/API/Desktop.

## Phase 2: Review Slices / Core Implementation

- [x] 2.1 PR1 Goal: implement quote preview; Files: API `/cotizaciones/preview`, Desktop quote controller/view; Deps: 1.1; Validation: `python -m unittest discover -s tests`; Rollback: hide quote entrypoint; Areas: Desktop/API.
- [x] 2.2 PR2 Goal: implement wash-only pricing config CRUD; Files: API `/tipos-lavado`, `/tipos-vehiculo-lavado`, Desktop config; Deps: 1.2; Validation: wash config affects only lavado, not parking salida/quote; Rollback: seed config keys remain; Areas: Desktop/API/DB/Mobile contracts.
- [x] 2.3 PR3 Goal: implement solo lavado API/domain and cierre/report semantics; Files: API `/lavados/solo/*`, cierres/report repos, Desktop accounting helpers; Deps: 1.3-1.4; Validation: solo charge-now and convert-to-stay tests pass; Rollback: block new endpoints; Areas: API/Desktop/DB.
- [x] 2.4 PR4 Goal: implement Desktop solo lavado UX and detailed tickets; Files: `views/registro.py`, controllers, `utils/ticket.py`; Deps: 2.3; Validation: manual + tests preserve ingreso+lavado and ticket totals; Rollback: hide solo lavado buttons; Areas: Desktop/API ticket payloads.

## Phase 3: Mobile, Users, and Printer Support

- [x] 3.1 PR5 Goal: add mobile unified operation screen and Lavados/Baño search; Files: Mobile `lib/features/operacion_diaria/`, operations APIs/state/widgets; Deps: 2.3; Validation: `flutter test`, `flutter analyze`, newest-first, blocked-salida, inline ingreso/salida/lavado action tests, active-wash finalization, and unified Sunmi ticket print coordination; Rollback: keep old modules/routes; Areas: Mobile/API. Correction: primary unified actions now execute inline instead of routing to old modules; unified ingreso/salida reuse the old working Sunmi ticket formatter/service path; active lavado can be finalized from record actions. Executor re-run confirmed `flutter test` 13/13 and `flutter analyze` clean.
- [x] 3.2 PR6 Goal: add safe user delete; Files: API `usuarios`, Desktop `usuarios_controller.py`/`views/usuarios.py`; Deps: 1.4; Validation: no-activity hard delete, activity deactivates, current/last admin blocked; Rollback: remove delete action, keep deactivate; Areas: Desktop/API/DB. Strict TDD added API/Desktop tests first, then implementation; validation passed with API `python -m unittest discover -s tests` (61 tests) and Desktop `python -m unittest discover -s tests` (136 tests). Correction: optional/additive activity tables missing from older DBs are skipped/logged instead of blocking hard delete, required legacy checks remain strict, and Desktop `USER_DELETE_ERROR` is shown as internal error requiring logs; revalidation passed with API full suite (62 tests) and Desktop full suite (138 tests).
- [x] 3.3 PR7 Goal: add printer diagnostics/test-print guidance; Files: Desktop printer config, API printer-agent diagnostics, installer/docs README/setup; Deps: none; Validation: success/failure diagnostic scenarios, manual Sumatra/printer test; Rollback: docs-only fallback if code deferred; Areas: Desktop/API/Installer/Docs. Strict TDD added Desktop/API diagnostic helpers/tests first; installer diagnostics bundle now includes printer info and docs describe Sumatra/PRINTER_NAME/vendor-driver support. Focused validation passed with Desktop `python -m unittest tests.test_printer_diagnostics`, API `python -m unittest tests.test_print_agent_diagnostics tests.test_print_agent_service_main`, installer `collect_diagnostics.ps1` bundle creation, and `check_production_health.ps1 -Action DryRun`. Manual physical Sumatra/printer test remains recommended on the target thermal printer.

## Phase 4: Integration and Verification

- [x] 4.1 Verify each PR independently with repo commands: Desktop/API `python -m unittest discover -s tests`; Mobile `flutter test` + `flutter analyze`; Installer manual diagnostics note. Final SDD verify passed Desktop full suite (140 tests), API full suite (65 tests), Mobile `flutter test` (13 tests), Mobile `flutter analyze`, and installer PowerShell parser checks for printer diagnostics scripts.
- [x] 4.2 Before final tracker merge, run cross-flow regression: ingreso, ingreso+lavado, salida, solo lavado charge-now, wash→stay salida, cierre, reports, and ticket totals. Final SDD verify found passing automated coverage for quote, wash pricing, solo lavado lifecycle/accounting, mobile unified operation, safe user delete, and printer diagnostics; manual user evidence accepted unified mobile actions/tickets, bathroom action, safe delete, and normal/PDF printer diagnostics. Physical thermal printer remains hardware/driver-dependent because the current generic driver does not appear in Windows `Get-Printer`.
