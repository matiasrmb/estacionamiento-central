# Tasks: Desktop Intelligence Center Reporting and Audit Slice

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 260-360 |
| 400-line budget risk | Medium |
| Chained PRs recommended | No |
| Suggested split | Single Desktop PR |
| Delivery strategy | ask-on-risk |
| Chain strategy | feature-branch-chain |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: feature-branch-chain
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Normalize canonical dashboard data | PR 1 | `python -m unittest tests.test_reportes_controller` | N/A; payload-driven unit tests, live API PR #80/#81/#82 is runtime prerequisite | Revert `tests/test_reportes_controller.py` and `controllers/reportes_controller.py` |
| 2 | Render dashboard metadata and roadmap boundaries | PR 1 | `python -m unittest tests.test_reportes_view` | Open Desktop Reports view against API after PR #80/#81/#82 | Revert `tests/test_reportes_view.py` and `views/reportes.py` |

## Phase 1: RED Controller Tests

- [x] 1.1 Add RED canonical payload test in `tests/test_reportes_controller.py` proving labels, `period_state`, `source_state`, `completeness`, `capacity`, and `catalog_version` are preserved.
- [x] 1.2 Add RED fallback test in `tests/test_reportes_controller.py` proving API errors return local totals/items plus `source_state: local_fallback` and incomplete completeness metadata.
- [x] 1.3 Add RED payload-driven guard in `tests/test_reportes_controller.py` proving controller tests do not require PR #80/#81/#82 live API fields.

## Phase 2: Controller Normalization

- [x] 2.1 Extend `controllers/reportes_controller.py` `_normalizar_dashboard_reporting_api()` to preserve canonical fields and metric labels for the view model.
- [x] 2.2 Add fallback metadata handling in `controllers/reportes_controller.py` while preserving existing local `items` and `totals` compatibility.
- [x] 2.3 Run `python -m unittest tests.test_reportes_controller` and keep the new controller tests green.

## Phase 3: RED View Tests

- [x] 3.1 Add RED rendering tests in `tests/test_reportes_view.py` for canonical labels, open/closed period state, source state, incomplete warning, and capacity unavailable text.
- [x] 3.2 Add RED boundary tests in `tests/test_reportes_view.py` proving closed-report/export controls show future API-backed copy and do not call endpoints or generate PDF/CSV.

## Phase 4: View Rendering and Boundaries

- [x] 4.1 Update `views/reportes.py` dashboard rendering to display canonical labels, period/source state, completeness warning, and capacity metadata.
- [x] 4.2 Add non-operational closed/export boundary UI in `views/reportes.py` with prerequisite copy and information-only activation.
- [x] 4.3 Run `python -m unittest tests.test_reportes_view` and keep the new view tests green.

## Phase 5: Verification

- [x] 5.1 Run `python -m unittest tests.test_reportes_controller tests.test_reportes_view`.
- [x] 5.2 Run `python -m unittest discover -s tests`.
- [x] 5.3 Record runtime verification risk: live API validation requires PR #80/#81/#82 or equivalent canonical API work, but unit tests must remain payload-driven.
