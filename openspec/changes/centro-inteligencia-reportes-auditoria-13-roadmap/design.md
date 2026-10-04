# Design: Centro Inteligencia Reportes Auditoria 1.3 Roadmap

## Technical Approach

Make the API reporting read model the canonical boundary, then keep Desktop as the full Intelligence Center consumer and Mobile as a limited daily operational dashboard for 1.3.0. Existing closure rows (`cierres_diarios`) remain the reproducible snapshot source; operational rows provide drill-down and discrepancy checks. Calendar date filters stay secondary to closure-to-closure periods.

## Architecture Decisions

| Decision | Alternatives considered | Rationale |
|---|---|---|
| API owns metric semantics and completeness labels. | Duplicate calculations in Desktop/Mobile. | `controllers/reportes_controller.py` and Mobile already normalize `/reporting/metric-catalog` + `/reporting/dashboard`; one API contract prevents semantic drift. |
| Closure snapshots are primary for closed reports; operational rows are drill-down evidence. | Recompute every closed report from mutable operational tables only. | `reporting_repo.get_closed_report()` already compares `closure_reference` with `operation_totals`; snapshots support reproducible reports while discrepancies remain visible. |
| Replace required CSV roadmap with XLSX while keeping PDF. | Keep CSV as required export. | Specs require PDF/XLSX; current `build_report_export()` supports CSV/PDF, so tasks must add XLSX and stop treating CSV as required. |
| Defer transversal audit event log. | Add event sourcing or before/after audit tables now. | Specs require 1.3.0 inventory/readiness only; `build_audit_inventory()` can expose available/unavailable source coverage without schema-heavy audit logging. |

## Data Flow

    cierres_repo.realizar_cierre() -> cierres_diarios snapshot + row links
              │
              ├-> reporting_repo.get_open_dashboard() -> /reporting/dashboard
              └-> reporting_repo.get_closed_report(id)
                       -> reporting_read_models export/audit metadata
    Desktop ReportesWindow -> utils.api_client -> API reporting read models
    Mobile ReportesAdminScreen -> ReportesApi.dashboard() only

## File Changes

| File | Action | Description |
|---|---|---|
| `estacionamiento-central-api/app/repositories/reporting_read_models.py` | Modify | Update metric meanings, add completeness/capacity fields, add XLSX export builder, remove CSV as required roadmap format, expand audit inventory coverage. |
| `estacionamiento-central-api/app/repositories/reporting_repo.py` | Modify | Align open/closed dashboard income with journey-collected mensualidades, expose closure-to-closure bounds and historical source state. |
| `estacionamiento-central-api/app/api/v1/endpoints/reporting.py` | Modify | Preserve admin-only endpoints; validate `pdf`/`xlsx` exports and dashboard period filters. |
| `estacionamiento-central/controllers/reportes_controller.py` | Modify | Normalize new catalog/completeness/capacity fields and keep local fallback clearly labelled incomplete/local. |
| `estacionamiento-central/views/reportes.py` | Modify | Show canonical labels, operational period state, completeness warnings, and Desktop-only closed/export roadmap entry points when implemented. |
| `estacionamiento_central_mobile/lib/features/admin/reportes/data/reportes_api.dart` | Modify | Consume only dashboard fields required for 1.3.0 and ignore/defer closed report/export capabilities. |
| `estacionamiento_central_mobile/lib/features/admin/reportes/presentation/reportes_admin_screen.dart` | Modify | Keep Mobile UI to operational daily summary and explicit no-export/no-closed-report scope. |
| `estacionamiento-central-installer` | No change unless dependencies/assets change | Only update packaging if XLSX/PDF generation introduces bundled assets or migrations. |

## Interfaces / Contracts

`/api/v1/reporting/dashboard` and closed reports should expose: `period {id,start,end,state,business_date?}`, `catalog_version`, `metrics`, `capacity {total_spaces:50, active_monthly_customers, effective_transient_capacity}`, `completeness {status: complete|partial|unavailable, reasons}`, and `filters`. Exports accept `pdf` and `xlsx` and include report id, bounds, closure id, generated timestamp, catalog version, filters, source state, and template version.

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| API unit | net includes journey mensualidades, closure periods cross midnight, capacity subtraction, completeness labels, PDF/XLSX metadata, CSV not required | Extend `tests/test_reporting_read_models.py`, `test_reporting_exports.py`, `test_reporting_endpoints.py`, `test_reporting_closed_reports.py`. |
| Desktop unit | API normalization, local fallback labels, UI cards/warnings | Extend `tests/test_reportes_controller.py` and `tests/test_reportes_view.py`. |
| Mobile widget/unit | dashboard-only scope and ignored closed/export features | Extend `test/features/admin/reportes/reportes_mensualidades_test.dart`. |

## Threat Matrix

N/A — this design does not introduce routing, shell commands, subprocesses, VCS/PR automation, executable-file classification, or process-integration boundaries. Existing HTTP endpoints are extended within the current FastAPI router pattern and admin role guard.

## Migration / Rollout

No immediate migration for the design artifact. Implementation should avoid runtime DDL; add migrations only if XLSX dependencies or persisted metadata require schema/packaging changes. Roll out by API contract/tests first, then Desktop UI, then Mobile limited rendering.

## Open Questions

- [ ] Which existing table/flag is the authoritative source for active monthly customers when calculating effective transient capacity?
- [ ] Should legacy CSV remain accepted as non-roadmap compatibility, or be rejected once XLSX is added?
