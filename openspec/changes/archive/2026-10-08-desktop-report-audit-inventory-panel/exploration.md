## Exploration: Desktop report audit inventory panel

### Current State
The broad roadmap `centro-inteligencia-reportes-auditoria-13-roadmap` is still evidence-only for runtime work because it spans Desktop, API, Mobile, and Installer repositories. Its latest task status says the repo-scoped API derivatives already landed canonical reporting semantics, PDF/XLSX exports, existing-source audit inventory, historical plate lookup, anomaly/statistics endpoints, and audit-inventory remediation. It also says Mobile remains dashboard-only for 1.3.0 and Installer/release hardening is deferred until a concrete release scope.

Desktop has now completed the three recent reporting slices: closed-report operation drill-down, closed-report PDF/XLSX exports, and dashboard audit coverage visibility. The canonical Desktop code consumes the metric catalog, dashboard, closed reports, closed-report operations, and exports through `utils/api_client.py` and `controllers/reportes_controller.py`, while `views/reportes.py` renders dashboard metadata, compact audit coverage, closed-report metadata, operations, pagination, and export status. There is still no Desktop audit-inventory endpoint wrapper or dedicated audit inventory/review panel.

Canonical specs now leave the next meaningful reporting/audit gap in `admin-reporting-access`: the system should support administrative review of existing-source audit coverage for closures, payments, expenses, users/sessions, prints, and deterministic anomalies without adding event sourcing, formal accounting, auditor roles, or machine-learning anomaly scoring. The compact dashboard audit label satisfies visibility of supplied limitations, but it is not a detailed audit inventory review surface.

### Affected Areas
- `utils/api_client.py` — would need a small wrapper for the existing API-owned audit inventory endpoint only if the API contract is already stable.
- `controllers/reportes_controller.py` — would need audit-inventory normalization, explicit API error handling, and no local fallback fabrication.
- `views/reportes.py` — would need a compact audit inventory panel inside the existing Intelligence Center/closed-report area without replacing dashboard, closed-report, operations, or export flows.
- `tests/test_api_client_session.py` — should cover endpoint construction and avoid invented query parameters.
- `tests/test_reportes_controller.py` — should cover source coverage normalization, unavailable/gap states, deterministic anomaly metadata, and API errors.
- `tests/test_reportes_view.py` — should cover rendering the audit inventory panel, empty/unavailable states, and preserving existing closed-report/export/operations behavior.
- `openspec/specs/admin-reporting-access/spec.md` — source requirement for existing-source audit inventory and serious audit review boundaries.
- `openspec/specs/operational-dashboard/spec.md` — confirms Desktop is the full Intelligence Center consumer while Mobile remains limited.

### Approaches
1. **Desktop audit inventory panel** — Add Desktop-only consumption and rendering of the existing API audit inventory contract as a compact administrative review panel.
   - Pros: Smallest remaining Desktop roadmap value; uses API-owned data instead of local inference; advances the serious audit requirement beyond a summary label; no API, Mobile, Installer, database, or packaging work if the endpoint contract is stable.
   - Cons: Depends on the already-landed API contract being usable from Desktop evidence; `views/reportes.py` is large, so the UI must stay deliberately compact.
   - Effort: Medium

2. **API-first audit inventory contract hardening** — Switch to the API repository and plan a repo-scoped API change if the audit inventory endpoint lacks stable fields for Desktop.
   - Pros: Correct boundary if the API payload is incomplete, unstable, or missing deterministic anomaly/source coverage needed by Desktop.
   - Cons: Not justified as the first recommendation from current Desktop evidence because the roadmap says API audit inventory and anomaly remediation already landed.
   - Effort: Medium

3. **Cleanup/status-only reporting roadmap reconciliation** — Create a Desktop repo cleanup change that updates roadmap/status artifacts and records that Desktop is effectively complete for 1.3.0 reporting.
   - Pros: Lowest risk; useful if product decides the compact dashboard audit label is enough for 1.3.0.
   - Cons: Leaves the `admin-reporting-access` serious audit review requirement with no Desktop-facing detailed inventory surface; little product value.
   - Effort: Low

4. **Mobile or Installer follow-up** — Plan Mobile closed reports/exports or Installer release hardening in their own repositories.
   - Pros: Correct repo boundary if the product wants release packaging or future Mobile expansion next.
   - Cons: Mobile closed reports/exports are explicitly deferred to later 1.3.x, and Installer work is deferred until concrete release scope; neither is the smallest reporting/audit roadmap slice in this Desktop repo.
   - Effort: Medium/High

### Recommendation
Recommend a new Desktop-scoped change named `desktop-report-audit-inventory-panel`.

The slice should add a compact Desktop audit inventory panel that consumes the existing API-owned audit inventory/readiness data, displays available sources, gaps/unavailable sources, deterministic anomaly status, and source limitations, and keeps all local calendar reporting, closed-report operations, exports, dashboard summary, API implementation, Mobile, Installer, database, schema, event-sourcing, auditor-role, and formal-accounting behavior out of scope.

This is preferable to another dashboard-only UX follow-up because dashboard audit visibility is already archived. It is preferable to API-first work only if proposal validation confirms the API audit inventory contract is stable enough; if that validation fails, stop and switch to an API repo change such as `api-report-audit-inventory-contract-hardening` instead of expanding Desktop scope. Mobile and Installer follow-ups should not be planned in this Desktop repo now.

### Risks
- The Desktop repo evidence says API audit inventory landed, but this exploration did not inspect the API repository implementation; proposal/design must validate the exact payload shape before committing Desktop apply work.
- The existing `views/reportes.py` file is already large; adding a panel can exceed the review budget unless tasks keep the UI compact and test-driven.
- The panel must not fabricate audit coverage from local calendar reports or treat compact dashboard audit text as full audit review.
- If product decides compact dashboard audit coverage is sufficient for 1.3.0, the better next change becomes a cleanup/status reconciliation slice rather than implementation.

### Ready for Proposal
Yes — proceed to proposal for `desktop-report-audit-inventory-panel` only after confirming the existing API audit inventory response contract is stable enough for Desktop consumption. The orchestrator should tell the user this is a Desktop-only display/UX follow-up, with an explicit API-first escape hatch if contract validation fails.
