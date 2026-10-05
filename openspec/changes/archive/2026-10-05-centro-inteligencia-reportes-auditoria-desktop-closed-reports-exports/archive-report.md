# Archive Report: Desktop Closed Reports and Exports

## Status

Archived successfully on 2026-10-05.

## Change

- Change: `centro-inteligencia-reportes-auditoria-desktop-closed-reports-exports`
- Artifact store: `openspec`
- Archived to: `openspec/changes/archive/2026-10-05-centro-inteligencia-reportes-auditoria-desktop-closed-reports-exports/`

## Source-of-Truth Sync

| Domain | Action | Evidence |
|--------|--------|----------|
| `reproducible-closed-reports` | Updated existing canonical spec | Native `gentle-ai sdd-archive-compose` completed with exit code 0 and replaced `openspec/specs/reproducible-closed-reports/spec.md`. |

Command:

```text
gentle-ai sdd-archive-compose --canonical "openspec/specs/reproducible-closed-reports/spec.md" --delta "openspec/changes/centro-inteligencia-reportes-auditoria-desktop-closed-reports-exports/specs/reproducible-closed-reports/spec.md" --output "openspec/specs/reproducible-closed-reports/spec.md.compose-tmp"
```

## Final-State Evidence

- Native status reported `dependencies.archive: ready` and `nextRecommended: archive` for the selected change.
- Persisted `tasks.md` shows 14 of 14 tasks complete and no unchecked implementation tasks.
- Persisted `verify-report.md` reports `critical_findings: 0`, no blockers, and verdict `pass_with_warnings`.
- Parent final-state facts confirm final full discovery passed: `python -m unittest discover -s tests` -> 397 OK.

## Archive Contents

- `proposal.md`
- `specs/reproducible-closed-reports/spec.md`
- `design.md`
- `tasks.md`
- `apply-progress.md`
- `verify-report.md`
- `exploration.md`
- `archive-report.md`

## Mechanical Readback

The change folder was moved with a shell transaction. `git mv` refused because the source was not tracked as a non-empty Git directory operation; the guarded fallback verified the pre-move source against the snapshot and then used `Move-Item`. The mandatory final recursive diff compared the pre-move snapshot with the archived destination and produced no output.

```text

```

## Findings and Warnings

- No critical findings blocked archive.
- Remaining warning: view tests cover totals through `total_general`, `total_gastos`, and `total_neto`; a future hardening assertion may target canonical `operation_totals` keys if the API contract confirms those keys are exclusive.

## Completion

The SDD cycle is complete for this change. The canonical spec now reflects Desktop API-backed closed-report retrieval and PDF/XLSX export behavior, and the active change directory no longer contains this change.
