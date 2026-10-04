# Proposal: Desktop Table Audit Search and Reports Accounting

## Intent

Improve Desktop table sorting/search and make Reports show dashboard-like cash-register clarity. Keep this Desktop-first and avoid unrelated debt.

## Scope

### In Scope
- Add shared typed sorting/search for relevant Desktop `QTableWidget` tables.
- Add report/audit filters for plate, min/max time range, and user where source data supports it.
- Enrich Desktop Reports with accounting categories, gross/net totals, expenses, and row metadata.
- Split work under the 400-line policy where practical.

### Out of Scope
- Mobile, installer, and API changes unless specs/design prove a required contract gap.
- Database migrations unless evidence shows missing schema/index support.
- Fixing unrelated UI bugs or historical report debt found during implementation.

## Capabilities

### New Capabilities
- `desktop-table-controls`: Shared sorting/search with typed values and protected rows.
- `desktop-report-accounting`: Report totals, audit filters, and cash-register row metadata.

### Modified Capabilities
- None.

## Approach

Create a small utility for normalized search and typed sort roles, then apply it to key views. Extend Reports controller/UI with date/time/user/plate filters and dashboard-aligned totals, using the API contract only as reference.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `utils/table_filters.py` | Modified | Shared search/sort helpers. |
| `views/registro.py`, `views/asistencias.py`, `views/gastos.py`, `views/mensuales.py`, `views/usuarios.py` | Modified | Adopt relevant table controls. |
| `views/reportes.py` | Modified | Add filters, accounting cards, metadata columns, sortable table. |
| `controllers/reportes_controller.py` | Modified | Return filtered rows and structured totals. |
| `controllers/accounting_contracts.py` | Modified | Align Desktop totals for bathrooms, expenses, gross, and net. |
| Report/table tests | Modified | Cover sort, filter, and totals behavior. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Formatted strings sort incorrectly. | Med | Store typed sort values outside display text. |
| Summary/action rows move. | Med | Exclude or rebuild protected rows. |
| User filtering omits categories. | Med | Specify category-by-category user semantics first. |
| Scope exceeds review budget. | High | Slice foundation and reports enrichment separately. |

## Rollback Plan

Revert implementation slices. With no migrations or cross-repo contracts, rollback restores previous Desktop table behavior and Reports output without data changes.

## Dependencies

- Existing Desktop plate, timestamp, user, and accounting columns.
- OpenSpec strict TDD: add/update tests before implementation.

## Success Criteria

- [ ] Relevant Desktop tables sort correctly by text, numbers, currency, dates/times, and IDs.
- [ ] Search/filter behavior supports requested plate, time range, and user cases where data exists.
- [ ] Reports show dashboard-like accounting totals including gross, expenses, and net.
- [ ] No Mobile/API/installer/database change is introduced without explicit spec/design justification.
