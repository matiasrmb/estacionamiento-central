## Exploration: Desktop Financial/Operational Reports

### Current State
Desktop reporting already has three overlapping surfaces: a local date-range report table, an API-backed dashboard summary, and an API-backed closed-report section. The dashboard slice consumes `GET /reporting/metric-catalog` and `GET /reporting/dashboard` through `utils/api_client.py`, normalizes canonical metric labels and metadata in `controllers/reportes_controller.py`, and renders source/completeness/capacity warnings in `views/reportes.py`. The closed-report/export roadmap slice added client wrappers for `GET /reporting/reports/closed/{closure_id}` and `GET /reporting/exports/{closure_id}.{format}`, but the view still hides PDF/XLSX export buttons as deferred 1.3.x scope.

The API contract now also exposes operation drill-down rows through `GET /reporting/reports/operations?period_id=closure:{id}` with optional `category`, `operator`, `plate`, `sort`, `direction`, `limit`, and `offset`; pagination defaults to 100 rows and caps at 200. Desktop has no operation-row client wrapper yet. The current local `obtener_reportes()` path still queries MySQL directly by calendar dates and filters by plate, time, user, and movement type; it is useful for legacy/local consultation but is not the canonical journey/closure-based API read model.

### Affected Areas
- `utils/api_client.py` — would need a Desktop wrapper for the canonical operations endpoint if this slice includes operation rows.
- `controllers/reportes_controller.py` — would need operation-report normalization, pagination metadata handling, API error states, and a clear boundary from local `obtener_reportes()`.
- `views/reportes.py` — would need the closed-report detail area to expose drill-down rows and pagination controls without duplicating the dashboard cards or enabling deferred exports.
- `tests/test_api_client_session.py` — should cover endpoint construction for operations requests and reject undeclared query parameters by omission rather than client invention.
- `tests/test_reportes_controller.py` — should cover operation-row normalization, pagination metadata, category/operator/plate filters, sort options, and API errors without local fallback fabrication.
- `tests/test_reportes_view.py` — should cover rendering operation rows, pagination state, warning/error visibility, and preserving the existing dashboard/closed-report behavior.
- `openspec/specs/canonical-reporting-api/spec.md` — already defines canonical metrics, closure/journey semantics, and API-owned read models.
- `openspec/specs/reproducible-closed-reports/spec.md` — already defines closed-report reproduction, discrepancy visibility, drill-down, and the export deferral boundary.
- `openspec/specs/operational-dashboard/spec.md` — already defines dashboard consumption and explicitly kept operations pagination UI out of the previous validation slice.

### Approaches
1. **Closed-report operation drill-down only** — Treat financial/operational reports as the next Desktop detail layer after a closed report is loaded: fetch operation rows for that closed report's closure period, render canonical category/amount/operator/plate rows, and page through API results.
   - Pros: Uses the newly merged operations pagination contract, advances financial/operational reporting beyond dashboard summaries, and stays aligned with the reproducible closed-report requirement that drill-down explains totals.
   - Cons: Closed reports only; open/current-period API operation rows remain out of scope because the API endpoint currently accepts only `closure:{id}` periods.
   - Effort: Medium

2. **Broader report center replacement** — Replace the existing local calendar-date report table with API-backed report data for dashboard, closed reports, operation rows, and exports.
   - Pros: Moves Desktop closer to a single canonical reporting source.
   - Cons: Too broad for this slice, risks duplicating dashboard validation and closed-export work, and would require unresolved API support for open/current operation rows and calendar secondary filters.
   - Effort: High

3. **Dashboard-only hardening** — Keep this slice limited to additional dashboard metadata/metric rendering.
   - Pros: Low implementation risk and small review footprint.
   - Cons: Does not answer the roadmap need for financial/operational reports because dashboard validation has already been merged and archived.
   - Effort: Low

### Recommendation
Proceed with **Closed-report operation drill-down only**. In this slice, “financial/operational reports” should mean a Desktop admin can load a canonical closed report and inspect the API-owned operation rows that explain its totals, including pagination and filters supported by the API contract. The proposal should explicitly keep the dashboard summary, exports, audit inventory, historical plate UI, open/current operation rows, API changes, Mobile changes, Installer changes, and formal accounting ledgers out of scope.

The narrow proposal should add Desktop consumption of `GET /reporting/reports/operations` only after a closed report identifies a `closure:{id}` period or operation drill-down link. The UI should avoid building a new report module from scratch; it should extend the existing closed-report section with an operations table and pagination/status controls, preserving the existing local report table as legacy/local consultation for now.

### Risks
- The current Desktop closed-report loader asks for free text and sends it to `/reporting/reports/closed/{closure_id}`; the API endpoint expects an integer `closure_id`, so the next slice should avoid promising flexible report-id lookup unless the API contract changes.
- API operation rows are only supported for `closure:{id}` periods; open/current financial-operation drill-down should remain out of scope until the API owns that contract.
- Existing Desktop view code is already large; adding operations rows inside the same file may increase maintenance and review risk unless the task plan keeps changes small and test-driven.
- Local `obtener_reportes()` uses calendar-date MySQL queries, while canonical reporting uses closure/journey periods; mixing those semantics in one UI can confuse users unless labels are explicit.
- Exports are partially wired in controller/client but hidden by spec as deferred; this slice must not re-enable export buttons or turn operation drill-down into an export delivery slice.

### Ready for Proposal
Yes — propose a Desktop-only, API-consuming closed-report operations drill-down slice. The orchestrator should tell the user that the next safe step is not another dashboard or export slice, but a narrow operation-row drill-down for closed reports using the canonical API pagination contract.
