# Proposal: Desktop Closed Reports and Exports

## Intent

Make Desktop's visible closed-report and export actions operational by consuming already-archived API reporting/export contracts, replacing roadmap-only placeholders with admin-facing API-backed behavior.

## Scope

### In Scope
- Add Desktop client/controller support for API-backed closed-report retrieval.
- Add Desktop PDF/XLSX export request handling and correct the current PDF/CSV mismatch.
- Render closed-report metadata, reproducibility/source/completeness state, warnings, and API errors in the existing reports UI.

### Out of Scope
- API endpoint, schema, installer, Mobile, or database changes.
- Historical plate, anomaly, statistics, event-log, or anomaly-persistence UI.
- Formal accounting, taxes, commissions, auditor role, or payment-method ledger behavior.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `reproducible-closed-reports`: Replace Desktop roadmap-boundary-only closed/export behavior with operational API-backed closed-report retrieval and PDF/XLSX export flows.

## Approach

Keep the derivative Desktop-only. Extend `utils/api_client.py` additively for closed report and export endpoints, normalize payloads in `controllers/reportes_controller.py`, and update `views/reportes.py` to trigger operational flows while preserving admin-only reporting boundaries and incomplete/source-state warnings.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `utils/api_client.py` | Modified | Add closed-report and PDF/XLSX export API calls. |
| `controllers/reportes_controller.py` | Modified | Normalize closed metadata, reproducibility fields, source/completeness state, and export results/errors. |
| `views/reportes.py` | Modified | Replace future-only actions with operational closed/export UI behavior. |
| `tests/test_reportes_controller.py` | Modified | Cover payload normalization, export handling, and API error paths. |
| `tests/test_reportes_view.py` | Modified | Cover operational UI actions and warning states. |
| `openspec/specs/reproducible-closed-reports/spec.md` | Modified | Delta spec will update Desktop closed/export requirements. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| API payload or endpoint names differ from archived contracts. | Med | Confirm contract details in spec/design before implementation. |
| Export file handling expands UI scope. | Med | Keep Desktop behavior to request/download/open response only as specified. |
| Work exceeds the 400-line review budget. | Med | Keep tasks narrow and ask-on-risk if task forecast grows. |

## Rollback Plan

Revert the proposal/spec/design/tasks/apply changes for this derivative; Desktop then returns to the existing non-operational closed/export roadmap boundaries with no API, database, installer, or Mobile rollback needed.

## Dependencies

- Archived API canonical reporting/export contracts must remain compatible and available at runtime.

## Success Criteria

- [ ] Desktop retrieves and displays API-backed closed reports with reproducibility/source/completeness metadata.
- [ ] Desktop requests PDF and XLSX exports without exposing the old PDF/CSV promise.
- [ ] Tests cover normal, incomplete, and API-error closed/export paths.
