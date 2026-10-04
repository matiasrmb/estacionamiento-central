## Exploration: desktop-table-audit-search-and-reports-accounting

### Current State
Desktop tables are implemented directly in PySide6 views with `QTableWidget`; no table sorting helper is enabled today. A shared text-only filter exists in `utils/table_filters.py`, but each view wires filters and data loading separately. Reports already aggregate vehicles, bathrooms, solo washes, expenses, monthly payments, and night charges, but the Desktop report UI only shows movement count and net total, and Desktop report totals are less complete than the API report contract.

Evidence inspected:
- `views/registro.py` — active vehicles table and main cash summary cards.
- `views/reportes.py` — report filters, summary cards, table, and PDF trigger.
- `controllers/reportes_controller.py` — Desktop report queries and PDF totals.
- `controllers/dashboard_controller.py` — dashboard uses cashbox summary from registration controller.
- `controllers/registro_controller.py` — `obtener_resumen_caja_actual()` cash-register source.
- `controllers/accounting_contracts.py` — Desktop accounting summary/report helpers.
- `utils/table_filters.py` and `tests/test_table_filters.py` — shared text search behavior.
- `views/asistencias.py`, `views/gastos.py`, `views/mensuales.py`, `views/usuarios.py`, `views/tarifas_personalizadas.py`, `views/admin_edicion.py`, `views/configuracion.py` — relevant table implementations.
- `schema.sql` — existing time/user/accounting columns.
- `tests/test_reportes_controller.py`, `tests/test_accounting_report_contracts.py` — current accounting/report coverage.
- `estacionamiento-central-api/app/repositories/reportes_repo.py` and `app/repositories/accounting_contracts.py` — API report shape for comparison.

Evidence-separated findings:
- Hecho: `QTableWidget` instances are created independently in the views; no `setSortingEnabled(True)` or shared sort helper appears in Desktop views.
- Hecho: `utils.table_filters.filtrar_filas_tabla()` only performs normalized text matching against visible table cells.
- Hecho: Existing table search is duplicated in several views (`gastos`, `mensuales`, `usuarios`, `tarifas_personalizadas`, `admin_edicion`, `configuracion`) and absent in `registro` active table and `reportes` beyond controller-side date/patente filters.
- Hecho: `views/asistencias.py` already supports user and date range filtering; `controllers/asistencias_controller.py` filters by `usuario` and `hora_inicio BETWEEN start/end`.
- Hecho: `views/reportes.py` filters by date and plate only, then displays columns `Patente`, `Ingreso`, `Salida`, `Minutos`, `Monto` plus cards for movement count and net total.
- Hecho: `controllers.reportes_controller.obtener_reportes()` includes multiple accounting categories, but the item dictionaries do not consistently include `usuario`, category labels, or a full totals dictionary.
- Hecho: `controllers.dashboard_controller.obtener_resumen_diario()` reuses `registro_controller.obtener_resumen_caja_actual()` for cashbox figures, including bathrooms, solo washes, monthly payments, night charges, expenses, gross, and net.
- Hecho: Desktop `controllers.accounting_contracts.build_report_totals()` lacks bathrooms, expenses, and net fields that already exist in the API `build_report_totals()`.
- Inferencia: Sorting should be centralized in a Desktop utility because tables are mostly `QTableWidget` with common numeric, money, date/time, and text columns.
- Inferencia: Report accounting should align Desktop with the API report/cashbox contract to avoid semantic drift.
- Inferencia: Most requested table improvements are Desktop-only because the local schema already contains user/time columns and current Desktop controllers query MySQL directly.
- Hipótesis: If reports must expose operator/user filtering for every accounting line, some Desktop report queries need to return operator columns from `ingresos.usuario`, `usos_bano.usuario`, `operaciones_servicio.usuario_fin`, `pagos_mensuales.usuario`, `cobros_noches.usuario`, and `gastos_operacion.usuario`.

### Affected Areas
- `utils/table_filters.py` — extend from text-only filtering into shared table search/sort helpers.
- `tests/test_table_filters.py` — add coverage for numeric, currency, date/time, total-row, and hidden-row behavior.
- `views/reportes.py` — add time range/user filters, richer accounting summary cards, sortable typed table columns, and likely a type/user column.
- `controllers/reportes_controller.py` — add user/time filtering, return structured totals, normalize item metadata, and align with cashbox/report accounting semantics.
- `controllers/accounting_contracts.py` — bring Desktop report totals in line with API totals for bathrooms, expenses, and net cash.
- `tests/test_reportes_controller.py` and `tests/test_accounting_report_contracts.py` — cover the report query contract and total semantics.
- `views/registro.py` — active vehicles table currently disables sorting during refresh and contains a synthetic total row that must not be sorted as data.
- `views/asistencias.py` — already has user/date filtering; candidate for shared sortable table behavior and possibly finer time range if required.
- `views/gastos.py`, `views/mensuales.py`, `views/usuarios.py`, `views/tarifas_personalizadas.py`, `views/admin_edicion.py`, `views/configuracion.py` — duplicated table/search setup that can adopt shared sorting with low controller impact.
- `schema.sql` — likely no schema change required for initial Desktop scope; existing columns cover the discovered filters.
- `estacionamiento-central-api/app/repositories/reportes_repo.py` — useful compatibility reference; only affected if cross-client report parity is required by product scope.

### Approaches
1. **Central Desktop table behavior utility** — Add reusable helpers/items for enabling typed sorting and normalized search on existing `QTableWidget` views.
   - Pros: Reduces duplication, consistent sorting semantics, low risk for most tables.
   - Cons: Needs careful handling for action-widget columns, hidden rows, and summary/total rows.
   - Effort: Medium

2. **Reports-first accounting enhancement** — Keep generic table sorting small, then expand Reports controller/UI to expose dashboard-like cash-register categories and audit filters.
   - Pros: Directly addresses the highest-value accounting request and can reuse existing dashboard/report contracts.
   - Cons: Leaves some non-report table search differences for a later slice.
   - Effort: Medium

3. **Full cross-repo report parity** — Align Desktop and API report outputs/contracts before changing the UI.
   - Pros: Strongest long-term consistency for Desktop/API/Mobile.
   - Cons: Broader than the requested Desktop target; likely exceeds a 400-line review budget.
   - Effort: High

### Recommendation
Split the request. First deliver a Desktop-only foundation slice for typed table sorting/search helpers plus adoption in the main relevant views. Then deliver a Reports accounting/audit slice that aligns Desktop report totals with dashboard cashbox semantics and the existing API report contract. Treat API changes as out of scope unless proposal/spec discovers a required cross-client contract change.

Suggested scope boundaries:
- Include Desktop `QTableWidget` sorting for user-facing operational/admin tables.
- Include search by normalized text where a table already has or clearly needs search.
- Include Reports date + optional time range + user filter, with accounting summary cards matching dashboard/cashbox categories.
- Exclude database migrations unless a missing index becomes a measured performance problem.
- Exclude Mobile and Installer changes for the initial Desktop slices.

Detected debt:
- Table setup is duplicated across views.
- Search is centralized only for simple cell text, not typed values or server-side filters.
- Desktop and API accounting report contracts have drifted; the API helper already has richer report totals than Desktop.
- Report row dictionaries use display fields such as `[BAÑO]`, `[GASTO]`, `[MENSUAL]` instead of a complete typed row model.
- Several tables contain action widgets or synthetic total rows, which need explicit sorting exclusions.

### Risks
- Enabling default `QTableWidget` sorting on formatted strings will mis-sort money, minutes, dates, and IDs unless typed sort roles/items are used.
- Sorting while tables are being refreshed can reorder rows unexpectedly or move synthetic total rows.
- Report user filtering can silently omit categories if each source table's user semantics are not defined.
- Expanding Reports and all table behavior together is probably too broad for the 400-line review policy.
- The stale memory about low-end hardware should be revalidated before choosing live/server-side filtering thresholds.

### Ready for Proposal
Yes — tell the user the request is valuable but too broad for one safe implementation pass. Recommend splitting into at least two Desktop-first SDD changes/slices: table sorting/search foundation, then Reports accounting/audit enhancement. API/DB work should remain conditional, not assumed.
