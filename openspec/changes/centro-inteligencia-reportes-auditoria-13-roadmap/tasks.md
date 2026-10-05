# Tasks: Centro Inteligencia Reportes Auditoria 1.3 Roadmap

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 650-950 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | Feature branch chain: tracker branch → PR 1 API contract/read models → PR 2 Desktop Intelligence Center → PR 3 Mobile limited scope/packaging check |
| Delivery strategy | ask-on-risk |
| Chain strategy | feature-branch-chain |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | API canonical reporting, exports, audit inventory | PR 1 | `python -m unittest tests.test_reporting_read_models tests.test_reporting_exports tests.test_reporting_endpoints tests.test_reporting_closed_reports` | Call `/api/v1/reporting/dashboard` and closed export as admin | API reporting files only |
| 2 | Desktop normalization and Intelligence Center UI | PR 2 | `python -m unittest tests.test_reportes_controller tests.test_reportes_view` | Open Desktop reports view against API | Desktop controller/view only |
| 3 | Mobile dashboard-only scope plus installer check | PR 3 | `flutter test test/features/admin/reportes/reportes_mensualidades_test.dart && flutter analyze` | Mobile admin reports screen; installer N/A unless assets change | Mobile reportes files; installer only if needed |

## Repo Authority Notes

- Desktop repo is the active OpenSpec root. API, Mobile, and Installer tasks require explicit edit authority before apply.
- User selected feature-branch-chain PRs. Use a tracker branch for integration; PR #1 targets the tracker branch, PR #2 targets PR #1's branch, and PR #3 targets PR #2's branch so diffs stay focused. Grant edit authority only for Desktop, API, and Mobile when their work units are authorized; Installer remains conditional until a phase proves packaging edits are required.
- Threat matrix: N/A, so no security RED tasks are required.

## Derivative Roadmap Status

- Native umbrella apply remains blocked by `blocked(cross_common_dir_runtime_target)` because this roadmap spans sibling repositories with independent Git/runtime accounting.
- Runtime implementation is intentionally split into repo-scoped derivative changes; do not use this umbrella task list to claim cross-repo completion.
- Completed derivative `centro-inteligencia-reportes-auditoria-api` landed the API semantic/export/audit-inventory slice: canonical reporting semantics, active-monthly capacity source, CSV legacy-only policy, PDF/XLSX closed-report exports, and existing-source audit inventory.
- Completed derivative `centro-inteligencia-reportes-auditoria-api-filters-sorting-pagination` landed backend filters, deterministic sorting, and pagination for canonical reporting operation drill-down/list endpoints.
- Completed derivative `centro-inteligencia-reportes-auditoria-api-historical-anomalies-statistics` landed API historical plate lookup, anomaly/statistics endpoints, and audit inventory remediation for reporting-relevant source tables.
- Completed derivative `centro-inteligencia-reportes-auditoria-desktop-intelligence-center` landed Desktop canonical dashboard normalization/rendering, incomplete/local fallback metadata, and non-operational closed/export roadmap boundaries.
- Completed derivative `centro-inteligencia-reportes-auditoria-desktop-closed-reports-exports` landed Desktop API-backed closed report loading and PDF/XLSX export actions.
- Completed derivative `centro-inteligencia-reportes-auditoria-mobile-limited-scope` landed Mobile dashboard-only reporting, 1.3.x deferral copy, and no closed/export entry points.
- Installer/package edits were not required by the completed API/Desktop/Mobile slices because no XLSX/PDF dependency or asset packaging change was introduced.
- Release-hardening work remains intentionally deferred until there is a concrete release scope; any further reporting Intelligence Center expansion should be planned as a new repo-scoped derivative rather than reopening this cross-repo roadmap.

## Phase 1: API Contract and Decisions — landed by `centro-inteligencia-reportes-auditoria-api`

- [x] 1.1 Add RED API tests in `../estacionamiento-central-api/tests/test_reporting_read_models.py` for operational net, closure periods, capacity, and completeness labels. Completed in archived API derivative; verification passed 28 unittest tests.
- [x] 1.2 Resolve active monthly customer source and encode it in `../estacionamiento-central-api/app/repositories/reporting_repo.py` with tests. Completed as active monthly vehicles.
- [x] 1.3 Decide whether legacy CSV remains compatibility-only or rejected; encode endpoint expectations in `../estacionamiento-central-api/tests/test_reporting_endpoints.py`. Completed as CSV legacy-only.
- [x] 1.4 Update `../estacionamiento-central-api/app/repositories/reporting_read_models.py` for catalog, completeness, capacity, audit inventory, and PDF/XLSX metadata. Completed in archived API derivative.
- [x] 1.5 Update `../estacionamiento-central-api/app/repositories/reporting_repo.py` for journey-collected mensualidades, closure bounds, and historical source state. Completed in archived API derivative.
- [x] 1.6 Update `../estacionamiento-central-api/app/api/v1/endpoints/reporting.py` to validate period filters and `pdf`/`xlsx` exports under admin guard. Completed for the first API slice; operation-list filters/sorting/pagination are split to `centro-inteligencia-reportes-auditoria-api-filters-sorting-pagination`.

## Phase 2: Desktop Intelligence Center

- [x] 2.1 Add RED Desktop tests in `tests/test_reportes_controller.py` for API normalization and incomplete local fallback labels. Completed in archived Desktop derivative; focused tests passed.
- [x] 2.2 Update `controllers/reportes_controller.py` to consume canonical fields and label local fallback as incomplete/local. Completed in archived Desktop derivative.
- [x] 2.3 Add RED view tests in `tests/test_reportes_view.py` for labels, warnings, period state, and Desktop-only closed/export entry points. Completed in archived Desktop derivative; focused tests passed.
- [x] 2.4 Update `views/reportes.py` to render canonical labels, completeness warnings, capacity, and roadmap boundaries. Completed in archived Desktop derivative.

## Phase 3: Mobile Limited Scope

- [x] 3.1 Add RED Mobile tests in `../estacionamiento_central_mobile/test/features/admin/reportes/reportes_mensualidades_test.dart` for dashboard-only rendering and no closed/export UI. Completed in archived Mobile derivative; focused Flutter tests passed.
- [x] 3.2 Update `../estacionamiento_central_mobile/lib/features/admin/reportes/data/reportes_api.dart` to consume only 1.3.0 dashboard fields. Completed in archived Mobile derivative.
- [x] 3.3 Update `../estacionamiento_central_mobile/lib/features/admin/reportes/presentation/reportes_admin_screen.dart` to mark closed reports/exports deferred to 1.3.x. Completed in archived Mobile derivative.

## Phase 4: Packaging and Verification

- [x] 4.1 Inspect `../estacionamiento-central-installer` (read-only) only if XLSX/PDF dependencies or assets change; request edit authority before packaging edits. No installer inspection/edit was required because the completed slices introduced no XLSX/PDF dependency or asset packaging changes.
- [x] 4.2 Run API, Desktop, and Mobile focused tests plus full repo runners before marking tasks complete. Final cross-repo verification passed: API focused 28 tests and full 487 tests; Desktop focused 20 tests and full 380 tests; Mobile focused +4, full +67 using repo-local `TEMP/TMP`, and `flutter analyze` no issues.
