# Proposal: Desktop Financial Operational Reports

## Intent

Let Desktop admins load a canonical closed report and inspect API-owned operation rows that explain its totals. This advances reporting beyond dashboard summaries while preserving the existing local calendar report table as legacy/local consultation.

## Scope

### In Scope
- Add Desktop client support for `GET /reporting/reports/operations?period_id=closure:{id}` with declared filters, sort, direction, limit, and offset.
- Normalize operation rows, pagination metadata, status, warnings, and API errors in the reporting controller.
- Extend the closed-report detail view with operation rows, filters/sort/pagination/status controls, and tests.

### Out of Scope
- Dashboard reimplementation or broad report center replacement.
- PDF/XLSX export delivery or re-enabling export buttons.
- API, Mobile, or Installer changes.
- Open/current operation rows.
- Formal accounting ledger, event sourcing, audit inventory UI, historical plate UI, or production/remote probing.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `reproducible-closed-reports`: Add Desktop closed-report operation drill-down behavior using API-owned rows, pagination, filters, and explicit local/canonical boundaries.

## Approach

Extend the existing Desktop closed-report flow, not the dashboard. After a closed report provides a closure period or drill-down link, request operations with `period_id=closure:{id}` only. Keep query construction allow-listed, preserve API pagination metadata, and show local calendar reports as separate legacy/local consultation.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `utils/api_client.py` | Modified | Add operations endpoint wrapper with declared query params only. |
| `controllers/reportes_controller.py` | Modified | Normalize rows, filters, pagination, status, and errors. |
| `views/reportes.py` | Modified | Render closed-report operation table and controls. |
| `tests/test_api_client_session.py` | Modified | Prove endpoint construction and param omission. |
| `tests/test_reportes_controller.py` | Modified | Cover normalization, filters, pagination, and errors. |
| `tests/test_reportes_view.py` | Modified | Cover rendering, controls, status, and legacy boundary. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Closure id ambiguity | Medium | Only promise integer closure-backed periods or API drill-down links. |
| Large view changes | Medium | Keep UI changes narrow and test-driven under the 400-line review budget. |
| Local/canonical confusion | Medium | Label local calendar reports as legacy/local and separate from closed-report drill-down. |

## Rollback Plan

Revert the Desktop client/controller/view/test changes and this delta spec. Existing dashboard, closed-report loading, hidden exports, and local calendar consultation remain unchanged.

## Dependencies

- Existing API contract for `GET /reporting/reports/operations` with `period_id=closure:{id}`.
- Existing Desktop closed-report retrieval flow.

## Success Criteria

- [ ] Desktop lists API-owned operation rows for a loaded closed report.
- [ ] Filters, sorting, pagination, status, and API errors are covered by tests.
- [ ] Dashboard, exports, API, Mobile, Installer, and local calendar reporting behavior remain out of scope.
