# Research: Desktop Reporting Dashboard API Validation

## Research Lane

Repository-backed contract validation for Desktop reporting dashboard against the merged API reporting contracts.

## Evidence Summary

### Endpoint paths and request shape

- Desktop `utils/api_client.py` calls:
  - `GET /reporting/metric-catalog`
  - `GET /reporting/dashboard?period_id=current&state=open`
- API `app/api/v1/endpoints/reporting.py` exposes:
  - `GET /reporting/metric-catalog`
  - `GET /reporting/dashboard`
- API dashboard currently declares only the explicit unsupported-filter test hook; it does not model `period_id` or `state` as accepted dashboard query parameters.

Conclusion: endpoint paths match, but Desktop sends dashboard query parameters that the API ignores rather than owns as contract. This is contract drift risk, not an immediate runtime break.

### Payload compatibility

- API metric catalog uses canonical metrics including:
  - `collected_sources_total`
  - `operational_expense_total`
  - `net_revenue_total`
  - `monthly_payments_collected_total`
  - `vehicle_movement_count`
- API open dashboard currently returns `period`, `catalog_version`, `filters`, `metrics`, and `pagination`.
- Desktop controller normalization preserves `period`, `filters`, `pagination`, `catalog_version`, and summary values while defaulting missing metadata such as `source_state`, `period_state`, `completeness`, `capacity`, and `warnings`.

Conclusion: current dashboard payload is compatible with Desktop normalization. Capacity remains a future risk if API starts returning canonical capacity helper keys that differ from current Desktop rendering assumptions.

### Operations pagination impact

API operations pagination added through `/reporting/reports/operations` is out of scope for the current Desktop dashboard because Desktop does not call that endpoint and does not render operation drill-down pagination UI.

### Recommended follow-up

Use a narrow validation and adapter/test-alignment change:

- Required: mocked contract tests for metric catalog and dashboard payload compatibility.
- Required: align Desktop dashboard request shape with the API-owned dashboard contract by removing misleading `period_id=current&state=open` query parameters unless API explicitly accepts them later.
- Optional: local seeded API smoke for `GET /api/v1/reporting/metric-catalog` and `GET /api/v1/reporting/dashboard` when an authenticated local API is available.
- Do not reimplement the archived Desktop dashboard.

## Out of Scope

- Desktop operations drill-down UI.
- Desktop pagination UI for `/reporting/reports/operations`.
- API endpoint changes.
- Mobile or Installer changes.
- Production data probing or remote validation.
- `printer_agent/run_agent_task.cmd` or any API printer-agent file.

## Source References

- Desktop: `utils/api_client.py`
- Desktop: `controllers/reportes_controller.py`
- Desktop: `views/reportes.py`
- Desktop tests: `tests/test_api_client_session.py`, `tests/test_reportes_controller.py`, `tests/test_reportes_view.py`
- API: `app/api/v1/endpoints/reporting.py`
- API: `app/repositories/reporting_read_models.py`
- API: `app/repositories/reporting_repo.py`
- API tests: `tests/test_reporting_endpoints.py`, `tests/test_reporting_read_models.py`
