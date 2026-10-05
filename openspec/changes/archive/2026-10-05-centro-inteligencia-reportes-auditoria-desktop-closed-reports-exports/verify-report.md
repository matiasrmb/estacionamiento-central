```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:ef20741b7022d93c32144301be7ba49ef1efeb1c9d74de6f32e195d6cd1aea04
verdict: pass_with_warnings
blockers: 0
critical_findings: 0
requirements: 1/1
scenarios: 5/5
test_command: python -m unittest tests.test_api_client_session tests.test_reportes_controller; QT_QPA_PLATFORM=offscreen python -m unittest tests.test_reportes_view; QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests
test_exit_code: 0
test_output_hash: sha256:24399d694a1ca8610cf8363dc5bc2bc2ff3b061ae7bd8c5e96d1b9f1c0e57f6e
build_command: python -m compileall -q controllers utils views tests
build_exit_code: 0
build_output_hash: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

## Verification Report

**Change**: centro-inteligencia-reportes-auditoria-desktop-closed-reports-exports
**Version**: N/A
**Mode**: Standard

### Completeness
| Metric | Value |
|--------|-------|
| Requirements total | 1 |
| Requirements compliant | 1 |
| Scenarios total | 5 |
| Scenarios compliant | 5 |
| Tasks total | 14 |
| Tasks complete | 14 |
| Tasks incomplete | 0 |

### Build & Tests Execution
**Build**: Passed
```text
Command: python -m compileall -q controllers utils views tests
Exit code: 0
Output: <empty>
Output hash: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

**Tests**: Passed
```text
Command: python -m unittest tests.test_api_client_session tests.test_reportes_controller
Exit code: 0
Result: Ran 34 tests in 0.046s, OK
Output hash: sha256:9930c29cd390019a531a57f131a7209deb61bb37e4d37545ac3d26a46e21d863

Command: QT_QPA_PLATFORM=offscreen python -m unittest tests.test_reportes_view
Exit code: 0
Result: Ran 6 tests in 0.115s, OK
Output hash: sha256:ffd55558f222330a162804d5693cb7223f604c81e2d9f7d2645029b76bb79537

Command: QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests
Exit code: 0
Result: Ran 397 tests in 4.302s, OK
Output hash: sha256:c0521fe1dd036fd85544c60aa224301597bc65db4458e9d0cdad9a36c6d35e87

Combined test output hash: sha256:24399d694a1ca8610cf8363dc5bc2bc2ff3b061ae7bd8c5e96d1b9f1c0e57f6e
```

**Coverage**: Not available; this repository uses unittest without coverage instrumentation in the verified command set.

### Spec Compliance Matrix
| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| Desktop Closed and Export Roadmap Boundaries | Closed report is retrieved from the API | `tests.test_api_client_session > test_closed_report_uses_canonical_endpoint`; `tests.test_reportes_controller > test_closed_report_normalizes_api_metadata_and_totals`; `tests.test_reportes_view > test_loads_api_closed_report_and_renders_metadata_without_local_fallback` | COMPLIANT |
| Desktop Closed and Export Roadmap Boundaries | Incomplete closed report remains usable with warnings | `tests.test_reportes_controller > test_closed_report_preserves_incomplete_state_and_warnings`; `tests.test_reportes_view > test_closed_report_warnings_and_api_errors_are_actionable` | COMPLIANT |
| Desktop Closed and Export Roadmap Boundaries | Closed report API failure is explicit | `tests.test_reportes_controller > test_closed_report_api_error_is_explicit_without_local_fallback`; `tests.test_reportes_view > test_closed_report_warnings_and_api_errors_are_actionable` | COMPLIANT |
| Desktop Closed and Export Roadmap Boundaries | PDF export request is operational | `tests.test_api_client_session > test_closed_report_pdf_export_uses_canonical_endpoint`; `tests.test_reportes_controller > test_closed_report_pdf_export_writes_returned_base64_content`; `tests.test_reportes_view > test_closed_report_pdf_and_xlsx_exports_use_api_result` | COMPLIANT |
| Desktop Closed and Export Roadmap Boundaries | XLSX export replaces CSV promise | `tests.test_api_client_session > test_closed_report_xlsx_export_uses_canonical_endpoint`; `tests.test_api_client_session > test_closed_report_export_rejects_non_pdf_xlsx_format`; `tests.test_reportes_view > test_closed_report_pdf_and_xlsx_exports_use_api_result` | COMPLIANT |

**Compliance summary**: 5/5 scenarios compliant.

### Correctness (Static Evidence)
| Requirement | Status | Notes |
|------------|--------|-------|
| Desktop Closed and Export Roadmap Boundaries | Implemented | `utils/api_client.py` adds additive closed-report and PDF/XLSX export helpers against `/reporting/reports/closed/{closure_id}` and `/reporting/exports/{closure_id}.{format}`. `controllers/reportes_controller.py` normalizes closed metadata, warnings, explicit API errors without local fallback, and export persistence under `reportes/`. `views/reportes.py` replaces future-only closed/export controls with API-backed load and PDF/XLSX actions. |
| Desktop-only boundary | Implemented | Git diff names are limited to Desktop client/controller/view/test files plus this OpenSpec change. No API, Mobile, installer, or schema/database files are modified. |
| No CSV promise for closed-report exports | Implemented | Closed-report controls are `Export closed PDF` and `Export closed XLSX`; client validation rejects non-`pdf`/`xlsx` formats. |

### Coherence (Design)
| Decision | Followed? | Notes |
|----------|-----------|-------|
| Consume existing reporting endpoints through additive `api_client` helpers | Yes | Helpers are thin wrappers over `_request` and leave open-period reporting calls unchanged. |
| Prompt for a closure/report id in the existing reports window | Yes | `ReportesWindow.cargar_reporte_cerrado` uses `QInputDialog.getText` and renders the result in the existing reports UI. |
| Persist API export content to `reportes/closed_<closure_id>.<format>` | Yes | Controller export writes normalized bytes to the `reportes` output directory and returns path/content metadata. |
| Show actionable API errors without local fallback recomputation | Yes | Closed-report API errors return `ok: False` and do not call `obtener_reportes`; the view presents warning dialogs and does not fabricate totals. |

### Issues Found
**CRITICAL**: None.

**WARNING**:
- The view-level totals rendering is covered with `total_general`, `total_gastos`, and `total_neto` shaped fixtures. The controller also preserves canonical `operation_totals` fields such as `operational_income_total`, but there is no dedicated view assertion that maps those canonical names to the closed-report cards. If the API returns only canonical operation-total keys, the cards may render zero while metadata still displays correctly.

**SUGGESTION**:
- Add a focused view assertion for canonical `operation_totals` key names in a follow-up hardening slice if the archived API contract confirms those are the only closed-report total keys.

### Verdict
PASS WITH WARNINGS
All required tasks are complete, all five spec scenarios have passing unittest coverage, final Desktop discovery passes, and the implementation remains Desktop-only. The warning is a contract-shape hardening risk rather than a verified runtime failure in the current Desktop test evidence.
