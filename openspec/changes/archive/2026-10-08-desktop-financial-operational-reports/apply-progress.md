# Apply Progress: Desktop Closed-Report Operation Drill-Down

## Mode

Strict TDD.

## Completed Tasks

- [x] 1.1 Add `tests/test_api_client_session.py` coverage for `GET /reporting/reports/operations` with `period_id=closure:42`.
- [x] 1.2 Add `tests/test_api_client_session.py` coverage that only supported operation parameters are sent.
- [x] 1.3 Add `tests/test_api_client_session.py` coverage that unsupported and blank params are omitted.
- [x] 2.1 Add controller row normalization tests for core operation fields, filters, and `source=api`.
- [x] 2.2 Add controller tests for empty/warning status while keeping closed-report data visible.
- [x] 2.3 Add controller tests for explicit API error payloads and request failures.
- [x] 2.4 Add controller tests for pagination metadata and no local fallback.
- [x] 3.1 Add view coverage for operation row rendering.
- [x] 3.2 Add view coverage for operation filters, sorting, limit/offset navigation, and pagination status.
- [x] 3.3 Add view coverage for empty, warning, and actionable error states without enabling exports.
- [x] 3.4 Add view coverage that local calendar reports remain labeled legacy/local and separate.
- [x] 4.1 Add `ALLOWED_OPERATION_PARAMS` and `obtener_operaciones_reporte()`.
- [x] 4.2 Add `obtener_operaciones_reporte_cerrado()` normalization.
- [x] 4.3 Add closed-report operation controls, table, status, and pagination wiring.
- [x] 4.4 Preserve dashboard cards, hidden exports, local calendar query behavior, and no open/current operation rows.
- [x] 5.1 Run focused unittest command and fix failures.
- [x] 5.2 Run full unittest discovery and record evidence.

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 1.1-1.3 | `tests/test_api_client_session.py` | Unit | ✅ 42/42 focused baseline | ✅ Missing `obtener_operaciones_reporte` failed | ✅ Focused suite 53/53 | ✅ Closure period, allow-list, blank omission | ✅ Ordered encoder constant |
| 2.1-2.4 | `tests/test_reportes_controller.py` | Unit | ✅ 42/42 focused baseline | ✅ Missing controller API alias failed | ✅ Focused suite 53/53 | ✅ Rows, warnings, API errors, pagination, no fallback | ✅ Extracted pure normalization helpers |
| 3.1-3.4 | `tests/test_reportes_view.py` | Unit/PySide | ✅ 42/42 focused baseline | ✅ Missing view controls/table failed | ✅ Focused suite 53/53 | ✅ Rows, controls, empty/warning/error, local boundary | ✅ Kept closed-report operations isolated from local table |
| 4.1-4.4 | Production files | Unit/PySide | ✅ 42/42 focused baseline | ✅ Tests written before production changes | ✅ Focused suite 53/53 | ✅ API/client/controller/view paths exercised | ✅ No dashboard/export reimplementation |

## Work Unit Evidence

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `python -m unittest tests.test_api_client_session tests.test_reportes_controller tests.test_reportes_view` → 53 tests, OK |
| Runtime harness command/scenario and exact result | N/A; desktop slice is covered by mocked unittest/PySide tests and has no separate runtime harness in `openspec/config.yaml` |
| Rollback boundary | Revert `utils/api_client.py`, `controllers/reportes_controller.py`, `views/reportes.py`, matching tests, `tasks.md`, and this apply progress artifact |

## Verification Evidence

- Focused command passed: `python -m unittest tests.test_api_client_session tests.test_reportes_controller tests.test_reportes_view` → 53 tests, OK.
- Full discovery command ran: `python -m unittest discover -s tests` → 410 tests, 1 failure in `test_registrar_ingreso_retorna_true_con_fecha_hora_personalizada_valida`; evidence points to a time-dependent pre-existing test using `datetime.now() - timedelta(hours=2)` across the current-day guard, unrelated to this reporting slice.

## Review Boundary

- Delivery strategy: auto-chain.
- Chain strategy: stacked-to-main.
- Current work unit: desktop-closed-report-operation-drilldown.
- Authored code/test diff: 513 changed tracked lines before this artifact; this exceeds the 450-line attempt hint, but the slice is cohesive and covered. Recommend `size:exception` if the parent keeps it as one review unit.
