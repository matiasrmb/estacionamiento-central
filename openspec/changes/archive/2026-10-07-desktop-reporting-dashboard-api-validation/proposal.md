# Proposal: Desktop Reporting Dashboard API Validation

## Intent

Validate and align the existing Desktop reporting dashboard client with the canonical API contract. The archived Desktop dashboard is already implemented; this change closes the deferred API-validation gap and removes misleading dashboard query parameters that the API does not own.

## Scope

### In Scope
- Add/adjust Desktop mocked contract tests for metric catalog and dashboard payload compatibility.
- Align the Desktop dashboard request shape with `GET /reporting/dashboard` by removing unowned `period_id=current&state=open` parameters unless the API later declares them.
- Keep the existing dashboard rendering, normalization, fallback behavior, and local report table flows intact.
- Optionally document/run local API smoke for metric catalog and dashboard only when an authenticated seeded local API is available.

### Out of Scope
- Reimplementing the archived Desktop Intelligence Center dashboard.
- Desktop operations drill-down or pagination UI for `/reporting/reports/operations`.
- API, Mobile, or Installer changes.
- Remote, production, or unauthenticated environment validation.
- Broad production refactors beyond the minimal adapter cleanup.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `operational-dashboard`: Desktop dashboard consumption must use only API-owned dashboard request parameters and prove compatibility through mocked contract tests.

## Approach

Use validation-first Desktop work: tighten API-client/session tests around canonical endpoint construction, cover current dashboard payload metadata preservation in controller/view tests, and make only the minimal adapter cleanup needed to stop sending unowned dashboard query parameters. Treat local seeded API smoke as optional verification evidence, not a delivery gate.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `utils/api_client.py` | Modified | Remove unowned dashboard query parameters if still present. |
| `tests/test_api_client_session.py` | Modified | Assert canonical metric catalog and dashboard request construction. |
| `tests/test_reportes_controller.py` | Modified | Preserve dashboard payload compatibility coverage. |
| `tests/test_reportes_view.py` | Modified | Preserve rendering coverage for canonical metadata. |
| `openspec/specs/operational-dashboard/spec.md` | Modified | Delta spec for Desktop request-shape validation scope. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Seeded local API is unavailable | Medium | Keep smoke optional; require mocked contract tests. |
| Scope expands into dashboard rework | Low | Explicitly limit production changes to adapter cleanup. |
| Operations pagination is confused with dashboard needs | Low | Exclude drill-down/pagination UI from this change. |

## Rollback Plan

Revert the proposal/spec/tasks and any Desktop adapter/test changes from this change. The archived dashboard implementation remains untouched.

## Dependencies

- Existing Desktop reporting tests and canonical OpenSpec specs.
- Optional authenticated seeded local API for smoke validation only.

## Success Criteria

- [ ] Desktop tests prove canonical dashboard endpoint construction without unowned parameters.
- [ ] Mocked contract tests prove metric catalog and dashboard payload compatibility.
- [ ] No API, Mobile, Installer, drill-down, pagination UI, or broad dashboard production changes are introduced.
