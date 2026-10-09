# Proposal: Desktop Report Audit Inventory Panel

## Intent

Add a compact Desktop audit inventory/readiness panel for admins. It will consume `GET /api/v1/reporting/audit-inventory` and show existing-source coverage, gaps, and limitations without fabricating local audit data.

## Scope

### In Scope
- Desktop API client wrapper for `GET /reporting/audit-inventory` with optional `period_id`.
- Controller normalization/error handling for API-supplied coverage/readiness/limitations.
- Compact panel in the existing reporting/Intelligence Center area.
- Mocked Desktop tests for endpoint construction, normalization, rendering, unavailable states, and preserved existing flows.

### Out of Scope
- API, Mobile, Installer, database migrations, event sourcing, persisted anomaly records, formal accounting, or auditor roles.
- Source totals/counts, freshness timestamps, or locally inferred audit coverage.
- API-first hardening unless later phases prove the validated contract is insufficient.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `admin-reporting-access`: Desktop audit surfaces will include a detailed existing-source inventory/readiness panel backed only by API-supplied audit inventory data.

## Approach

Use the existing admin-only API endpoint with `period_id` omitted for current or set to `current`, `closure:<positive_int>`, `open:initial`, or `open:<positive_int>`. Normalize only current contract fields: `period_id`, `coverage[]`, per-source `state`, `available_sources`, `partial_sources`, `unavailable_sources`, `affected_scopes`, `unavailable_history`, `requires_event_sourcing`, `supports_persisted_anomalies`, and `unsupported_behaviors`. Render coverage/readiness and limitations compactly; show errors or missing data as unavailable, never as fallback coverage.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `utils/api_client.py` | Modified | Add endpoint wrapper and optional query handling. |
| `controllers/reportes_controller.py` | Modified | Normalize payload and expose unavailable/error states. |
| `views/reportes.py` | Modified | Add compact panel without replacing existing flows. |
| `tests/test_api_client_session.py` | Modified | Cover endpoint path and allowed optional query behavior. |
| `tests/test_reportes_controller.py` | Modified | Cover normalization, gaps, limitations, and errors. |
| `tests/test_reportes_view.py` | Modified | Cover panel rendering and flow preservation. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Large view file increases review burden | Medium | Keep UI compact and split implementation tasks under the 400-line review budget. |
| Payload assumptions drift from API | Medium | Limit Desktop to the validated current contract and mocked contract tests. |

## Rollback Plan

Remove the wrapper, normalization, panel rendering, and related tests. Existing dashboard, closed-report, operations, and export paths remain unchanged.

## Dependencies

- Existing admin-only `GET /api/v1/reporting/audit-inventory` endpoint with the validated fields above.

## Success Criteria

- [ ] Desktop requests only `GET /reporting/audit-inventory` with no undeclared query beyond optional `period_id`.
- [ ] The panel displays available, partial, unavailable, affected scope, event-sourcing, persisted-anomaly, and unsupported-behavior limitations from API data.
- [ ] Missing/error payloads are rendered as unavailable without local fallback fabrication.
- [ ] Existing reporting dashboard, closed reports, operations, and exports remain covered by tests.
