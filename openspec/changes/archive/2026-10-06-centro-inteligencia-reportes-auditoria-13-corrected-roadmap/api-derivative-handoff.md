# API Derivative Handoff: Corrected Reporting Intelligence and Audit Roadmap

## Scope Boundary

This artifact is a Desktop-repo planning handoff for the API repo derivative. It does not modify API, Desktop, Mobile, Installer, application code, tests, branches, commits, pushes, or pull requests.

The API implementation must happen in a separate `estacionamiento-central-api` derivative. The sibling API paths below are read-only evidence references captured from `D:\Desarrollo\EstacionamientoCentral\estacionamiento-central-api`.

## Read-Only Evidence References

| Evidence path | Evidence used | Required API derivative outcome |
|---|---|---|
| `../estacionamiento-central-api/app/repositories/reporting_read_models.py` | Lines 5-67 define `METRIC_CATALOG_VERSION`, hard-coded `TOTAL_PARKING_SPACES = 50`, legacy metric names (`operational_income_total`, `operational_net_total`, `mensualidad_sales_total`), canonical PDF/XLSX plus legacy CSV export formats, and unsupported accounting fields. Lines 102-148 summarize old metric names. Lines 151-168 build capacity from immutable 50. Lines 211-258 build closed report discrepancy/anomaly metadata from old metric names. Lines 261-287 expose audit inventory coverage without event sourcing. Lines 290-321 keep CSV as `legacy-only` export compatibility. | Rename catalog and payload semantics to `collected_sources_total`, `operational_expense_total`, `net_revenue_total`, `monthly_payments_collected_total`, and `vehicle_movement_count`; preserve unsupported accounting exclusions; make capacity configurable with default/current 50 and historical `historical-capacity-limited`; keep deterministic anomaly/discrepancy behavior; make CSV non-canonical and ensure export delivery remains deferred/non-blocking for 1.3.0. |
| `../estacionamiento-central-api/app/repositories/reporting_repo.py` | Lines 122-148 build the current open journey from the latest closure and pending closure data. Lines 151-230 read closed reports from `cierres_diarios`, include `fecha_inicio`/`fecha_cierre`, charged solo lavado, night charges, monthly payments, hard-coded capacity 50, and closure-vs-operation discrepancy. Lines 233-250 inventory closures, payments, expenses, print jobs, users, operator sessions, parking, solo wash, monthly payment, night charge, closure, and logical deletion sources. Lines 253-278 build plate history. Lines 281-299 emit old metric names. Lines 305-316 count active monthly customers. | Preserve closure/journey truth and current journey behavior; ensure bad closure/period identifiers fail safely; count monthly payments by `fecha_pago`/collection journey rather than covered month; include charged solo lavado and future source-compatible collected totals; replace immutable 50 with configurable current capacity defaulting to 50; keep audit inventory coverage and limitations explicit. |
| `../estacionamiento-central-api/app/api/v1/endpoints/reporting.py` | Lines 22-48 keep `/reporting/metric-catalog`, `/reporting/dashboard`, `/reporting/reports/closed/{closure_id}`, and `/reporting/audit-inventory` behind `require_role("admin")`; lines 27-35 reject unsupported dashboard filters with 422; lines 38-43 map missing closures to 404; lines 51-80 validate plate-history inputs with 422; lines 98-109 expose export endpoint validation through `build_report_export`. | Preserve admin-only route contracts; add/keep focused API derivative tests for non-admin rejection, unsupported filters returning 422, malformed or missing period/closure identifiers failing safely, route payload contract alignment, and export deferral/non-canonical CSV behavior. |

## API Derivative Requirements

### Admin and Route Guard Contracts

- Keep all reporting routes admin-only.
- Verify unsupported dashboard/report filters return 422 instead of being silently ignored.
- Verify bad closure IDs, bad period IDs, malformed history bounds, and invalid limits fail safely with the existing route error conventions.
- Keep route shape compatible for Desktop and Mobile consumers while migrating payload names through a documented compatibility mapping when needed.

### Metric and Revenue Contracts

- Replace canonical catalog names from `operational_income_total`, `operational_net_total`, and `mensualidad_sales_total` to the corrected names required by the spec.
- Define `net_revenue_total` as all collected sources minus operational expenses.
- Include parking records, bathroom usage, converted washes, charged solo lavado, monthly payments, night charges, and future service categories as collected sources.
- Count monthly payments in the journey where they are collected; the covered month must not define the financial period.
- Preserve unsupported formal accounting exclusions: taxes, commissions, payment-method accounting, and ledger balances.

### Period, Closure, and Journey Contracts

- Treat daily closure/journey boundaries as official reporting truth.
- Keep calendar dates secondary and label them as secondary grouping/filtering, never as official financial periods.
- Preserve current open journey behavior from the latest trusted closure when no next closure exists.
- Reproduce closed reports from closure references and expose later operational discrepancies as anomaly metadata instead of rewriting closure truth.

### Capacity Contracts

- Replace immutable `TOTAL_PARKING_SPACES = 50` usage with a configurable current capacity source.
- Keep 50 as the default/current configured value until product configuration changes.
- Label historical periods without reliable capacity configuration as `historical-capacity-limited` and avoid authoritative utilization percentages for those periods.

### Audit and Anomaly Contracts

- Keep the audit inventory based on existing sources: closures, payments, expenses, users/sessions, print jobs, parking, solo wash, monthly payment, night charge, closure references, and logical deletions.
- Keep the 1.3.0 audit slice deterministic and existing-source based; do not require event sourcing, machine learning, formal accounting, taxes, commissions, payment-method accounting, or auditor-role workflows.
- Surface coverage gaps and unsupported behaviors as audit limitations.

### Export Boundary

- Do not make PDF/XLSX delivery a 1.3.0 readiness blocker.
- If export routes remain present in the API derivative, mark them explicitly non-blocking/deferred for 1.3.0 readiness.
- CSV must not be advertised as the canonical spreadsheet target; if retained for compatibility, it must remain legacy-only and non-canonical.

## Required API Derivative Verification

| Area | Minimum API derivative tests |
|---|---|
| Admin guard | Non-admin users cannot access reporting routes; admin users can access allowed routes. |
| Unsupported filters | Unsupported dashboard/report filters return 422. |
| Bad identifiers | Missing closure IDs return the existing safe error; malformed/bad period IDs fail safely. |
| Metric catalog | Corrected metric names and unsupported accounting exclusions are returned. |
| Net revenue | Collected sources minus expenses drives `net_revenue_total`. |
| Monthly timing | Monthly payments count by `fecha_pago`/collection journey. |
| Solo lavado | Charged solo lavado contributes to collected sources; uncharged active washes do not. |
| Capacity | Current configured/default 50 is reported; historical missing capacity is labeled `historical-capacity-limited`. |
| Anomalies | Closure/reference mismatch emits deterministic discrepancy metadata; matching totals emit no discrepancy. |
| Audit inventory | Existing-source coverage includes closures, payments, expenses, users/sessions, print jobs, and source limitations without event sourcing. |
| Export deferral | 1.3.0 readiness does not depend on PDF/XLSX exports; CSV is not canonical. |

## Work Unit Evidence

| Evidence | Required value |
|---|---|
| Focused test command and exact result | Structural readback only for this Desktop planning artifact. Command captured in `apply-progress.md`; no runtime code was touched. |
| Runtime harness command/scenario and exact result | N/A: this work unit is a planning-only API derivative handoff in the Desktop repo. API runtime verification belongs to the later `estacionamiento-central-api` derivative. |
| Rollback boundary | Remove this file and revert only Phase 2 task checkboxes plus the Phase 2 section in `apply-progress.md`. |

## Handoff Status

Phase 2 is complete when this artifact exists, the three read-only API evidence paths are referenced, tasks 2.1 through 2.4 are checked, and `apply-progress.md` records the structural verification results.
