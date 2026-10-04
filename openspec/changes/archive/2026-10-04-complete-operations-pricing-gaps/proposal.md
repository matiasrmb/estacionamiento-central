# Proposal: Complete Operations Pricing Gaps

## Intent

Close the highest-risk pricing/reporting gap by bringing Desktop solo lavado accounting in line with existing API semantics: charged solo lavados must appear in daily closures and reports, while converted solo lavados remain deferred until parking exit.

## Scope

### In Scope
- Include `FINALIZADO_COBRADO` solo lavados from `operaciones_servicio` in Desktop cierres and report totals/items.
- Exclude `ACTIVO` and `CONVERTIDO_ESTADIA` solo lavados from immediate accounting.
- Mark charged solo lavados as closed so later closures do not count them again.
- Add additive/idempotent Desktop schema support for solo-lavado closure fields needed by the accounting flow.

### Out of Scope
- Persistent quote/contract records, quote numbering, expiry, PDFs, or conversion workflows.
- Mobile quote expansion for estadía, mensualidad, or combined services.
- Monthly customer operational billing automation until business rules are confirmed.
- API behavior changes beyond regression coverage; API is the semantic reference.
- Installer schema parity unless split into a separately reviewed slice.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `wash-operations`: finalize solo lavado accounting semantics for Desktop closure/report inclusion and one-time closure marking.
- `canonical-reporting-api`: preserve payment-focused reporting semantics by including charged solo lavado operational income in Desktop local reports.
- `reproducible-closed-reports`: ensure persisted Desktop closure references include solo lavado totals once closed.

## Approach

Use the API solo lavado accounting behavior as reference. Wire Desktop cierres/reportes to existing accounting helper semantics instead of duplicating pricing rules. Apply schema changes additively and idempotently before querying new columns.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `controllers/cierres_controller.py` | Modified | Include and close charged solo lavados. |
| `controllers/reportes_controller.py` | Modified | Include charged solo lavados in report totals/items. |
| `controllers/accounting_contracts.py` | Modified | Reuse or extend shared accounting helpers if needed. |
| `schema.sql` | Modified | Add solo-lavado closure support additively. |
| `tests/` | Modified | Add strict TDD coverage for inclusion, exclusion, and no double counting. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Existing databases lack new columns | Medium | Use additive/idempotent schema ensure before reads/writes. |
| Double counting converted washes | Medium | Test `CONVERTIDO_ESTADIA` exclusion explicitly. |
| Scope creep into quotes/monthly billing | High | Keep unresolved business-policy gaps out of this change. |

## Rollback Plan

Revert Desktop controller/helper/test changes. Leave additive schema columns in place but stop writing/reading them; no destructive migration is required.

## Dependencies

- Later spec/design/tasks phases must define exact Desktop requirements and schema migration/ensure points.
- Business decisions are required before quote persistence or monthly billing can be proposed.

## Success Criteria

- [ ] Desktop closures include one charged solo lavado in solo-lavado totals and `total_general`.
- [ ] Active and converted solo lavados are excluded from immediate Desktop accounting.
- [ ] Closed charged solo lavados are not counted by later closures.
- [ ] Desktop reports include charged solo lavados without changing API/Mobile behavior.
