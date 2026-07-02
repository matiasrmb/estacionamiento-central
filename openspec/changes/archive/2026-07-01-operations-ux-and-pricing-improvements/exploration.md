# Exploration: operations-ux-and-pricing-improvements

## Executive summary

This change is feasible, but it is not one feature. It should be decomposed into reviewable slices across Desktop, API, Mobile, and DB: quoting, wash-only operations, configurable vehicle/wash types, safe user deletion, unified mobile daily operation, and printer support hardening. The safest path is additive: preserve current ingreso/salida and parking-linked lavado behavior, add explicit service records and APIs where the current schema forces lavados to belong to an ingreso.

## Current-state map

### Desktop / DB

| Area | Current behavior | Key files |
| --- | --- | --- |
| Parking ingreso/salida | `ingresos` stores active stays (`fecha_hora_salida IS NULL`), payment amount in `tarifa_aplicada`, and close state in `cerrado`. Desktop creates ingreso, blocks duplicate active plates, calculates salida, prints ticket. | `schema.sql`, `controllers/registro_controller.py`, `views/registro.py`, `utils/ticket.py` |
| Active list / daily operation | Desktop `RegistroWindow` is already a keyboard/mouse daily-operation hub with plate search, ingreso, salida, espera, baño, lavado, shortcuts, active table, and current-turn totals. | `views/registro.py`, `controllers/registro_controller.py` |
| Lavados | Lavados require an active `id_ingreso`; `ingresos.en_lavado` pauses parking charge and salida is blocked while wash is active. Wash amount is charged later with parking salida. | `controllers/lavados_controller.py`, `controllers/registro_controller.py`, `views/registro.py` |
| Daily close / caja | Cierre sums closed `ingresos.tarifa_aplicada` where `cerrado = FALSE`, plus `usos_bano` in the close range. It then marks ingresos closed. There is no independent wash-only close path. | `controllers/cierres_controller.py`, `schema.sql` |
| Tarifas / wash values | Parking tariffs live in `configuracion` and `tarifas_personalizadas`; wash categories are hard-coded constants backed by config keys. | `controllers/config_controller.py`, `controllers/tarifas_controller.py`, `views/configuracion.py` |
| Mensuales | Mensual customers are `vehiculos.tipo_cliente='mensual'`, `activo`, and optional `tarifa_mensual`. Deleting a mensual deactivates the vehicle record. | `controllers/mensuales_controller.py`, `schema.sql` |
| Users | Users can be created, password-changed, and activated/deactivated. No delete function exists. Historic rows reference usernames as text, not FK IDs. | `controllers/usuarios_controller.py`, `views/usuarios.py`, `schema.sql` |
| Printing | Desktop renders 58mm PDF tickets via FPDF and prints through SumatraPDF to a selected Windows printer. Config UI already has printer selection and test print. | `utils/ticket.py`, `utils/printer_manager.py`, `views/configuracion.py` |

### API

| Area | Current behavior | Key files |
| --- | --- | --- |
| Ingresos / activos | API creates ingreses, creates PC print jobs, lists active records ordered oldest-first. | `app/api/v1/endpoints/ingresos.py`, `app/api/v1/endpoints/activos.py`, `app/repositories/ingresos_repo.py` |
| Salidas | API has preview/confirm. It subtracts wash minutes, adds wash totals, blocks salida while `en_lavado=1`, and creates PC/Sunmi print jobs. | `app/api/v1/endpoints/salidas.py`, `app/schemas/salidas.py` |
| Lavados / baño | API exposes `/lavados/categorias`, `/lavados/iniciar`, `/lavados/finalizar`, `/banos`. Washes require `id_ingreso`. | `app/api/v1/endpoints/operaciones.py`, `app/repositories/operaciones_repo.py` |
| Tarifas / mensuales / usuarios | Tarifa intervals support CRUD; mensuales support upsert/tarifa/deactivate; users support list/create/password/status only. | `app/api/v1/endpoints/tarifas.py`, `mensuales.py`, `usuarios.py` |
| Cierres / reports | Cierres summarize non-closed salida rows plus baños; reports expose movement queries. | `app/repositories/cierres_repo.py`, `app/api/v1/endpoints/reportes.py` |
| Print agent | Agent polls `print_jobs`, renders ReportLab PDFs, and prints via Sumatra. It requires `SUMATRA_PATH` and `PRINTER_NAME`; non-Sumatra engine is rejected. | `printer_agent/agent.py`, `printer_agent/pdf_renderer.py`, `printer_agent/pdf_printer.py` |

### Mobile

| Area | Current behavior | Key files |
| --- | --- | --- |
| Home operation | Daily operation is split into `Ingreso`, `Activos / Salida`, and `Lavados / Baño`. | `lib/features/home/presentation/home_screen.dart` |
| Ingreso | Dedicated plate form creates ingreso and optionally prints on Sunmi. | `lib/features/ingreso/presentation/ingreso_screen.dart` |
| Salida | Dedicated active list selects an active ingreso, previews salida, confirms, and optionally prints on Sunmi. It blocks salida when record is in wash. | `lib/features/salida/presentation/activos_salida_screen.dart` |
| Lavados / baño | Separate module lists active parking records only, starts/finalizes wash by `id_ingreso`, and registers bathroom. No wash-only plate search exists. | `lib/features/operaciones/presentation/operaciones_screen.dart`, `data/operaciones_api.dart` |
| Admin config | Mobile config edits fixed config keys, including hard-coded wash keys. | `lib/features/admin/configuracion/presentation/configuracion_admin_screen.dart` |

## Confirmed business rules

- Quote/cotización must support stay, washes, monthly, and combinations.
- Monthly quote must calculate per-day cost per vehicle and support multiple small/large vehicles.
- Existing parking ingreso → start/finalize washing flow must remain.
- New wash-only flow must accept a plate without an active parking stay.
- Wash-only must impact daily close/caja like parking exits.
- Wash-only must track wash start/end duration.
- At wash completion, operator chooses: charge wash and vehicle leaves, or convert to parking/stay.
- If converted to parking, stay starts at wash end, not wash start.
- Tickets for wash + later stay must show wash detail, stay detail, and total.
- Config must allow adding/removing vehicle types and values; historic use must be protected.
- Users module must keep deactivate and add deletion semantics.
- Mobile must keep `Lavados / Baño`, add a unified daily-operation search, add bathroom there, show newest-first records, and add plate search to Lavados.
- Printer strategy must document supported drivers/config, test print, diagnostics, and fallback guidance.

## Open questions

- What are the monthly quote formulas for “small” and “large” vehicles if no monthly tariff is configured? Use fixed defaults, admin-configured type prices, or existing `vehiculos.tarifa_mensual` only?
- Should wash-only records count as `total_ingresos/total_salidas`, a separate `total_lavados_solos`, or only monetary totals in cierre PDFs/reports?
- Should quote output be printable, saved historically, or only calculated on screen?
- Should physical user deletion be allowed for the currently logged-in admin or the last remaining admin? Recommended answer: no.

## Candidate approach: additive service operations

### Data model

Minimal intervention should avoid overloading `ingresos` for wash-only because `lavados.id_ingreso` is currently `NOT NULL` and parking close semantics are tied to salida.

Add explicit service/type tables and compatibility columns:

- `tipos_vehiculo(id_tipo_vehiculo, codigo, nombre, categoria_tamano, valor_mensual_default, activo, created_at, updated_at)`.
- `tipos_lavado(id_tipo_lavado, codigo, nombre, valor, activo, created_at, updated_at)` or a generic `servicios_configurados` if broader services are expected.
- Add nullable `id_tipo_lavado` to `lavados`, keeping `categoria_lavado` and `valor_lavado` as historical snapshot fields.
- Add nullable `id_ingreso` support to `lavados` only if introducing wash-only in same table; otherwise add `operaciones_servicio`.
- Recommended: add `operaciones_servicio(id_operacion, tipo='LAVADO_SOLO', patente, id_vehiculo, id_tipo_lavado, categoria_snapshot, valor_snapshot, fecha_hora_inicio, fecha_hora_fin, estado, destino_post_lavado, id_ingreso_generado, usuario_inicio, usuario_fin, cerrado)`.
- Extend `cierres_diarios` with service totals or compute them from `operaciones_servicio` and include them in generated PDF/API response.

Deletion policy:

- Vehicle/wash types: deactivate if referenced by historical lavados, operations, monthly quotes, or vehicles; physical delete only if never referenced.
- Users: keep deactivate as default. Add delete-only-if-no-activity, checking text username references in `ingresos.usuario`, `lavados.usuario_inicio/fin`, `usos_bano.usuario`, `cierres_diarios.usuario`, `asistencias.usuario`, and API-created records. If any activity exists, block physical delete and offer deactivate.

### API

Add endpoints rather than changing existing request shapes:

- `POST /cotizaciones` or `POST /cotizaciones/preview` for stateless quote calculations.
- `GET/POST/PUT/DELETE /tipos-vehiculo` and `/tipos-lavado` with deactivate-or-delete behavior.
- `POST /lavados/solo/iniciar` by plate and wash type.
- `POST /lavados/solo/finalizar` with `accion = COBRAR_Y_SALIR | PASAR_A_ESTADIA`.
- `GET /operacion-diaria/registros?search=&limit=` returning active stays, recent exits, wash-only operations, and baños newest-first for mobile unified operation.
- `POST /operacion-diaria/patente` for mobile single-search command: if no active ingreso, create ingreso; if active, return salida preview or confirm depending UX decision.
- `GET /impresion/diagnostico` and/or print-agent self-check output for printer name, Sumatra path, queue visibility, last job error.

Compatibility rule: existing `/ingresos`, `/activos`, `/salidas/*`, `/lavados/iniciar`, `/lavados/finalizar`, `/banos` must keep current contracts for Desktop and Mobile until replacements are adopted.

### Desktop UI

- Add `Cotización` button/module near daily operation or admin/config depending expected operator role.
- Keep Registro as the primary desktop operation hub; add wash-only action from plate search when no active ingreso exists.
- On wash-only finalization, present the confirmed two-action decision. If converted to parking, create an ingreso at `fecha_hora_fin`.
- Update tickets to render detailed wash + stay sections when both exist.
- Extend configuration screen with CRUD lists for vehicle types and wash types; keep existing config keys as migration/default seed.
- Add user delete action alongside deactivate with guardrails and clear blocked-delete reason.

### Mobile UI

- Add a new unified daily operation screen rather than removing existing modules.
- Home can route primary daily use to the unified screen, while keeping `Lavados / Baño` as a secondary module.
- Unified screen: plate search, if inactive then ingreso, if active then salida path; visible newest-first record list; tap opens bottom sheet with salida, wash, mensual, bathroom-related actions as applicable.
- Add bathroom button to unified screen.
- Add plate search to existing Lavados / Baño so operators can start wash-only or locate active wash records.

### Printing support

- Supported strategy should be explicit: SumatraPDF + vendor-specific or validated thermal driver + configured printer name is the supported path.
- Generic printer drivers should be documented as unsupported/unreliable unless validated on the target hardware.
- Desktop already has printer selection and test print; API print agent already requires `SUMATRA_PATH` and `PRINTER_NAME`. Next phase should align diagnostics and setup instructions across both.
- Add fallback guidance: save PDF, reprint last ticket/job, manual Windows test page, and visible last print error before marking work as complete.

## Recommended decomposition into slices

1. **Quote/cotización preview** — stateless calculations and UI only; no DB persistence unless explicitly required.
2. **Configurable types foundation** — vehicle/wash type tables, migration seed from existing config keys, deactivate-or-delete policy.
3. **Wash-only backend** — DB + API + cierre/report/ticket payload support, preserving current parking-linked lavados.
4. **Desktop wash-only and quote UX** — operator-facing actions and detailed tickets.
5. **Mobile unified daily operation** — additive new screen/API integration; keep existing modules.
6. **User safe deletion** — Desktop/API/Mobile admin actions with activity checks.
7. **Printer diagnostics/support hardening** — diagnostics endpoint/UI/docs and supported driver guidance.

Given `review_budget_lines=400` and `chained_pr_strategy=ask-always`, these should become separate capabilities/slices in proposal/tasks; implementing all in one PR would be too large.

## Risks and dependencies

- Wash-only impacts accounting: cierre/report semantics must be defined before implementation.
- Current wash schema requires `id_ingreso NOT NULL`; forcing wash-only through fake ingresos would pollute parking metrics.
- Existing ticket format is duplicated between Desktop FPDF and API ReportLab/Sunmi payloads; detail changes must stay contract-compatible.
- Hard-coded wash categories exist in Desktop, API, and Mobile config; migration to dynamic types requires careful compatibility seeding.
- Historic user references are plain text, so safe delete checks must query several tables and cannot rely on FK constraints.
- Printer reliability depends on Windows driver/spooler/Sumatra configuration outside app code; diagnostics can reduce support load but cannot guarantee generic driver stability.

## Non-goals for this change

- Do not remove current Desktop ingreso/salida flow.
- Do not remove current parking-linked lavado behavior.
- Do not remove Mobile `Lavados / Baño`.
- Do not change existing API contracts used by current mobile screens unless versioned or backward-compatible.
- Do not physically delete historically referenced users or vehicle/wash types.
- Do not promise support for unvalidated generic thermal drivers.

## Compatibility rules

- Existing active parking records must continue to calculate parking minus wash minutes plus wash amount.
- Wash-only conversion to parking must start `ingresos.fecha_hora_ingreso` at wash end.
- Historical tickets/reports must remain readable after type names/prices change by storing snapshot labels and values on operation rows.
- Cierre must not miss wash-only revenue; pending wash-only operations should remain visible until finalized/closed.
- Existing test commands remain the verification baseline: Desktop/API `python -m unittest discover -s tests`, Mobile `flutter test` plus `flutter analyze` for mobile slices.

## Recommendation for next phase

Proceed to `sdd-propose`, but frame this as an umbrella change with explicit capability slices and a likely chained PR plan. The proposal should first lock the accounting model for wash-only close totals and monthly quote formula defaults, then specify additive API/data contracts before UI work.
