# Proposal: Desktop Report Audit Visibility

## Intent

Expose existing dashboard audit coverage/status data in Desktop so admins can see audit limitations in the reporting Intelligence Center without expanding API, Mobile, Installer, database, or endpoint scope.

## Scope

### In Scope
- Render compact audit coverage/status in the existing Desktop reporting dashboard metadata area.
- Preserve and, only if needed, normalize existing `audit_coverage` dashboard variants into stable UI text.
- Label local fallback reports as unavailable/local/non-official for audit coverage without fabricating coverage.
- Add focused controller/view tests for API coverage rendering and local fallback boundaries.

### Out of Scope
- API, Mobile, Installer, database, migrations, remote validation, or new endpoint work.
- Rich audit inventory workbench, event sourcing, ledger UI, anomaly UI, or closed-report audit workbench unless already directly supported by the current dashboard payload in a tiny display-only way.
- Formal accounting, tax, commission, payment-method accounting, or auditor-role workflows.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `operational-dashboard`: Desktop dashboard rendering adds compact audit coverage/status from existing payload metadata and keeps local fallback non-official.
- `admin-reporting-access`: Desktop surfaces existing-source audit limitations when dashboard coverage data is available.

## Approach

Use the current `GET /reporting/dashboard` flow. `controllers/reportes_controller.py` already preserves `audit_coverage` and clears it for local fallback; add normalization only if tests reveal payload variants need stable fields. `views/reportes.py` will render concise coverage/status text beside existing source/completeness/capacity/warnings metadata. If spec/design validation proves the current API payload cannot support meaningful visibility beyond empty or unusable data, stop Desktop work and switch to API change `api-report-audit-inventory`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `controllers/reportes_controller.py` | Modified | Preserve/normalize dashboard audit coverage; keep local fallback empty. |
| `views/reportes.py` | Modified | Render compact audit coverage/status in the Intelligence Center/dashboard area. |
| `tests/test_reportes_controller.py` | Modified | Cover API coverage preservation and fallback non-fabrication. |
| `tests/test_reportes_view.py` | Modified | Cover coverage/status rendering and unavailable local state. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Live payload lacks meaningful `audit_coverage` | Medium | Stop Desktop and recommend `api-report-audit-inventory`. |
| UI growth in large `views/reportes.py` | Medium | Keep display compact and test-driven. |
| Local fallback appears official | Low | Explicit unavailable/local/non-official label and tests. |

## Rollback Plan

Revert the Desktop view/controller/test changes and remove the delta specs for this change. No persisted data, API contract, installer, or database rollback is required.

## Dependencies

- Existing dashboard payloads must provide usable `audit_coverage` or equivalent audit status metadata.

## Success Criteria

- [ ] API-backed dashboard audit coverage/status is visible in Desktop when supplied.
- [ ] Local fallback reports show audit coverage as unavailable/local/non-official.
- [ ] No API, Mobile, Installer, database, or new endpoint changes are introduced.
- [ ] Focused controller/view tests prove the behavior.
