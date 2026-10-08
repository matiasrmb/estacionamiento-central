# Tasks: Desktop Report Audit Visibility

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 120-220 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | auto-chain |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: stacked-to-main
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Add Desktop audit visibility test-first and implementation | PR 1 | `python -m unittest tests.test_reportes_controller tests.test_reportes_view` | N/A: unittest validates controller/view metadata without launching Desktop UI | Revert `controllers/reportes_controller.py`, `views/reportes.py`, `tests/test_reportes_controller.py`, `tests/test_reportes_view.py` |

## Phase 1: RED Controller Coverage

- [x] 1.1 Add failing `tests/test_reportes_controller.py` cases proving API-backed `audit_coverage` variants are preserved/normalized into stable available, gap, unavailable, and not-provided states without invented coverage.
- [x] 1.2 Add a failing `tests/test_reportes_controller.py` case proving local fallback remains local, non-official, and audit-empty/unavailable.
- [x] 1.3 Stop before production edits if sampled dashboard payloads are unusable for meaningful audit status; recommend API change `api-report-audit-inventory`.

## Phase 2: RED View Coverage

- [x] 2.1 Add failing `tests/test_reportes_view.py` cases for compact audit label rendering: available coverage, known gaps, unavailable, and not provided.
- [x] 2.2 Add a failing `tests/test_reportes_view.py` case proving local fallback text includes local, non-official, and audit unavailable.

## Phase 3: GREEN Desktop Implementation

- [x] 3.1 Update `controllers/reportes_controller.py` only to preserve/normalize supplied audit coverage variants, return explicit not-provided/unavailable states for missing data, and keep local fallback audit-empty.
- [x] 3.2 Update `views/reportes.py` only to add `label_dashboard_auditoria` after capacity metadata and render compact audit text without fabricating source coverage.

## Phase 4: Verification

- [x] 4.1 Run focused verification: `python -m unittest tests.test_reportes_controller tests.test_reportes_view`.
- [x] 4.2 Run full Desktop verification: `python -m unittest discover -s tests`.
- [x] 4.3 Confirm no API, Mobile, Installer, database, migration, new endpoint, or `utils/api_client.py` changes were introduced.
