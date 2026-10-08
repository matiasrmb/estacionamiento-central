## Exploration: Desktop report audit visibility

### Current State
Desktop reporting already consumes the canonical reporting dashboard through `GET /reporting/metric-catalog` and `GET /reporting/dashboard`. The controller normalizes dashboard metadata including `source_state`, `period_state`, `completeness`, `capacity`, `warnings`, and `audit_coverage`, but the view only renders source/completeness/capacity/warnings. Audit coverage data is preserved in the normalized payload and then dropped at the UI boundary.

Closed-report operation drill-down and PDF/XLSX exports are already merged. The closed-report UI displays period/source/completeness/capacity/warnings and operation rows, but it does not expose a dedicated audit inventory panel. The canonical `admin-reporting-access` spec requires audit inventory from existing sources, and the roadmap evidence says the API audit inventory/readiness work already landed in repo-scoped API derivatives. No new Desktop endpoint wrapper is currently needed for the smallest visible slice because dashboard payloads already carry `audit_coverage`.

### Affected Areas
- `controllers/reportes_controller.py` — already preserves `dashboard.get("audit_coverage")`; proposal should only normalize shape if existing payload variants need stable UI fields.
- `views/reportes.py` — needs a compact audit coverage/status rendering area in the existing Intelligence Center/dashboard section.
- `tests/test_reportes_controller.py` — should prove audit coverage/status data from dashboard payloads is preserved and local fallback remains empty/non-official.
- `tests/test_reportes_view.py` — should prove Desktop renders available/gap coverage, hides or labels empty coverage, and does not fabricate audit data from local reports.
- `utils/api_client.py` — likely unchanged because dashboard fetching already exists and no audit-specific endpoint is required for this slice.
- `openspec/specs/admin-reporting-access/spec.md` — source requirement for existing-source inventory and visible audit limitations.
- `openspec/specs/operational-dashboard/spec.md` — source requirement for Desktop as the full Intelligence Center consumer.

### Approaches
1. **Desktop-only consumption of existing audit coverage/status data** — Render `audit_coverage` already present in normalized dashboard payloads as a compact audit visibility panel.
   - Pros: Smallest repo-scoped slice; uses existing Desktop/API dashboard contract; no API, Mobile, Installer, schema, or new endpoint work; directly exposes audit limitations already required by specs.
   - Cons: Limited to whatever audit inventory/status the API already returns in dashboard payloads; does not create a richer audit inventory endpoint or closed-report audit workbench.
   - Effort: Low

2. **API-first audit inventory contract** — Switch to the API repository and define/expand a dedicated audit inventory response before Desktop UI work.
   - Pros: Best if the current dashboard payload is insufficient or lacks source-level coverage details in the API implementation.
   - Cons: Not justified from Desktop evidence alone because Desktop already preserves `audit_coverage`; would delay visible Desktop value and requires a new repo/change name.
   - Effort: Medium

3. **Normalize existing audit coverage fields before UI** — Add controller-only normalization/tests for `audit_coverage` and defer rendering.
   - Pros: Very safe prerequisite if payload shape is inconsistent.
   - Cons: Too narrow as an independent roadmap slice because users still gain no audit visibility; better as the first task inside the Desktop UI slice.
   - Effort: Low

### Recommendation
Proceed with `desktop-report-audit-visibility` as a Desktop-only change. The smallest coherent next slice is to render existing audit coverage/status data already available through current reporting/dashboard payloads, with controller normalization only as needed for stable view rendering.

Do not create Desktop implementation work that depends on new API endpoints. If proposal/spec work discovers that the API does not actually provide usable `audit_coverage` details beyond an empty or unstable field, stop and switch to an API repo change named `api-report-audit-inventory` instead of expanding Desktop scope.

### Risks
- The current Desktop evidence proves the normalized payload preserves `audit_coverage`, but not that the live API always returns enough detail for a meaningful panel.
- `views/reportes.py` is already large; keep the UI addition compact and test-driven to stay below the review budget.
- Local fallback must not fabricate audit coverage; it should remain explicitly local/non-official with empty or unavailable audit status.
- Avoid reopening the blocked cross-repo roadmap change; use it only as evidence.

### Ready for Proposal
Yes — propose `desktop-report-audit-visibility` as a Desktop-only audit visibility slice. The orchestrator should state that API-first work is not required unless proposal/spec validation proves current dashboard `audit_coverage` is unusable.
