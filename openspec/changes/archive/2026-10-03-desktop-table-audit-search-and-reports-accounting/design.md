# Design: Desktop Table Audit Search and Reports Accounting

## Technical Approach

Keep the change Desktop-first. Extend the existing `utils/table_filters.py` into the shared table-control utility for normalized search plus typed `QTableWidgetItem` sort values stored in `Qt.UserRole`. Apply it only to relevant `QTableWidget` screens already named by the specs. Reports will return a structured Desktop report payload with rows, category metadata, user metadata where available, and dashboard-like totals aligned with the existing accounting contract. API code is reference evidence only; no API, Mobile, installer, or DB migration is required.

## Architecture Decisions

| Decision | Choice | Alternatives considered | Rationale |
|---|---|---|---|
| Sort/search home | Extend `utils/table_filters.py` | Per-view helpers or new dependency/model layer | Existing views already import it; a small helper avoids rewriting `QTableWidget` screens. |
| Sort values | Store semantic values in item data (`Qt.UserRole`) and use a small sortable item subclass/helper | Parse display text during compare | Display text contains `$`, `min`, dates, labels, and accents; typed roles preserve formatting and deterministic sorting. |
| Protected rows/actions | Disable sorting during refresh, set roles on data rows, then enable sorting; keep total rows outside sortable data by rebuilding/appending after row load or leaving them out of sortable tables | Let Qt sort all rows | `registro.py` and `reportes.py` synthetic total rows must not move; action widgets in `gastos`, `mensuales`, and `usuarios` must stay attached to records. |
| Reports shape | Return `{items, totals}` from `controllers/reportes_controller.obtener_reportes()` while keeping PDF/export callers adapted | Keep a raw list only | UI needs category/user/totals without recalculating; tests can validate controller semantics directly. |
| Reports user filter UI | Use a dropdown sourced from existing users | Free-text user search | Dropdown filtering is less ambiguous for audits and matches the user's explicit decision. |
| Cross-repo impact | No API/DB change | Align API repository in same change | `schema.sql` already has date/user fields; API already has richer report totals and can remain untouched for Desktop scope. |

## Data Flow

    ReportesWindow filters
      └─ fecha/date + optional time range + plate + user
          └─ controllers.reportes_controller.obtener_reportes(...)
              ├─ category queries from existing Desktop DB tables
              ├─ normalized report rows with category/user metadata
              └─ accounting_contracts.build_report_totals(...)
          └─ ReportesWindow cards + typed sortable table + PDF export

Other table views populate rows as today, but create items through shared helpers so search and sorting use semantic values without changing controller behavior.

## File Changes

| File | Action | Description |
|---|---|---|
| `utils/table_filters.py` | Modify | Add typed item/sort helpers, row protection options, and keep normalized search backward compatible. |
| `views/registro.py` | Modify | Apply typed sorting to active vehicles; protect appended total row and preserve current refresh behavior. |
| `views/asistencias.py` | Modify | Apply typed sorting to user/time/count/amount columns; existing controller filters remain. |
| `views/gastos.py` | Modify | Apply typed sorting/search excluding action column when present. |
| `views/mensuales.py` | Modify | Apply typed sorting/search for ID, plate, tariff, due day, payment date; keep actions unsorted. |
| `views/usuarios.py` | Modify | Apply text sorting/search for user/role; keep actions unsorted. |
| `views/reportes.py` | Modify | Add time/user filters, category/user columns, richer cards, typed sortable report table, and updated export call. |
| `controllers/reportes_controller.py` | Modify | Add optional time/user filters, category serializers, structured totals, and user semantics. |
| `controllers/accounting_contracts.py` | Modify | Make Desktop `build_report_totals()` include bathrooms, expenses, gross, net, and full movement count. |
| `tests/test_table_filters.py` | Modify | Cover typed money/number/date/text sort, hidden rows, protected rows, and action-safe rows. |
| `tests/test_reportes_controller.py` | Modify | Cover filters, row metadata, totals, and no-result payload. |
| `tests/test_accounting_report_contracts.py` | Modify | Cover Desktop report totals parity with dashboard/API semantics. |

## Interfaces / Contracts

`obtener_reportes(fecha_inicio, fecha_fin, patente="", hora_inicio=None, hora_fin=None, usuario="")` returns:

```python
{
    "items": [{"tipo": "vehiculo|bano|lavado_solo|mensualidad|noche|gasto", "categoria": str,
               "patente": str, "fecha_hora_ingreso": datetime, "fecha_hora_salida": datetime,
               "minutos": int, "tarifa_aplicada": int, "usuario": str | None}],
    "totals": {"total_recaudado": int, "total_banos_monto": int,
               "total_lavados_solos_monto": int, "total_mensualidades_monto": int,
               "total_noches_monto": int, "total_gastos": int,
               "total_general": int, "total_neto": int, "total_movimientos": int},
}
```

Filter semantics: plate applies only to plate-bearing categories (`vehiculo`, `lavado_solo`, `mensualidad`, `noche`); bathroom and expense rows are excluded when a plate is provided. Time bounds apply to each category's effective event time: vehicle exit, bathroom use, solo-wash finish, monthly payment time, night payment time, and expense time. User filter is selected from an existing-users dropdown and applies where schema exposes user/operator: `ingresos.usuario`, `usos_bano.usuario`, `operaciones_servicio.usuario_fin`, `pagos_mensuales.usuario`, `cobros_noches.usuario`, `gastos_operacion.usuario`; rows without meaningful user metadata are excluded when user is specified.

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit | Table helpers sort semantic values and preserve protected/action rows | PySide offscreen `QTableWidget` tests in `tests/test_table_filters.py`. |
| Unit | Report accounting totals and row metadata | Mock cursor tests in `tests/test_reportes_controller.py` and pure contract tests. |
| Integration/E2E | Not planned | Existing project has no Desktop integration/E2E runner; run `python -m unittest discover -s tests`. |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration / Rollout

No migration required. Existing schema already contains the needed date/user/accounting columns and indexes are acceptable for this Desktop-first scope. Rollout should be split into two reviewable slices: table-control foundation first, then Reports accounting enrichment.

## Open Questions

None.
