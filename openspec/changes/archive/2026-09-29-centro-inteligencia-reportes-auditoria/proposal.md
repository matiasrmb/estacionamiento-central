# Proposal: Centro de Inteligencia, Reportes y Auditoría

## Intent

Create the 1.3.0 reporting foundation with canonical API metrics reused by Desktop and Mobile. Current reports have divergent names, filters, totals, and closure semantics.

## Scope

### In Scope
- Desktop: consume canonical metrics where practical; preserve current reports during parity migration.
- API: own report contracts, operational-day windows, operator-session filters, exports, closed-report replay, and discrepancy detection.
- Mobile: include API-backed dashboard/report consumption.
- Installer: package required config/migration assets only if needed.

### Out of Scope
- Ledger-grade accounting, taxes, commissions, payment-method accounting, and auditor role.
- Non-admin financial reporting access.
- Replacing all Desktop report internals before API parity.

## Capabilities

### New Capabilities
- `canonical-reporting-api`: canonical metric names, totals, filters, and exports.
- `operational-dashboard`: closure-based operational-day dashboard for Desktop and Mobile.
- `reproducible-closed-reports`: exact closed-period replay with drill-down and discrepancies.
- `admin-reporting-access`: admin-only financial, audit, and reporting access.

### Modified Capabilities
- None.

## Approach

Use the approved incremental hybrid architecture: data-first API read models become canonical while Desktop reports remain operational. Open periods calculate from operations. Closed periods preserve closure as administrative reference; reports reproduce exactly and show discrepancies. Net equals operational income minus expenses. Expenses are positive in lists and negative as result components. Financial reports focus on payments; commercial reports may focus on mensualidad.

## Decision Status

- Made: API-backed 1.3.0 Desktop/Mobile scope, closure-to-closure operational day, PDF+CSV, admin-only access, canonical names, reproducible closed reports, ~400 vehicles/day.
- Pending: exact canonical field list, endpoint shapes, export layouts, and discrepancy thresholds.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/repositories/reportes_repo.py` | New/Modified | Canonical queries and exports. |
| `controllers/reportes_controller.py` / `views/reportes.py` | Modified | Desktop parity checks. |
| `lib/features/admin/reportes/...` | Modified | Mobile reporting UI. |
| `EstacionamientoCentral.iss` | Modified | Package config/migrations if needed. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Desktop/API semantic drift | High | Contract tests around canonical names and totals. |
| Closed report reproducibility gaps | Medium | Snapshot immutable closure inputs and compare with operations. |
| Review scope exceeds 400 lines | Medium | Split tasks by repo and capability. |

## Rollback Plan

Keep current Desktop reports active until parity passes. Roll back new consumers and packaging without changing operational data or closure snapshots.

## Dependencies

- Follow-up specs/design/tasks must define canonical names, API contracts, export boundaries, reproducibility rules, and verification.

## Success Criteria

- [ ] Admins can view API-backed Desktop/Mobile 1.3.0 reporting for ~400 vehicles/day.
- [ ] Open periods calculate from operations and closed reports reproduce exactly.
- [ ] PDF and CSV exports use canonical names and totals.
- [ ] Accounting concerns remain excluded.
