## Exploration: complete-operations-pricing-gaps

### Current State
- **Solo lavados** are implemented as independent service operations in Desktop and API via `operaciones_servicio` with states `ACTIVO`, `FINALIZADO_COBRADO`, and `CONVERTIDO_ESTADIA`. Desktop can start/finalize them from the registration UI; API exposes `/lavados/solo`; Mobile can start, charge, convert, and list them in the Lavados/Baño module. Converted solo lavados are included once at final parking exit in Desktop/API salida flows.
- **Solo lavado accounting is only partially complete.** API cierres/reportes already query `operaciones_servicio` charged rows and have migration `003_solo_lavado_accounting.sql`. Desktop has reusable accounting helpers/tests, but `controllers/cierres_controller.py` and `controllers/reportes_controller.py` still only aggregate `ingresos`, `usos_bano`, and parking-linked `lavados`, not `operaciones_servicio`. Desktop `schema.sql` and Installer bundled `schema.sql` also lack `operaciones_servicio.cerrado` and cierre aggregate columns.
- **Cotizaciones** exist as preview-only logic in Desktop and API for estadía, lavado, mensualidad, and combinations. Desktop UI exposes separate single-service quote dialogs. API exposes `/cotizaciones/preview`. Mobile only exposes lavado quote from `OperacionesScreen`; no persistent quote/contract table/entity was found in SQL schemas or app code.
- **Mensualidad admin** exists in Desktop/API/Mobile (`vehiculos.tipo_cliente='mensual'`, `activo`, `tarifa_mensual`), but operational ingreso/salida billing does not use monthly status. Salida calculation in Desktop/API uses generic parking tariff logic regardless of `tipo_cliente`/`activo`.

### Affected Areas
- `C:\Users\matia\estacionamiento-central\controllers\cierres_controller.py` — Desktop daily closure ignores charged solo lavados and cannot mark them closed.
- `C:\Users\matia\estacionamiento-central\controllers\reportes_controller.py` — Desktop reports/PDF totals omit charged solo lavados from `operaciones_servicio`.
- `C:\Users\matia\estacionamiento-central\controllers\accounting_contracts.py` — Existing Desktop helper has the desired revenue semantics and should be reused/wired instead of duplicating rules.
- `C:\Users\matia\estacionamiento-central\schema.sql` — Desktop schema has `operaciones_servicio` but lacks `cerrado` and solo-lavado cierre total columns.
- `C:\Users\matia\estacionamiento-central-installer\app\EstacionamientoCentral\_internal\schema.sql` — Installer schema is behind Desktop/API: it lacks wash pricing tables, `operaciones_servicio`, and solo-lavado accounting columns.
- `C:\Users\matia\estacionamiento-central-api\app\repositories\cierres_repo.py` — API already implements pending/close semantics for charged solo lavados.
- `C:\Users\matia\estacionamiento-central-api\app\repositories\reportes_repo.py` — API already includes charged solo lavados in unfiltered reports.
- `C:\Users\matia\estacionamiento-central-api\app\db\migrations\003_solo_lavado_accounting.sql` — API migration documents required DB additions for API-side accounting.
- `C:\Users\matia\estacionamiento-central\controllers\cotizaciones_controller.py` and `C:\Users\matia\estacionamiento-central-api\app\services\cotizaciones.py` — Preview-only quote services; no persistence.
- `C:\Users\matia\estacionamiento_central_mobile\lib\features\operaciones\data\operaciones_api.dart` and `...\presentation\operaciones_screen.dart` — Mobile only quotes lavado, not estadía/mensual/combinations.
- `C:\Users\matia\estacionamiento-central\controllers\registro_controller.py` and `C:\Users\matia\estacionamiento-central-api\app\api\v1\endpoints\salidas.py` — Salida billing ignores monthly customer status.

### Approaches
1. **Narrow repair: wire charged solo lavado accounting in Desktop + schema parity** — Update Desktop cierre/reporte queries to use existing accounting semantics; add/ensure schema columns/tables needed for cierre marking; keep API behavior unchanged except tests if needed.
   - Pros: Directly repairs the clearest revenue gap; small, testable, reviewable under 400 lines if split carefully.
   - Cons: Installer schema parity may push scope; existing installed DBs need safe additive migration/ensure logic.
   - Effort: Medium

2. **Quote expansion/persistence** — Add persistent quote/contract entity and full mobile quote UI.
   - Pros: Solves the larger cotización product gap.
   - Cons: New domain model, DB schema, API contracts, mobile UI, lifecycle/expiry questions; likely exceeds 400-line review budget and needs user decisions.
   - Effort: High

3. **Monthly operational billing automation** — Make salida/preview detect active monthly customers and apply a defined billing rule.
   - Pros: Connects admin mensualidad to operations.
   - Cons: Business rule is not defined in code/spec: free exits, recurring invoice, daily allocation, or warning-only are materially different. Dangerous without explicit confirmation.
   - Effort: Medium/High

### Recommendation
Scope this repair change to **solo lavado accounting parity and schema safety**: Desktop cierres/reportes must include only `FINALIZADO_COBRADO` solo lavados, converted solo lavados must remain deferred until parking exit, and charged solo lavados should not be counted twice after closure. Treat API behavior as the reference because it already implements these semantics. Keep quote persistence/full mobile quote and monthly billing automation out of scope unless the user explicitly confirms business rules.

Safe implementation under the 400-line review budget:
- Prefer small pure helpers or reuse `controllers.accounting_contracts` for totals.
- Add focused Desktop unittest coverage before changing controllers.
- Make schema changes additive/idempotent (`ADD COLUMN IF NOT EXISTS` or startup schema ensure pattern if available).
- If Installer schema parity is required, do it as a separate slice because it has no automated runner.

### Tests that would prove the repair
- Desktop unit: cierre pending/creation includes one `FINALIZADO_COBRADO` solo lavado in `total_lavados_solos_monto` and `total_general`.
- Desktop unit: cierre excludes `ACTIVO` and `CONVERTIDO_ESTADIA` solo lavados.
- Desktop unit: cierre marks charged solo lavados as `cerrado=TRUE` and later pending closure does not count them again.
- Desktop unit: report totals/items include charged solo lavados when no plate filter is applied.
- Desktop unit: report totals exclude converted solo lavados because their amount is charged at parking salida.
- API regression: existing `test_solo_lavado_accounting_semantics.py`, `test_accounting_report_contracts.py`, and cierre/report tests remain green.
- Mobile regression: existing solo lavado flow tests remain green; no mobile change is required for the narrow repair.
- Installer manual verification if schema is touched: fresh install schema contains `operaciones_servicio`, `cerrado`, and solo-lavado cierre columns.

### Out of Scope Unless Confirmed
- Creating persistent cotización/contract records, quote lifecycle, numbering, expiry, conversion to operation, or quote PDFs.
- Full mobile cotización support for estadía/mensualidad/combinations.
- Changing monthly customer operational billing behavior, because the billing rule is undefined.
- Reworking mobile unified daily-operation screen to offer solo lavado from search; solo lavado is already reachable in Lavados/Baño.
- Broad report redesign or historical data backfill beyond additive accounting columns.

### Risks
- Desktop `schema.sql` and Installer bundled schema are behind API migrations; runtime code may fail if `cerrado`/aggregate columns are queried before existing databases are migrated.
- Desktop reports currently present lavados as already included in vehicle totals; solo lavados charged immediately break that assumption and need explicit labeling.
- Monthly billing is a business-policy risk, not just a technical gap.
- Installer has no automated tests, so schema parity should be manually verified or isolated.

### Ready for Proposal
Yes — propose a narrow repair for solo lavado accounting/schema parity. Ask the user separately before expanding into persistent cotizaciones or monthly billing automation.
