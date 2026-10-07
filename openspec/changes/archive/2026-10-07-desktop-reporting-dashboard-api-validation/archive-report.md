# Archive Report: Desktop Reporting Dashboard API Validation

## Status

Partial archive completed with an evidence gap.

The canonical OpenSpec spec was updated and the active change folder was moved to `openspec/changes/archive/2026-10-07-desktop-reporting-dashboard-api-validation/`. However, the mandatory pre-move `diff -r` readback was not captured during the move transaction because PowerShell resolved `diff` to `Compare-Object` instead of GNU diff. This archive report records that gap explicitly instead of overstating byte-identity evidence.

## Final State

- Change: `desktop-reporting-dashboard-api-validation`
- Archive location: `openspec/changes/archive/2026-10-07-desktop-reporting-dashboard-api-validation/`
- Canonical spec updated: `openspec/specs/operational-dashboard/spec.md`
- Active change folder removed: yes
- Archived tasks complete: 9/9 implementation tasks complete
- Verify verdict: PASS
- Requirements: 4/4
- Scenarios: 8/8
- Scope: Desktop-only

## Specs Synced

| Domain | Action | Details |
|---|---|---|
| `operational-dashboard` | Updated | Applied four ADDED requirements from the delta spec through `gentle-ai sdd-archive-compose`. |

### Composition Evidence

Command:

```text
gentle-ai sdd-archive-compose --canonical "openspec/specs/operational-dashboard/spec.md" --delta "openspec/changes/desktop-reporting-dashboard-api-validation/specs/operational-dashboard/spec.md" --output "openspec/specs/operational-dashboard/spec.md.compose-tmp"
Move-Item "openspec/specs/operational-dashboard/spec.md.compose-tmp" "openspec/specs/operational-dashboard/spec.md"
```

Result: exit code 0; no stdout/stderr was emitted.

## Archive Move Evidence

Attempted transaction:

```text
source=openspec/changes/desktop-reporting-dashboard-api-validation
destination=openspec/changes/archive/2026-10-07-desktop-reporting-dashboard-api-validation
```

Observed result:

```text
fatal: source directory is empty, source=openspec/changes/desktop-reporting-dashboard-api-validation, destination=openspec/changes/archive/2026-10-07-desktop-reporting-dashboard-api-validation

InputObject                                                                    SideIndicator
-----------                                                                    -------------
openspec/changes/desktop-reporting-dashboard-api-validation                    =>
C:/Users/matia/AppData/Local/Temp/opencode/sdd-archive.WLh5Jf/source           <=
openspec/changes/archive/2026-10-07-desktop-reporting-dashboard-api-validation =>
C:/Users/matia/AppData/Local/Temp/opencode/sdd-archive.WLh5Jf/source           <=
```

The output above is not valid GNU `diff -r` evidence. It is retained to make the audit trail honest.

## Archive Contents

- `proposal.md`
- `exploration.md`
- `research.md`
- `design.md`
- `tasks.md`
- `apply-progress.md`
- `verify-report.md`
- `specs/operational-dashboard/spec.md`
- `archive-report.md`

## Tests and Evidence Referenced

- Focused verification: `python -m unittest tests.test_api_client_session tests.test_reportes_controller tests.test_reportes_view` passed with 42 tests.
- Full verification: `python -m unittest discover -s tests` passed with 399 tests.
- Parent spot-check after verify: focused command passed again with 42 tests.
- Live API smoke was not run and remains optional by spec and design.

## Scope Boundary

No API, Mobile, Installer, operations drill-down, pagination UI, remote validation, or production-data probing changes are part of this archive.

## Risk

The archive location and canonical spec update are present, but the required pre-move GNU `diff -r` readback is missing. Treat the archive as operationally moved but not fully byte-identity-proven by the SDD archive mechanical-copy contract.
