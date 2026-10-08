# Archive Report: Desktop Financial Operational Reports

## Change

- Name: `desktop-financial-operational-reports`
- Archived at: `openspec/changes/archive/2026-10-08-desktop-financial-operational-reports/`
- Store mode handled: hybrid (`openspec` filesystem archive plus Engram archive report)
- Native status before archive: `dependencies.archive=ready`, `nextRecommended=archive`, `taskProgress=17/17`

## Final State

- All 17 tasks are complete in the archived OpenSpec `tasks.md` artifact.
- Focused reporting verification passed: `python -m unittest tests.test_api_client_session tests.test_reportes_controller tests.test_reportes_view` → 53 tests OK.
- Full discovery remains warning-only for this change: `python -m unittest discover -s tests` ran 410 tests with one unrelated/time-dependent failure in `test_registrar_ingreso_retorna_true_con_fecha_hora_personalizada_valida`.
- Native verify settlement evidence: `sha256:0504374fbb7c8e93cf30744149487161ebd04ef567e38ccc4e2e142b926f3637`.
- The maintainer approved an SDD ledger reset after apply exceeded the changed-line budget: the actual attempt changed 601 lines against the 450-line attempt budget, then verification passed with the warning above.
- Delivery remains unresolved under the 400-line review policy. The implementation is archived as an SDD cycle, but PR readiness still requires a split/chained PR decision or an explicit `size:exception` with an approved issue.

## Specs Synced

| Domain | Action | Details |
|--------|--------|---------|
| `reproducible-closed-reports` | Updated | Added Desktop closed-report operation drill-down, API-owned query controls, and local report boundary requirements. |

## Source of Truth Updated

- `openspec/specs/reproducible-closed-reports/spec.md`

## Archive Contents

- `proposal.md` ✅
- `specs/reproducible-closed-reports/spec.md` ✅
- `design.md` ✅
- `tasks.md` ✅ (17/17 implementation tasks complete)
- `apply-progress.md` ✅
- `verify-report.md` ✅
- `exploration.md` ✅
- `archive-report.md` ✅

## Engram Traceability

Artifacts read for this archive:

- Proposal: observation `#1754`, topic `sdd/desktop-financial-operational-reports/proposal`
- Spec: observation `#1755`, topic `sdd/desktop-financial-operational-reports/spec`
- Design: observation `#1756`, topic `sdd/desktop-financial-operational-reports/design`
- Tasks: observation `#1757`, topic `sdd/desktop-financial-operational-reports/tasks`
- Verify report: observation `#1762`, topic `sdd/desktop-financial-operational-reports/verify-report`

### Hybrid Reconciliation

Engram observation `#1757` initially still showed stale unchecked task boxes, while the OpenSpec `tasks.md`, `apply-progress.md`, `verify-report.md`, refreshed native SDD status, and orchestrator final-state facts all reported 17/17 tasks complete. Before archiving, observation `#1757` was reconciled to the final checked task state so hybrid completion visibility matches the archived OpenSpec task artifact.

## Mechanical Archive Evidence

### Spec composition command

```text
gentle-ai sdd-archive-compose --canonical "openspec/specs/reproducible-closed-reports/spec.md" --delta "openspec/changes/desktop-financial-operational-reports/specs/reproducible-closed-reports/spec.md" --output "openspec/specs/reproducible-closed-reports/spec.md.compose-tmp"
Move-Item -LiteralPath "openspec\\specs\\reproducible-closed-reports\\spec.md.compose-tmp" -Destination "openspec\\specs\\reproducible-closed-reports\\spec.md" -Force
```

Result: zero exit; no stderr/stdout.

### Archive move readback

The archive folder was moved mechanically from `openspec/changes/desktop-financial-operational-reports` to `openspec/changes/archive/2026-10-08-desktop-financial-operational-reports`. `git mv` reported the source as empty/untracked and the shell transaction fell back to `mv` after confirming the source matched the pre-move snapshot.

Verbatim `diff -r` readback output between the pre-move snapshot and archived destination:

```text
```

Empty output is the passing evidence for byte-identical archive movement.

## Verification Checklist

- [x] Main specs updated correctly.
- [x] Change folder moved to archive.
- [x] Archive contains proposal, specs, design, tasks, apply-progress, verify-report, exploration, and archive-report artifacts.
- [x] Archived `tasks.md` has no unchecked implementation tasks.
- [x] Active `openspec/changes/desktop-financial-operational-reports/` no longer exists.
- [x] Verbatim `diff -r` readback output is included above and is empty.

## Risks and Follow-Up

- Full unittest discovery still has one unrelated/time-dependent failure in `test_registrar_ingreso_retorna_true_con_fecha_hora_personalizada_valida`.
- Delivery is not PR-ready until the parent resolves the 400-line review policy with a split/chained PR or explicit `size:exception` backed by an approved issue.

## SDD Cycle Status

The change has been planned, implemented, verified, and archived with warnings preserved. Delivery policy resolution remains outside archive completion.
