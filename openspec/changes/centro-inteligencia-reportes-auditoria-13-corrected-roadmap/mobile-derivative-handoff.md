# Mobile Derivative Handoff: Corrected Reporting Intelligence and Audit Roadmap

## Scope Boundary

This artifact is a Desktop-repo planning handoff for the Mobile repo derivative. It does not modify Mobile, API, Desktop application code, tests, branches, commits, pushes, or pull requests.

The Mobile implementation must happen in a separate `estacionamiento_central_mobile` derivative. The sibling Mobile paths below are read-only evidence references captured from `D:\Desarrollo\EstacionamientoCentral\estacionamiento_central_mobile`.

## Read-Only Evidence References

| Evidence path | Evidence used | Required Mobile derivative outcome |
|---|---|---|
| `../estacionamiento_central_mobile/lib/features/admin/reportes/data/reportes_api.dart` | `ReportesApi.dashboard()` already calls `/reporting/metric-catalog` and `/reporting/dashboard` for the current open journey. `ReportingDashboard.fromApi()` builds cards from API catalog names but still maps legacy labels such as `operational_income_total`, `operational_net_total`, and `mensualidad_sales_total`. | Keep API-backed dashboard consumption for quick consultation, migrate labels/metric names to `collected_sources_total`, `operational_expense_total`, `net_revenue_total`, `monthly_payments_collected_total`, and `vehicle_movement_count`, and ensure totals are read from the canonical dashboard payload without local recalculation. |
| `../estacionamiento_central_mobile/lib/features/admin/reportes/presentation/reportes_admin_screen.dart` | The screen is admin-gated, renders catalog version, open journey state, metric cards, and a notice that closed reports and exports are deferred to a later 1.3.x version. It does not expose closed-report navigation, export buttons, or Desktop full-center workflows. | Preserve the quick-consultation boundary: show current journey/card totals and limitation notices only; do not add full Intelligence Center navigation, closed-report workflows, PDF/XLSX/CSV export flows, or Desktop-equivalent audit/report management in the 1.3.0 Mobile derivative. |

## Mobile Derivative Requirements

### Quick Consultation Boundary

- Mobile remains a lightweight administrative consultation surface for the current reporting dashboard.
- Mobile MUST consume the same canonical API dashboard data as Desktop for matched totals, but it MUST NOT become the full Desktop reporting center.
- Mobile MUST NOT expose full-center navigation, closed-report management, export actions, CSV promises, or Desktop-only audit workflows in the 1.3.0 derivative.

### Canonical Labels and Matched Totals

- Replace legacy Mobile metric labels with the corrected canonical catalog names and user-facing labels from the API derivative.
- Required canonical metrics are `collected_sources_total`, `operational_expense_total`, `net_revenue_total`, `monthly_payments_collected_total`, and `vehicle_movement_count`.
- Values MUST come from the API dashboard payload. Mobile must not compute independent financial totals or reinterpret journey boundaries locally.
- Current journey state, catalog version, and any available source/completeness/capacity metadata should be displayed as quick-consultation context when the API payload provides them.

### Export and Full-Center Exclusions

- PDF/XLSX exports remain deferred to a later 1.3.x scope and must not block 1.3.0 Mobile reporting readiness.
- CSV must not be advertised as a canonical spreadsheet export target.
- Closed reports, reproducible export metadata, and full audit management belong to later or Desktop/API-scoped derivatives unless a future Mobile-specific SDD change explicitly expands scope.

## Required Mobile Derivative Verification

| Area | Minimum Mobile derivative verification |
|---|---|
| Canonical payload consumption | `flutter test` covers dashboard mapping from corrected metric names and proves card totals match API payload values. |
| Quick-consultation UI | `flutter test` covers admin reporting UI labels, current journey state, and absence of full-center/export flows. |
| Static analysis | `flutter analyze` passes in the Mobile repo after the derivative. |
| Runtime harness | Record whether a Mobile runtime harness is available. If unavailable, state `N/A` with the reason and rely on Flutter tests/analyze plus any available manual device/emulator smoke check. |

## Work Unit Evidence

| Evidence | Required value |
|---|---|
| Focused test command and exact result | Structural readback only for this Desktop planning artifact. Command captured in `apply-progress.md`; no runtime Mobile code was touched. |
| Runtime harness command/scenario and exact result | N/A: this work unit is a planning-only Mobile derivative handoff in the Desktop repo. Mobile runtime verification belongs to the later `estacionamiento_central_mobile` derivative. |
| Rollback boundary | Remove this file, revert only Phase 4 task checkboxes in `tasks.md`, and remove only the Phase 4 section in `apply-progress.md`. |

## Handoff Status

Phase 4 is complete when this artifact exists, both Mobile read-only evidence paths are referenced, Mobile verification expectations include `flutter test`, `flutter analyze`, and runtime harness availability, tasks 4.1 through 4.3 are checked, and `apply-progress.md` records structural verification results.
