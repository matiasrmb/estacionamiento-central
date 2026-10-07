## Exploration: Desktop Reporting Dashboard API Validation

### Current State
Desktop already contains the archived Intelligence Center dashboard slice. The archive passed 3/3 requirements and 10/10 scenarios, and explicitly deferred live API validation until the canonical reporting API was available. Current Desktop code calls the canonical reporting metric catalog and dashboard endpoints through `utils/api_client.py`, normalizes API dashboard metadata in `controllers/reportes_controller.py`, renders canonical labels/source/completeness/capacity in `views/reportes.py`, and keeps local report table queries separate from API-backed dashboard summaries.

Focused tests still pass for the reporting controller, reporting view, and API client session contract: `python -m unittest tests.test_reportes_controller tests.test_reportes_view tests.test_api_client_session` ran 42 tests OK. The current Desktop tests are payload-driven and already avoid requiring a live API server, so the remaining gap is live contract validation against the merged API PR #86/#90 behavior rather than reimplementing the archived dashboard.

### Affected Areas
- `utils/api_client.py` — defines Desktop API reporting endpoint paths for metric catalog, dashboard, closed reports, and exports.
- `controllers/reportes_controller.py` — normalizes dashboard API fields, preserving `filters` and `pagination` metadata from the API payload, and falls back to local incomplete/non-official summaries.
- `views/reportes.py` — renders dashboard source, period, completeness, warnings, capacity, and canonical metric labels; local table filtering/sorting remains Desktop-local.
- `tests/test_api_client_session.py` — verifies canonical endpoint construction for reporting API calls.
- `tests/test_reportes_controller.py` — verifies dashboard normalization and local fallback semantics with mocked payloads.
- `tests/test_reportes_view.py` — verifies Desktop rendering of canonical dashboard and fallback metadata.
- `openspec/specs/canonical-reporting-api/spec.md` — source of truth for canonical reporting read models, 400-vehicle completeness, and Desktop normalization.
- `openspec/specs/operational-dashboard/spec.md` — source of truth for Desktop full-center dashboard consumption and filter consistency.
- `openspec/changes/archive/2026-10-02-centro-inteligencia-reportes-auditoria-desktop-intelligence-center/` — archived Desktop dashboard implementation and verification evidence.

### Approaches
1. **Validation-only Desktop follow-up** — create proposal/spec/tasks for live API validation and mocked contract alignment only, with no production code changes unless validation finds drift.
   - Pros: avoids duplicating the archived dashboard, directly addresses the deferred live API validation gap, keeps review size very small.
   - Cons: depends on access to a running API fixture or agreed live-validation procedure in later phases.
   - Effort: Low

2. **Minor adapter update slice** — add or adjust Desktop adapter parameters only if PR #86/#90 changed dashboard query parameters, response keys, or pagination/filter metadata consumed by Desktop.
   - Pros: provides a safe path if live validation reveals a concrete API/Desktop mismatch.
   - Cons: premature without evidence; risks changing stable Desktop behavior for a contract that may already match.
   - Effort: Low to Medium

3. **No-code closure** — document that current Desktop contracts are already aligned and close after focused tests plus API contract readback.
   - Pros: smallest possible change and preserves the archived implementation untouched.
   - Cons: insufficient if the product wants explicit proof against merged live API endpoints after PR #86/#90.
   - Effort: Low

### Recommendation
Proceed with a validation-only follow-up change. The exploration did not find evidence that Desktop should duplicate or rebuild the archived dashboard. The likely next slice should prove the current adapter against the merged API reporting contracts, add/adjust mocked contract tests only if concrete schema drift is found, and keep production code unchanged unless live validation exposes an endpoint, query, or payload mismatch.

### Risks
- Live API validation may require a seeded API environment; without it, later verification can only prove mocked contract alignment.
- API PR #90 pagination/filter metadata may be relevant to API operations endpoints but not to the current Desktop dashboard path unless the dashboard response contract also changed.
- Desktop currently preserves `filters` and `pagination` in normalized payloads but does not render them, so any new user-visible pagination requirement would be a new product scope, not a validation-only fix.

### Ready for Proposal
Yes — tell the user this should become a narrow validation/test-alignment proposal, not a repeat implementation of the already archived Desktop dashboard. The proposal should explicitly allow “no production code change” as the preferred outcome and only permit adapter updates when proven by live API contract drift.
