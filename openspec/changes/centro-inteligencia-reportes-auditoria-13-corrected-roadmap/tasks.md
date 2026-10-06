# Tasks: Corrected Reporting Intelligence and Audit Roadmap

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 900-1400 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 Slice 0/API -> PR 2 Desktop -> PR 3 Mobile -> PR 4 Installer |
| Delivery strategy | auto-chain |
| Chain strategy | stacked-to-main |

Decision needed before apply: No - parent session selected auto-chain / stacked-to-main.
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Reconcile prior work and define derivative handoffs | PR 1 | OpenSpec status/readback | N/A: planning-only handoff | Corrected roadmap artifacts |
| 2 | API derivative handoff | PR 2 | OpenSpec status/readback | N/A: implemented in API repo derivative | API derivative artifact references |
| 3 | Desktop derivative handoff | PR 3 | OpenSpec status/readback | N/A: implemented in Desktop repo derivative | Desktop derivative artifact references |
| 4 | Mobile/Installer derivative handoffs | PR 4 | OpenSpec status/readback | N/A: implemented in repo-specific derivatives | Mobile/Installer derivative artifact references |

## Phase 1: Slice 0 Reconciliation Gate

- [x] 1.1 Produce keep/change/remove/defer matrix before apply; compare `openspec/changes/centro-inteligencia-reportes-auditoria-13-roadmap/` (read-only), merged work, and corrected specs.
- [x] 1.2 Classify API/admin keep, capacity/names/period truth change, exports defer, CSV remove, Desktop fallback change, Mobile dashboard keep/change.
- [x] 1.3 Block apply until unresolved rows name owner repo, outcome, derivative, verification, and rollback.

## Phase 2: API Derivative Handoff

- [x] 2.1 Create the API repo-scoped derivative handoff for admin guard, filter 422, bad period IDs, net revenue, monthly-payment timing, solo lavado, capacity, and anomalies.
- [x] 2.2 Reference `../estacionamiento-central-api/app/repositories/reporting_read_models.py` (read-only) as evidence for metric names, source/capacity/audit/anomaly contracts, and export deferral.
- [x] 2.3 Reference `../estacionamiento-central-api/app/repositories/reporting_repo.py` (read-only) as evidence for closure/journey truth, current journey, `fecha_pago`, capacity default 50, and audit inventory.
- [x] 2.4 Reference `../estacionamiento-central-api/app/api/v1/endpoints/reporting.py` (read-only) as evidence for route/admin contracts and required API derivative tests.

## Phase 3: Desktop Derivative

- [x] 3.1 RED: Add Desktop tests for canonical labels, full-center navigation, state/capacity visibility, and non-official fallback warnings.
- [x] 3.2 Update `controllers/reportes_controller.py` to normalize API contracts and mark fallback as `local_fallback`, incomplete, and non-official.
- [x] 3.3 Update `views/reportes.py` full-center UI labels and remove/hide 1.3.0 export promises when exports remain deferred.

## Phase 4: Mobile Derivative Handoff

- [x] 4.1 Create the Mobile repo-scoped derivative handoff for quick consultation, canonical labels, matched totals, and no full-center/export flows.
- [x] 4.2 Reference `../estacionamiento_central_mobile/lib/features/admin/reportes/**` (read-only) as evidence for canonical payload consumption and quick-consultation UI boundaries.
- [x] 4.3 Define Mobile verification expectations: `flutter test`, `flutter analyze`, and runtime harness availability in the Mobile derivative.

## Phase 5: Installer and Release Handoff

- [x] 5.1 Create the Installer/release handoff for API/Desktop payload manifest and version alignment.
- [x] 5.2 Reference `../estacionamiento-central-installer/**` (read-only) as evidence; installer edits must wait for an installer-scoped derivative or explicit release work.
- [x] 5.3 Define release verification expectations: API unittest, Desktop unittest, Mobile test/analyze, and Installer checklist after repo-scoped derivatives land.
