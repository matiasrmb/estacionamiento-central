# Proposal: Corrected Reporting Intelligence and Audit Roadmap

## Intent

Create a planning-only corrected roadmap for the administrative/financial-operational Intelligence Center. It must reconcile merged work first, then define closure/journey reporting, Desktop/API authority, Mobile limits, and audit foundation.

## Scope

### In Scope
- Slice 0: classify premature API/Desktop/Mobile work as keep, change, remove, or defer; retire the old roadmap conceptually.
- Define official semantics: net revenue is all collected sources minus expenses for the closure/journey/period; monthly payments count where collected; calendar days are secondary.
- Plan configurable capacity, default/current 50 vehicles, with historical-capacity limitations labeled.
- Keep Desktop as full center, API as canonical contract, and Mobile as dashboard-only quick consultation.
- Plan cross-cutting audit and a first serious audit slice without event sourcing.
- Include basic deterministic anomalies in 1.3.0; allow PDF/XLSX in 1.3.x.

### Out of Scope
- Code changes, reverts, version bumps, branches, implementation.
- Formal accounting, taxes, commissions, ledgers, or event sourcing.
- Treating Desktop local fallback as official closure truth.

## Capabilities

### New Capabilities
- None expected.

### Modified Capabilities
- `canonical-reporting-api`: closure/journey semantics, payment timing, capacity, historical labels, anomaly contracts.
- `operational-dashboard`: Desktop full center, Mobile quick consultation, incomplete/local labels.
- `reproducible-closed-reports`: closure/journey truth and 1.3.x export boundaries.
- `admin-reporting-access`: audit goal, audit slice, admin access, non-accounting limits.

## Approach

Start with Slice 0 before implementation specs: reconcile merged artifacts against corrected decisions and produce keep/change/remove/defer outcomes. Later phases must split repo-scoped derivatives under the 400-line policy.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `openspec/changes/centro-inteligencia-reportes-auditoria-13-roadmap/` | Superseded | Historical context, not execution authority. |
| `openspec/specs/canonical-reporting-api/` | Modified | Metrics, periods, capacity, anomalies. |
| `openspec/specs/operational-dashboard/` | Modified | Desktop/Mobile/fallback boundaries. |
| `openspec/specs/reproducible-closed-reports/` | Modified | Closure/journey truth and export timing. |
| `openspec/specs/admin-reporting-access/` | Modified | Audit slice and non-accounting limits. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Premature implementation shapes the roadmap | High | Require Slice 0 before specs/design/tasks. |
| Local fallback is confused with truth | Medium | Require incomplete/local labels and prohibit official fallback claims. |
| Scope exceeds review budget | High | Use repo-scoped derivatives and chained review slices. |

## Rollback Plan

Planning-only: remove this folder and Engram artifact. No code, data, branches, or versions change.

## Dependencies

- Parent-approved Discovery and corrected product decisions.
- Existing OpenSpec reporting capabilities and archived derivative evidence.

## Success Criteria

- [ ] Slice 0 reconciliation is specified before implementation planning.
- [ ] Specs can update existing capabilities with corrected semantics.
- [ ] Roadmap excludes implementation and formal accounting behavior.
- [ ] Next phase can produce delta specs without re-litigating product decisions.
