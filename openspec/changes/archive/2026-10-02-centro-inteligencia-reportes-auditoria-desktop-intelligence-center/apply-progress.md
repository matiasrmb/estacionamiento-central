# Apply Progress: Desktop Intelligence Center Reporting and Audit Slice

## Status

- Mode: Strict TDD
- Delivery path: Single Desktop PR within feature-branch-chain boundary
- Scope completed: Desktop controller/view/tests only
- Runtime prerequisite: Live API validation still requires PR #80/#81/#82 or equivalent canonical reporting API work

## Completed Tasks

- [x] 1.1 Add RED canonical payload test in `tests/test_reportes_controller.py` proving labels, `period_state`, `source_state`, `completeness`, `capacity`, and `catalog_version` are preserved.
- [x] 1.2 Add RED fallback test in `tests/test_reportes_controller.py` proving API errors return local totals/items plus `source_state: local_fallback` and incomplete completeness metadata.
- [x] 1.3 Add RED payload-driven guard in `tests/test_reportes_controller.py` proving controller tests do not require PR #80/#81/#82 live API fields.
- [x] 2.1 Extend `controllers/reportes_controller.py` `_normalizar_dashboard_reporting_api()` to preserve canonical fields and metric labels for the view model.
- [x] 2.2 Add fallback metadata handling in `controllers/reportes_controller.py` while preserving existing local `items` and `totals` compatibility.
- [x] 2.3 Run `python -m unittest tests.test_reportes_controller` and keep the new controller tests green.
- [x] 3.1 Add RED rendering tests in `tests/test_reportes_view.py` for canonical labels, open/closed period state, source state, incomplete warning, and capacity unavailable text.
- [x] 3.2 Add RED boundary tests in `tests/test_reportes_view.py` proving closed-report/export controls show future API-backed copy and do not call endpoints or generate PDF/CSV.
- [x] 4.1 Update `views/reportes.py` dashboard rendering to display canonical labels, period/source state, completeness warning, and capacity metadata.
- [x] 4.2 Add non-operational closed/export boundary UI in `views/reportes.py` with prerequisite copy and information-only activation.
- [x] 4.3 Run `python -m unittest tests.test_reportes_view` and keep the new view tests green.
- [x] 5.1 Run `python -m unittest tests.test_reportes_controller tests.test_reportes_view`.
- [x] 5.2 Run `python -m unittest discover -s tests`.
- [x] 5.3 Record runtime verification risk: live API validation requires PR #80/#81/#82 or equivalent canonical API work, but unit tests remain payload-driven.

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 1.1-1.3 / 2.1-2.3 | `tests/test_reportes_controller.py` | Unit | ✅ `python -m unittest tests.test_reportes_controller tests.test_reportes_view` → 16 tests OK baseline | ✅ New canonical, fallback, and payload-driven tests failed with missing fields | ✅ `python -m unittest tests.test_reportes_controller` → 16 tests OK | ✅ API canonical payload, fallback payload, and minimal legacy payload paths covered | ✅ Normalization helper added; focused test stayed green |
| 3.1-3.2 / 4.1-4.3 | `tests/test_reportes_view.py` | Unit with PySide offscreen | ✅ `python -m unittest tests.test_reportes_controller tests.test_reportes_view` → 16 tests OK baseline | ✅ New rendering and roadmap-boundary tests failed on missing state labels/buttons | ✅ `python -m unittest tests.test_reportes_view` → 4 tests OK | ✅ API rendering, local fallback warning, and roadmap boundary interactions covered | ✅ Metadata rendering helpers added; focused test stayed green |
| 5.1-5.3 | `tests/test_reportes_controller`, `tests.test_reportes_view`, test discovery | Unit suite | ✅ Baseline captured before edits | N/A verification task | ✅ Required commands passed | N/A verification task | N/A verification task |

## Work Unit Evidence

| Evidence | Unit 1: Controller normalization | Unit 2: View rendering and roadmap boundaries |
|---|---|---|
| Focused test command and exact result | `python -m unittest tests.test_reportes_controller` → Ran 16 tests in 0.023s, OK | `python -m unittest tests.test_reportes_view` → Ran 4 tests in 0.142s, OK |
| Runtime harness command/scenario and exact result | N/A; payload-driven unit tests only. Live API PR #80/#81/#82 is a runtime prerequisite. | N/A for this apply slice; PySide offscreen unit test exercises the Desktop view boundary. Live Desktop/API runtime check remains deferred until API prerequisite is available. |
| Rollback boundary | Revert `tests/test_reportes_controller.py` and `controllers/reportes_controller.py`. | Revert `tests/test_reportes_view.py` and `views/reportes.py`. |

## Verification Results

- `python -m unittest tests.test_reportes_controller` → Ran 16 tests in 0.023s, OK
- `python -m unittest tests.test_reportes_view` → Ran 4 tests in 0.142s, OK
- `python -m unittest tests.test_reportes_controller tests.test_reportes_view` → Ran 20 tests in 0.184s, OK
- `python -m unittest discover -s tests` → Ran 380 tests in 7.632s, OK

## Deviations

None. Implementation matches the design boundaries: no API, Mobile, Installer, printer agent, closed-report endpoint, PDF, or CSV generation changes were made.

## Risks

- Live API validation is still deferred until PR #80/#81/#82 or equivalent canonical reporting API work is available.
- Existing workspace had unrelated modified/untracked OpenSpec state before this apply phase; this apply only changed the active change's `tasks.md` and `apply-progress.md` artifacts.
