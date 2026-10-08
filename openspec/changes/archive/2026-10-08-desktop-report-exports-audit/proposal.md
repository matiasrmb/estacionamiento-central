# Proposal: Desktop Closed Report Exports

## Intent

Enable Desktop admins to export API-backed closed reports as PDF/XLSX through the existing controller/API path, removing the current UI deferral without expanding audit, API, Mobile, or installer scope.

## Scope

### In Scope
- Show and enable closed-report PDF/XLSX controls only after a valid API-backed closed report with a closure reference is loaded.
- Route clicks through `exportar_reporte_cerrado` and the existing API wrapper.
- Surface saved file path/status on success and preserve API/controller details on recoverable errors.
- Keep CSV absent and unsupported.
- Prevent local calendar reports from fabricating exports or API-owned closed-report outputs.

### Out of Scope
- Audit inventory visibility; follow-up after export enablement.
- API, Mobile, Installer, database, packaging, CSV, or local fallback export behavior.
- User-selected destination UX unless design proves the current `reportes/` convention is insufficient.

## Capabilities

### New Capabilities
- None

### Modified Capabilities
- `reproducible-closed-reports`: Replace the Desktop export deferral boundary with closed-report PDF/XLSX UI enablement requirements.

## Approach

Use the existing Desktop plumbing. `views/reportes.py` owns export button visibility/enabled state and status messages. `controllers/reportes_controller.py` continues writing API export bytes through `exportar_reporte_cerrado`. The smallest acceptable destination behavior is the existing local `reportes/` folder because current Desktop exports already use that convention; design may only introduce user-selected destinations if needed for recoverability without broadening scope.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `views/reportes.py` | Modified | Enable PDF/XLSX controls for valid API closed reports and keep errors recoverable. |
| `controllers/reportes_controller.py` | Modified | Preserve export result/status details if a tiny hardening gap is found. |
| `tests/test_reportes_view.py` | Modified | Cover visibility, enabled/disabled state, success path, and error path. |
| `tests/test_reportes_controller.py` | Modified | Focused regression only if controller result details need hardening. |
| `openspec/changes/desktop-report-exports-audit/specs/reproducible-closed-reports/spec.md` | New | Delta spec for Desktop export enablement. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Export controls become active for stale or local reports | Med | Gate on current API-backed closed report plus closure id. |
| Errors hide API details or leave disabled UI | Med | Preserve controller details and avoid destructive state resets on failure. |
| Audit scope expands the slice | Med | Keep audit inventory explicitly deferred. |

## Rollback Plan

Revert `views/reportes.py`, any controller hardening, related tests, and the delta spec; hidden/deferred export behavior returns unchanged.

## Dependencies

- Existing Desktop API token/session and `/reporting/exports/{closure_id}.{format}` wrapper.

## Success Criteria

- [ ] PDF/XLSX controls appear only for API-backed closed reports with closure reference.
- [ ] PDF/XLSX clicks save through `exportar_reporte_cerrado` and show the saved path/status.
- [ ] API/controller errors remain visible and the UI can retry.
- [ ] CSV and local calendar export fabrication remain absent.
