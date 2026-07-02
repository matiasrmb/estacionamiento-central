# Proposal: Operations UX and Pricing Improvements

## Problem Statement

Daily operation is split across flows that force workarounds: lavados require an active ingreso, mobile operators jump between screens, cotización is incomplete, wash pricing is hard-coded, and user deletion/printing support lack safe operational rules. The change must improve speed without corrupting caja, reports, tickets, or current ingreso+lavado behavior.

## Goals / Non-Goals

**Goals**
- Add solo lavado, cotización, configurable wash pricing, safe user delete, unified mobile operation, and printer diagnostics guidance.
- Preserve current ingreso, salida, ingreso+lavado, cierre, and reporting accuracy.
- Slice delivery into chained PRs under the 400-line review budget.

**Non-goals**
- No vehicle-size pricing for parking estadía.
- No removal of deactivate, Lavados/Baño, or current salida flow.
- No guarantee for unreliable generic thermal drivers.

## Capabilities

### New Capabilities
- `wash-only-operations`: solo lavado start/finalize, with charge-now or convert-to-stay outcomes.
- `operation-accounting-tickets`: cierre/report/ticket handling for wash-only and wash+stay temporal/monetary detail.
- `quote-pricing`: quote estadía, lavados, mensualidad, and combinations; monthly supports multiple vehicles and daily breakdowns.
- `configurable-wash-pricing`: configurable vehicle/wash types and values for wash pricing only.
- `safe-user-deletion`: hard delete only when no activity exists; otherwise deactivate/soft-delete.
- `unified-mobile-operations`: one mobile search, newest-first list, contextual actions, bathroom access, and lavados plate search.
- `printer-support-diagnostics`: supported driver/Sumatra guidance, diagnostics, and test-print workflow.

### Modified Capabilities
- None; no existing OpenSpec specs are present.

## Scope Boundaries

- Current washing inside a normal parking ingreso remains compatible.
- Wash→stay starts parking at wash end and then follows normal salida wherever possible.
- Wash+stay tickets show wash start/end/duration/amount and stay start/end/duration/amount/total.
- Parking tariff model remains independent of vehicle size.
- All money-affecting operations require auditable timestamps, users, status, and historical price snapshots.

## Proposed Approach

Use additive contracts. Desktop/API/DB add service-operation records for solo lavado instead of fake ingresos; API exposes new endpoints without breaking existing ones; Mobile adds a unified screen while keeping existing modules; tickets/cierres aggregate new finalized service revenue. Seed dynamic wash pricing from current config keys and keep historical labels/values on rows.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| Desktop `controllers/`, `views/`, `utils/ticket.py` | Modified | Cotización, solo lavado UX, tickets, users, config. |
| API `app/api/v1/`, `repositories/`, `schemas/` | Modified | New additive endpoints and accounting payloads. |
| DB `schema.sql` / migrations | Modified | Service operations, type tables, audit/snapshot fields. |
| Mobile `lib/features/` | Modified | Unified operation and lavados search. |
| Printer agent/docs | Modified | Diagnostics, test print, support guidance. |

## Rollout / Slicing Strategy

Chained PRs required: quote preview; configurable pricing foundation; wash-only backend/accounting; Desktop UX/tickets; Mobile unification; safe user deletion; printer diagnostics. Ask before apply for exact chain strategy.

## Validation Strategy

- Strict TDD per repo: Desktop/API `python -m unittest discover -s tests`; Mobile `flutter test` and `flutter analyze`.
- Accounting regression tests for cierre totals, wash→stay billing, and current ingreso+lavado.
- Manual printer validation with configured Sumatra/printer plus visible diagnostics.

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Caja/report mismatch | High | Add accounting tests before UI work. |
| Breaking existing lavado | Medium | Keep old APIs/flow unchanged. |
| PRs too large | High | Chain by capability under 400 lines. |

## Dependencies

- Decide whether cierre metrics count solo lavado separately from ingresos/salidas.

## Success Criteria

- [ ] Current ingreso+lavado and parking salida behavior still pass regression tests.
- [ ] Solo lavado supports charge-now and wash→stay with auditable tickets/caja totals.
- [ ] Cotización, mobile unification, user deletion, and printer diagnostics are delivered in reviewable slices.
