# Proposal: Desktop Intelligence Center Reporting and Audit Slice

## Intent

Make Desktop reporting consume and render the canonical Intelligence Center dashboard contract while staying repo-scoped. This derivative exists because direct umbrella apply remains blocked by `cross_common_dir_runtime_target`, so runtime accounting must be kept inside the Desktop repository.

## Scope

### In Scope
- Add controller tests for canonical API normalization and incomplete/local fallback metadata.
- Update `controllers/reportes_controller.py` to expose canonical fields and label local fallback as incomplete/local.
- Add view tests for canonical labels, warnings, period state, capacity, and Desktop-only closed/export entry points.
- Update `views/reportes.py` to render canonical labels, completeness warnings, capacity, period state, and roadmap boundaries.

### Out of Scope
- API, Mobile, Installer, printer agent, database schema, and API endpoint implementation changes.
- Consuming closed/export API endpoints in this slice.
- Formal accounting, auditor-role workflows, taxes, commissions, or ML anomaly scoring.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `operational-dashboard`: Desktop rendering must show canonical dashboard labels, period state, source state, completeness, and capacity metadata.
- `canonical-reporting-api`: Desktop controller normalization must preserve canonical reporting fields and mark local fallback as incomplete/local.
- `reproducible-closed-reports`: Desktop must expose closed/export roadmap boundaries without implementing API-backed closed/export flows.

## Approach

Use the existing `obtener_resumen_dashboard_reportes()` boundary. First RED-cover controller payload normalization, then RED-cover the PySide report view. Implementation should preserve API-provided labels, add machine-readable incomplete/local fallback metadata, and render Desktop-only closed/export boundary copy without adding API client methods.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `tests/test_reportes_controller.py` | Modified | RED tests for normalization and fallback completeness. |
| `controllers/reportes_controller.py` | Modified | Canonical payload fields and local fallback metadata. |
| `tests/test_reportes_view.py` | Modified | View tests for labels, warnings, state, capacity, and boundaries. |
| `views/reportes.py` | Modified | Render canonical metadata and roadmap boundary UI. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| View label overrides hide canonical API labels. | Med | Test that API labels are preserved. |
| Closed/export UI grows into endpoint consumption. | Med | Keep boundaries non-calling and document prerequisite. |
| Live API lacks PR #80/#81/#82 fields. | Med | Keep Desktop tests payload-driven; treat API chain as runtime prerequisite/risk. |

## Rollback Plan

Revert this change folder and the later Desktop test/controller/view edits. No data migration, API contract mutation, or installer rollback is required.

## Dependencies

- Runtime verification against a live API requires PR chain #80/#81/#82 or equivalent canonical API work.
- Desktop test runner: `python -m unittest discover -s tests`.

## Success Criteria

- [ ] Controller tests prove canonical API fields and incomplete/local fallback metadata.
- [ ] View tests prove labels, warnings, period state, capacity, and boundary entry points.
- [ ] Desktop implementation changes stay under the 400-line review budget or are split/approved.
