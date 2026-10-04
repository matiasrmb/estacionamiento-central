# Proposal: Centro Inteligencia Reportes Auditoria 1.3 Roadmap

## Intent

Plan the next reporting and audit roadmap without mutating the archived 1.3.0 change. The system needs data-first closure-to-closure reporting, explicit historical completeness, and reusable API contracts so Desktop remains the main Intelligence Center while Mobile stays limited to daily operational summaries for 1.3.0.

## Scope

### In Scope
- Define canonical metric semantics, including operational net, closure-to-closure periods, after-midnight attribution, historical completeness labels, and 50-space capacity rules.
- Extend Desktop/API dashboard and report roadmap while constraining Mobile 1.3.0 to dashboard/operational summaries.
- Define reproducible PDF/XLSX exports linked to closures and metadata.
- Define audit-readiness boundaries: use existing audit inventory now; defer high-level transversal event log to 1.3.x.

### Out of Scope
- Implementing application code, version bumps, migrations, packaging, branches, commits, or PRs.
- Full high-level audit event log in immediate 1.3.0 core.
- Mobile closed reports/exports before later 1.3.x work.
- Presenting incomplete historical data as complete truth.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `canonical-reporting-api`: add approved operational net, closure-to-closure, after-midnight, capacity, and historical completeness semantics.
- `operational-dashboard`: define Desktop/API Intelligence Center roadmap and Mobile-limited 1.3.0 dashboard scope.
- `reproducible-closed-reports`: change exports from PDF/CSV to PDF/XLSX and require closure-linked reproducibility metadata.
- `admin-reporting-access`: clarify 1.3.0 audit inventory/readiness and defer transversal before/after event log to 1.3.x.

## Approach

Use API read models as the canonical contract. Prefer hybrid closure snapshots plus operational rows for drill-down and discrepancy reporting. Specs should state completeness/availability labels for historical metrics and keep calendar dates as secondary filters/grouping, not primary business-day semantics.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `views/reportes.py` / `controllers/reportes_controller.py` | Modified | Desktop Intelligence Center planning and local-report parity boundaries. |
| `estacionamiento-central-api` reporting endpoints | Modified | Canonical metrics, dashboard, closed reports, audit inventory, PDF/XLSX exports. |
| `estacionamiento_central_mobile/lib/features/admin/reportes/*` | Modified | Dashboard-only operational reporting scope for 1.3.0. |
| `estacionamiento-central-installer` | Modified | Future packaging/release evidence only when payloads, migrations, or dependencies change. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Historical reports imply false completeness | High | Require explicit completeness labels and unavailable/partial states. |
| Calendar filters override business-day truth | Medium | Specs must make closure-to-closure primary for operational/financial/audit reports. |
| Scope exceeds review budget | Medium | Split later work by capability and repo under the 400-line review policy. |

## Rollback Plan

This proposal is planning-only. Revert by removing this change folder and Engram artifact; no application code, data, packaging, or versions are changed.

## Dependencies

- Existing canonical reporting endpoints and specs.
- Later specs/design/tasks must define exact labels, fields, export metadata, and audit-readiness hooks.

## Success Criteria

- [ ] Specs can be created as deltas against existing capability names.
- [ ] Historical incompleteness is explicit and never reported as complete truth.
- [ ] Desktop/API own the full roadmap while Mobile 1.3.0 remains operational-dashboard only.
- [ ] PDF/XLSX closure-linked export requirements are unambiguous.
