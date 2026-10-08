# Archive Report: Desktop Closed Report Exports

## Change

- Name: `desktop-report-exports-audit`
- Archived at: `openspec/changes/archive/2026-10-08-desktop-report-exports-audit/`
- Store mode handled: hybrid (`openspec` filesystem archive plus Engram archive report)
- Native status before archive: `dependencies.archive=ready`, `nextRecommended=archive`, `taskProgress=14/14`

## Final State

- Tasks complete: 14/14
- Requirements verified: 2/2
- Scenarios verified: 9/9
- Critical findings: 0
- Blockers: 0
- Implementation files changed by the apply phase: `views/reportes.py`, `tests/test_reportes_view.py`
- Controller hardening was inspected and not required.
- Delivery forecast remains low risk; a single PR is likely and no size exception is expected from the current diff.

## Verification Evidence

```text
python -m unittest tests.test_reportes_view
Exit code: 0
Ran 14 tests
OK

python -m unittest tests.test_reportes_view tests.test_reportes_controller
Exit code: 0
Ran 40 tests
OK

python -m unittest discover -s tests
Exit code: 0
Ran 412 tests
OK
```

## Specs Synced

| Domain | Action | Details |
|--------|--------|---------|
| `reproducible-closed-reports` | Updated | Applied two `MODIFIED` requirements: `PDF/XLSX Export Reproducibility Boundary` and `Desktop Closed and Export Roadmap Boundaries`. |

The canonical spec now enables Desktop PDF/XLSX exports only for loaded API-backed closed reports with a closure reference, keeps CSV absent, preserves local-calendar isolation, routes PDF/XLSX through `exportar_reporte_cerrado`, and requires retryable/actionable export errors.

## Archive Contents

- `proposal.md` ✅
- `specs/reproducible-closed-reports/spec.md` ✅
- `design.md` ✅
- `tasks.md` ✅ (14/14 tasks complete)
- `apply-progress.md` ✅
- `verify-report.md` ✅ (2 requirements, 9 scenarios)
- `exploration.md` ✅
- `archive-report.md` ✅

## Source of Truth Updated

- `openspec/specs/reproducible-closed-reports/spec.md`

## Mechanical Operations

### Spec composition

Command executed:

```text
gentle-ai sdd-archive-compose --canonical "openspec/specs/reproducible-closed-reports/spec.md" --delta "openspec/changes/desktop-report-exports-audit/specs/reproducible-closed-reports/spec.md" --output "openspec/specs/reproducible-closed-reports/spec.md.compose-tmp"
Move-Item "openspec/specs/reproducible-closed-reports/spec.md.compose-tmp" "openspec/specs/reproducible-closed-reports/spec.md"
```

Composition output:

```text
```

### Archive folder move

`git mv` was attempted first and refused because the source folder was untracked. The archive transaction verified the source against the pre-move snapshot, then used a plain filesystem move and compared the destination against that snapshot.

Move output:

```text
fatal: source directory is empty, source=openspec/changes/desktop-report-exports-audit, destination=openspec/changes/archive/2026-10-08-desktop-report-exports-audit
```

Pre-fallback source diff output (`diff -r snapshot/source openspec/changes/desktop-report-exports-audit`):

```text
```

Archive destination diff output (`diff -r snapshot/source openspec/changes/archive/2026-10-08-desktop-report-exports-audit`):

```text
```

Empty diff output is the passing readback evidence.

## Engram Traceability

Full observations read during archive:

- `sdd/desktop-report-exports-audit/proposal`: #1776
- `sdd/desktop-report-exports-audit/spec`: #1778
- `sdd/desktop-report-exports-audit/design`: #1779
- `sdd/desktop-report-exports-audit/tasks`: #1780
- `sdd/desktop-report-exports-audit/apply-progress`: #1781
- `sdd/desktop-report-exports-audit/verify-report`: #1783

The filesystem tasks and verify artifacts are the final terminal record for this archive. Engram observations #1780 and #1783 were older intermediate copies with stale checkbox/scenario counts; the final OpenSpec artifacts and launch facts show 14/14 tasks and 9/9 scenarios.

## Readiness Checks

- Main specs updated correctly: ✅
- Change folder moved to archive: ✅
- Archive contains proposal, specs, design, tasks, apply progress, and verify report: ✅
- Archived `tasks.md` has no unchecked implementation tasks: ✅
- Active changes directory no longer has `desktop-report-exports-audit`: ✅
- Verbatim diff readback output included and empty: ✅

## SDD Cycle Complete

The change has been fully planned, implemented, verified, and archived. Ready for delivery preparation.
