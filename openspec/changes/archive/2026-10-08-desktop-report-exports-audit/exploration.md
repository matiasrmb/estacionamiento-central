## Exploration: Desktop closed-report exports and audit next slice

### Current State
Desktop already has API-backed closed-report loading and operation drill-down. The API client and controller also already contain closed-report export plumbing for PDF/XLSX, including format validation, content decoding, file writing, and error preservation. The view still keeps the PDF/XLSX buttons hidden and shows a deferral label, so the smallest coherent next slice is enabling the existing backend-backed export handoff in the closed-report UI.

Audit visibility is less ready for a Desktop-only slice. The canonical specs require a serious audit slice, and Desktop dashboard normalization preserves `audit_coverage`, but there is no Desktop report audit-inventory endpoint wrapper or UI surface yet. Starting audit now would either be a broader API/Desktop contract slice or a thin label-only surface with weak user value.

### Affected Areas
- `views/reportes.py` — export controls are present but hidden; this is the main place to enable PDF/XLSX actions only after a valid API-backed closed report is loaded and to preserve error/status messaging.
- `controllers/reportes_controller.py` — export handoff already exists; next work likely needs only targeted hardening around metadata/status returned to the view.
- `utils/api_client.py` — canonical `/reporting/exports/{closure_id}.{format}` wrapper already supports PDF/XLSX and rejects CSV, so no new API route should be invented.
- `tests/test_reportes_view.py` — current tests assert exports are deferred/hidden; they should become RED coverage for visible enabled/disabled states, successful PDF/XLSX handoff, and API error messages.
- `tests/test_reportes_controller.py` and `tests/test_api_client_session.py` — existing export coverage should remain focused regression coverage unless design finds a specific metadata gap.
- `openspec/specs/reproducible-closed-reports/spec.md` — already contains Desktop export behavior; the change can modify/replace the deferral boundary with UI enablement requirements if needed.
- `openspec/specs/admin-reporting-access/spec.md` — audit remains relevant but should not be the primary target of this slice unless proposal evidence proves an API inventory endpoint is already consumable by Desktop.

### Approaches
1. **Enable closed-report PDF/XLSX export UI** — make existing closed-report export buttons visible/enabled only after a valid closed report is loaded, route clicks through the current controller, and keep CSV absent.
   - Pros: Smallest coherent user value; Desktop-focused; uses existing API/client/controller plumbing; directly resolves the visible deferral in the current UI.
   - Cons: Does not advance audit inventory visibility; needs careful state handling so exports are unavailable before a valid closure reference.
   - Effort: Low

2. **Desktop audit/inventory visibility** — add a closed-report audit coverage panel or inventory view.
   - Pros: Advances the serious audit roadmap and exposes source limitations more clearly.
   - Cons: No current Desktop audit-inventory client wrapper or view surface; likely needs API contract confirmation and more UI design; higher risk of exceeding a Desktop-only slice.
   - Effort: Medium

3. **Prerequisite: export state hardening only** — keep buttons hidden but refactor/export-state tests around existing controller behavior.
   - Pros: Very small and low risk.
   - Cons: Produces little product value because export handoff already exists below the UI; would leave the user-facing roadmap boundary unchanged.
   - Effort: Low

### Recommendation
Use change name `desktop-report-exports-audit`, but scope the first proposal narrowly to Desktop closed-report export enablement. The implementation should not add API endpoints, CSV promises, audit inventory UI, Mobile behavior, Installer behavior, or local fallback exports. If audit work is desired next, plan it as a follow-up slice after export enablement, likely starting with evidence that the API audit inventory contract is already stable enough for Desktop consumption.

The immediate proposal should define: PDF/XLSX buttons become visible and enabled only for a loaded API-backed closed report with a closure reference; clicking each button uses the existing `exportar_reporte_cerrado` path; success surfaces the saved file path; errors preserve API details; CSV remains absent; exports do not fabricate local/calendar report output.

### Risks
- Hidden export controls already exist, so the change may be deceptively small; tests must cover invalid/no-report states and stale report states after API errors.
- The controller writes returned content to a local `reportes` folder; proposal/design should decide whether that location is acceptable or needs a user-selected destination before apply.
- Existing UI copy mixes Spanish legacy labels with English canonical reporting labels; this slice should follow existing context rather than broaden copy cleanup.
- Audit scope pressure is real; including audit inventory in the same slice would likely grow beyond the smallest coherent Desktop export change.

### Ready for Proposal
Yes. Tell the user the recommended next change is `desktop-report-exports-audit`, scoped to Desktop closed-report PDF/XLSX export enablement only. Audit/inventory visibility should remain explicitly out of scope or be recorded as the next follow-up unless API evidence later proves it is already a tiny Desktop-only consumption task.
