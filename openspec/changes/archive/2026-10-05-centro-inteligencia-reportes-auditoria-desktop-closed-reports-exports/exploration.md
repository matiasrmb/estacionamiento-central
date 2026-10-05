# Exploration: Desktop API-backed closed reports and exports

### Current State
The umbrella roadmap remains a cross-repo planning artifact blocked for runtime execution by independent Desktop, API, and Mobile repositories. The API reporting base derivative has already archived canonical reporting semantics, closed-report identity, audit inventory, and PDF/XLSX export contracts; the API historical/anomalies/statistics derivative has also archived later API-only reporting contracts. Desktop has an archived Intelligence Center slice, but the current Desktop implementation still exposes closed-report and export actions only as non-operational roadmap boundaries. `utils/api_client.py` only provides reporting metric catalog and dashboard calls, so Desktop cannot yet retrieve API-backed closed reports or request canonical exports.

### Affected Areas
- `utils/api_client.py` — needs additive API client calls for closed reports and PDF/XLSX export endpoints.
- `controllers/reportes_controller.py` — needs controller normalization for closed-report metadata, reproducibility fields, completeness/source state, and export request handling.
- `views/reportes.py` — currently renders future-only closed/export buttons; should turn them into operational admin-facing flows once API-backed data is available.
- `tests/test_reportes_controller.py` — should cover closed-report/export normalization and API error handling.
- `tests/test_reportes_view.py` — should replace future-boundary assertions with operational UI behavior and warnings.
- `openspec/specs/reproducible-closed-reports/spec.md` — currently records Desktop closed/export entry points as roadmap boundaries only; the derivative should modify that boundary into implemented Desktop behavior.

### Approaches
1. **Operationalize Desktop closed reports and exports first** — Convert the existing Desktop roadmap buttons into API-backed closed-report retrieval and PDF/XLSX export flows.
   - Pros: Directly closes an explicit umbrella roadmap gap; reuses already archived API contracts; keeps work in the Desktop repo; avoids new API or Mobile scope.
   - Cons: Does not yet expose the newer historical plate/anomaly/statistics APIs in Desktop.
   - Effort: Medium

2. **Build Desktop historical/anomaly/statistics UI first** — Add Desktop surfaces for the API historical plate and source-backed anomaly/statistics contracts.
   - Pros: Follows the most recently archived API derivative; advances Desktop as the Intelligence Center for historical analysis.
   - Cons: Leaves existing visible closed/export buttons as non-operational placeholders; anomaly/statistics presentation likely needs additional product decisions.
   - Effort: Medium/High

3. **Bundle closed/export and historical/anomaly/statistics UI together** — Implement all remaining Desktop Intelligence Center consumers in one derivative.
   - Pros: Reduces repeated Desktop navigation work and produces a fuller Intelligence Center.
   - Cons: High review-budget risk under the 400 changed-line policy; mixes reproducible export workflows with investigative history/statistics UX.
   - Effort: High

### Recommendation
Proceed with Approach 1 as the next repo-scoped derivative: `centro-inteligencia-reportes-auditoria-desktop-closed-reports-exports` targeting `estacionamiento-central`. This is the safest next derivative because Desktop already exposes the exact closed/export roadmap placeholders, the umbrella roadmap explicitly requires Desktop/API closed reports and PDF/XLSX exports, and archived API work has made those contracts available. Keep Desktop historical plate/anomaly/statistics consumption as a follow-up derivative after this one.

### Risks
- API endpoint names and payload details must be confirmed during proposal/spec against the archived API contracts before design or implementation.
- PDF/XLSX export behavior may require deciding whether Desktop downloads binary content, opens a generated file, or delegates to an API-provided file response.
- UI changes can exceed the 400-line review budget if closed report selection, export handling, and error states are not kept narrow.
- The current Desktop UI still says `PDF/CSV`, while the roadmap requires PDF/XLSX; the derivative must correct that user-facing mismatch.

### Ready for Proposal
Yes. The next phase should be `sdd-propose` for `centro-inteligencia-reportes-auditoria-desktop-closed-reports-exports` in `estacionamiento-central`, scoped to Desktop operational closed reports and PDF/XLSX exports only.
