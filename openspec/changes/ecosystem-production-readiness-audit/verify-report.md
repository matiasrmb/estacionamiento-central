# Verification Report: ecosystem-production-readiness-audit — FINAL Slice 6 Minimal Client Guidance

**Mode**: OpenSpec + Engram, Strict TDD for mobile behavior changes; docs and installer guidance validated with static/parser checks.
**Current verification scope**: FINAL Slice 6 / Minimal Client Guidance only: mobile production-safe server fallback/copy plus desktop/API/installer docs. No firewall, health, slowlog, DB/schema, or feature redesign changes were made.
**Verdict**: PASS — Slice 6 tasks 6.1 and 6.2 are complete with mobile TDD evidence, rerun Flutter validation, documentation updates, installer guidance validation, and manual LAN proof from a regular phone and Sunmi V2.

## Final Slice 6 Acceptance — 2026-06-29

Slice 6 removes the mobile production dependency on a developer LAN IP while preserving saved QR/manual server settings. Documentation reflects the validated production installer path, and performance guidance remains measurement-first only. Manual LAN validation now confirms the app connects to the installed API service through the server LAN IP from both a regular phone and a Sunmi V2.

### Implementation Verified

| Area | Files | Result |
|---|---|---|
| Mobile server fallback | `lib/core/config.dart`, `test/core/config_test.dart` | `defaultApiBaseUrl` is neutral/empty; no saved server now means “not configured” instead of falling back to `192.168.100.28`. Saved QR/manual URLs remain the active base URL. |
| Mobile connection guidance copy | `server_settings_screen.dart`, `qr_server_scanner_screen.dart` | Error/help text references the installed API service/server availability and installer guidance instead of instructing users to run the dev launcher. |
| Production deployment docs | `README.md` | Documents the validated installer path: API WinSW service, Print Agent service, firewall rule, production health, diagnostics, Sumatra path, mobile guidance, and printer caveat. |
| Performance guidance | `docs/performance_baseline.md` | States that no speculative DB/schema/index tuning was added; future tuning must be based on baseline measurements or slow-log evidence. |
| Installer-generated mobile guidance | `scripts/write_production_config.ps1` | Generated `mobile-connection.txt` instructs QR/manual configuration and explicitly rejects developer LAN IP fallback reliance. |
| Task tracking | `openspec/changes/ecosystem-production-readiness-audit/tasks.md` | All planned slices 1-6 and tasks 1.1-6.2 are marked complete, with prior caveats preserved where applicable. |

### Final Manual LAN Evidence

| Case | Result | Evidence source |
|---|---|---|
| Regular phone production connection | ✅ Pass | User reported the mobile LAN production connection was tested and works from a regular phone. |
| Sunmi V2 production connection | ✅ Pass | User reported the mobile LAN production connection was tested and works from Sunmi V2. |
| Installed API service via server LAN IP | ✅ Pass | User reported the app connects to the installed API service through the server LAN IP. |

### Final Local Validation Evidence — 2026-06-29

| Check | Result | Evidence |
|---|---|---|
| Required artifacts read | ✅ Pass | Proposal, design, both delta specs, tasks, previous verify report, Engram apply-progress #149, mobile config/settings/tests, README, performance baseline, and installer mobile guidance script were reviewed. |
| Mobile tests | ✅ Pass | `flutter test` passed all 3 tests in `C:\Users\matia\estacionamiento_central_mobile`. |
| Mobile analyzer | ✅ Pass | `flutter analyze` reported no issues. |
| Stale mobile dev references | ✅ Pass | Static command found no `run.ps1`, `192.168.100.28`, or `192.168.1.13` in mobile `lib`/`test` Dart files. |
| Desktop docs stale dev IPs | ✅ Pass | Static command found no `192.168.100.28` or `192.168.1.13` in `README.md` or `docs/performance_baseline.md`. README contains one allowed negative reference stating that production does not require manual `run.ps1`. |
| Installer guidance stale dev references | ✅ Pass | Static command found no `run.ps1`, `192.168.100.28`, or `192.168.1.13` in `scripts/write_production_config.ps1`. |
| PowerShell parser | ✅ Pass | PowerShell parser accepted `write_production_config.ps1` with no syntax errors. |
| Installer mobile guidance generation | ✅ Pass | Temp generation with `-ApiPort 8123` emitted `mobile-connection.txt` containing `http://<server-lan-ip>:8123/api/v1`, QR/manual setup instructions, and “must not rely on a developer LAN IP fallback.” |
| Task completeness | ✅ Pass | `tasks.md` marks Slice 6 tasks 6.1/6.2 complete; prior slices 1-5 are also complete with their recorded caveats. |

### Exact Command Evidence — 2026-06-29

| Command | CWD | Exit code | Relevant output |
|---|---|---:|---|
| `flutter test` | `C:\Users\matia\estacionamiento_central_mobile` | 0 | `00:01 +3: All tests passed!` |
| `flutter analyze` | `C:\Users\matia\estacionamiento_central_mobile` | 0 | `No issues found! (ran in 43.5s)` |
| `cmd /c findstr /S /N /R /C:"run\.ps1" /C:"192\.168\.100\.28" /C:"192\.168\.1\.13" "lib\*.dart" "test\*.dart"; ...` | `C:\Users\matia\estacionamiento_central_mobile` | 0 | `findstr exit code: 1` after wrapper normalized no-match to success. |
| `cmd /c findstr /N /R /C:"192\.168\.100\.28" /C:"192\.168\.1\.13" "README.md" "docs\performance_baseline.md"; ...` | `C:\Users\matia\estacionamiento-central` | 0 | `findstr exit code: 1` after wrapper normalized no-match to success. |
| `cmd /c findstr /N /R /C:"run\.ps1" "README.md" "docs\performance_baseline.md"; ...` | `C:\Users\matia\estacionamiento-central` | 0 | `README.md:68` states production uses the installer path and does not require manually running `run.ps1`. |
| `cmd /c findstr /N /R /C:"run\.ps1" /C:"192\.168\.100\.28" /C:"192\.168\.1\.13" "scripts\write_production_config.ps1"; ...` | `C:\Users\matia\estacionamiento-central-installer` | 0 | `findstr exit code: 1` after wrapper normalized no-match to success. |
| `$tokens = $null; $errors = $null; [void][System.Management.Automation.Language.Parser]::ParseFile('C:\Users\matia\estacionamiento-central-installer\scripts\write_production_config.ps1', [ref]$tokens, [ref]$errors); ...` | `C:\Users\matia\estacionamiento-central-installer` | 0 | `Parser OK` |
| `write_production_config.ps1 -AppDir <temp> -ApiPort 8123` | `C:\Users\matia\estacionamiento-central-installer` | 0 | Generated guidance included `Example: http://<server-lan-ip>:8123/api/v1` and `Production mobile clients must not rely on a developer LAN IP fallback.` |

### TDD Compliance

| Check | Result | Details |
|---|---|---|
| TDD Evidence reported | ✅ | Engram apply-progress #149 includes the Slice 6 TDD Cycle Evidence table. |
| All behavior tasks have tests | ✅ | Task 6.1 has `test/core/config_test.dart`; task 6.2 is docs/guidance-only with parser/static checks. |
| RED confirmed | ✅ | Apply-progress records the test first failed because `getApiBaseUrl()` returned `http://192.168.100.28:8000/api/v1`; the test file exists. |
| GREEN confirmed | ✅ | Current `flutter test` passed 3/3 tests. |
| Triangulation adequate | ✅ | Unit tests cover both no saved URL/empty fallback and saved QR/manual URL preservation. |
| Safety net for modified files | ✅ | Apply-progress records pre-change `flutter test` passed 1/1 before mobile behavior changes; current full Flutter suite passed. |
| Assertion quality | ✅ | Assertions verify concrete empty fallback, absence of `192.168.`, and saved URL preservation; no tautology, ghost loop, smoke-only, or type-only assertion was found in `test/core/config_test.dart`. |

**TDD Compliance**: PASS for Slice 6 behavior scope.

### Test Layer Distribution

| Layer | Tests/checks | Files | Tools |
|---|---:|---:|---|
| Unit | 2 Slice 6 config tests; 3 full Flutter tests | 2 test files | Flutter test |
| Static/docs | 4 static reference checks plus source/doc review | Mobile Dart, README, performance baseline, installer script | `findstr`, source inspection |
| Parser/generation | 1 parser check plus 1 temp config generation | `write_production_config.ps1` | PowerShell parser/execution |
| Manual LAN | 3 manual production connection checks | Installed API service + mobile app | User-provided validation |

### Changed File Coverage

Coverage analysis skipped. Flutter coverage tooling was not required by the tasks, and no project coverage threshold was detected for this Slice 6 verification.

### Spec Compliance Matrix — Final Slice 6

| Requirement | Slice 6 scenario/evidence | Result |
|---|---|---|
| Central Production Configuration | Mobile connection is no longer hardcoded to a developer IP; saved QR/manual settings remain the source of truth and installer guidance explains the LAN URL. Manual phone and Sunmi V2 validation prove the installed LAN API path works. | ✅ COMPLIANT |
| API Windows Service Lifecycle | Mobile copy points operators to installed API service/server availability instead of manual dev launcher operation. User evidence confirms the mobile app reaches the installed API service through the server LAN IP. | ✅ COMPLIANT for client guidance |
| Idempotent Firewall Rule Management | Documentation points mobile setup at the configured LAN API port; firewall logic itself was intentionally unchanged and prior Slice 4 evidence remains preserved. | ✅ PRESERVED |
| Threshold-Based Slow Operation Logs / no speculative tuning | `docs/performance_baseline.md` states that tuning requires baseline/slow-log evidence; no indexes/schema/tuning were added. | ✅ COMPLIANT |
| Validation Evidence Matrix | Automated Flutter tests/analyze, parser/temp guidance generation, static grep, docs review, task completeness, and manual phone/Sunmi LAN proof are recorded. | ✅ COMPLIANT for final Slice 6 |

**Compliance summary for Slice 6 scenarios**: 5/5 compliant.

### Issues Found — Final Slice 6

**CRITICAL**:
- None.

**WARNING**:
- Prior Slice 3 physical thermal printer caveat remains preserved: VM validation proved queue/failure semantics up to the hardware boundary, but real physical thermal print success still needs target-printer sign-off before production printer acceptance.

**SUGGESTION**:
- Consider a future automated widget/integration test for the server settings save flow with a mocked successful `/health` response, so the QR/manual connection UI has behavior-level coverage beyond the config unit tests.

### Final Verdict — Slice 6

PASS — Slice 6 satisfies minimal client guidance and production-safe mobile fallback requirements. All planned tasks for this OpenSpec change are marked complete and appropriately caveated. Do not archive from this verification executor run.

---

# Historical Verification Report: ecosystem-production-readiness-audit — Slice 5 Observability

**Mode**: OpenSpec + Engram, Strict TDD for Desktop/API product-code changes; installer validated with parser/temp dry-run evidence because no automated installer runner exists.
**Current verification scope**: Slice 5 / Observability only: threshold slow logs and diagnostics completion.
**Verdict**: PASS — Slice 5 tasks 5.1 and 5.2 are complete with automated/unit, parser, diagnostics-bundle, and final user-provided admin VM install/reinstall evidence. Slice 6 remains unstarted.

## Final Slice 5 Acceptance — 2026-06-28

Slice 5 is accepted as complete for slow-operation logging and diagnostics completion. The implementation stays threshold-only, redacts secret-like values, and does not add DB indexes, schema changes, firewall mutations, Slice 6 client guidance, or new product features.

### Final Manual VM/Admin Evidence

| Lifecycle / diagnostics case | Result | Evidence source |
|---|---|---|
| Fresh installation after compiling installer | ✅ Pass | User reported fresh install executed without problems. |
| Reinstall/update after compiling installer | ✅ Pass | User reported reinstall executed without problems. |
| Diagnostics bundle location | ✅ Pass | Diagnostics zips exist under `C:\EstacionamientoCentral\diagnostics`. |
| Diagnostics bundle structure | ✅ Pass | Zip contains `config`, `logs`, `metadata`, plus root `metadata.json`. |
| Redacted API config | ✅ Pass | `api.env` shows `DB_PASSWORD=[REDACTED]` and thresholds `SLOW_API_REQUEST_MS=1000`, `SLOW_API_DB_MS=500`. |
| Redacted Print Agent config | ✅ Pass | `print-agent.env` shows `DB_PASSWORD=[REDACTED]`, `SUMATRA_PATH=...`, and `SLOW_PRINT_JOB_MS=3000`. |
| Redacted production config | ✅ Pass | `production.json` database password is `[REDACTED]`; observability thresholds are present. |
| Normal installed logs are quiet | ✅ Pass | User ran `Select-String -Path "C:\EstacionamientoCentral\logs\**\*.log" -Pattern "SLOW|slow" -ErrorAction SilentlyContinue`; it returned nothing, proving no noisy slow-log spam in normal operation. |

### Final Local Verification Evidence — 2026-06-28

| Check | Result | Evidence |
|---|---|---|
| Required artifacts read | ✅ Pass | Proposal, design, `production-observability` spec, `production-deployment` spec, tasks, previous verify report, API/Desktop/Installer source, and Engram apply-progress #149. |
| API targeted slow-log tests | ✅ Pass | `python -m unittest tests.test_slowlog`: 3 tests passed. |
| API full suite | ✅ Pass | `python -m unittest discover -s tests`: 26 tests passed. |
| Desktop targeted slow-log tests | ✅ Pass | `python -m unittest tests.test_slowlog`: 3 tests passed. |
| Desktop full suite | ✅ Pass | `python -m unittest discover -s tests`: 102 tests passed. |
| PowerShell parser | ✅ Pass | `collect_diagnostics.ps1` and `write_production_config.ps1` parsed with no errors. |
| Diagnostics smoke/redaction | ✅ Pass | Temp app config generation and diagnostics collection created a `.zip` with required root/config/logs/metadata files; seeded `super-secret-password`, `token=abc123`, and `api_key=xyz` were absent after extraction; slow threshold metadata was present. |
| Task boundary | ✅ Pass | `tasks.md` marks Slice 5 tasks 5.1/5.2 complete and leaves Slice 6 tasks 6.1/6.2 unchecked. |

### TDD Compliance — Final Slice 5

| Check | Result | Details |
|---|---|---|
| TDD Evidence reported | ✅ | Engram apply-progress #149 and this report preserve RED/GREEN evidence for API/Desktop slow-log tests and installer diagnostics validation. |
| RED confirmed | ✅ | API/Desktop `tests/test_slowlog.py` exist and cover fast quiet path, slow redacted path, and threshold `0` disable behavior. |
| GREEN confirmed | ✅ | API targeted/full and Desktop targeted/full suites passed during final verification. |
| Triangulation adequate | ✅ | Slow-log behavior is tested across fast, slow, redaction, and disabled-threshold cases; diagnostics smoke verifies structure and redaction with multiple secret patterns. |
| Safety net for modified files | ✅ | Full API and Desktop suites were rerun; installer scripts passed parser and temp diagnostics execution. |
| Assertion quality | ✅ | Assertions verify concrete emitted fields, absence of leaked secrets, no-message quiet path, and required bundle files; no tautologies, ghost loops, or smoke-only assertions found in `tests/test_slowlog.py`. |

### Spec Compliance Matrix — Final Slice 5

| Requirement | Slice 5 scenario/evidence | Result |
|---|---|---|
| Threshold-Based Slow Operation Logs — normal operations stay quiet | API/Desktop tests prove below-threshold operations emit no log; installed log search returned no `SLOW|slow` matches during normal operation. | ✅ COMPLIANT |
| Threshold-Based Slow Operation Logs — slow operation is captured safely | API/Desktop tests prove slow operations emit one structured `slow_operation` line with area, operation, duration, threshold, safe context, and redacted secret-like values. | ✅ COMPLIANT |
| Required Instrumentation Coverage | Source inspection confirms API request/DB, Desktop registration/exit/dashboard/table/PDF/print, and Print Agent claim/render/print/mark/retry paths are instrumented; thresholds are generated for API/Desktop/Print Agent. | ✅ COMPLIANT |
| Redacted Diagnostics Bundle | Local smoke and installed-bundle user evidence confirm config/log/metadata collection with secret redaction and observability thresholds. | ✅ COMPLIANT |
| Production Health Checks | Slice 4 health behavior remains preserved; Slice 5 adds diagnostics/log metadata without mutating health/firewall/service behavior. | ✅ PRESERVED |
| Validation Evidence Matrix | Automated API/Desktop tests, parser checks, diagnostics smoke, fresh install, reinstall, diagnostics zip inspection, and quiet installed logs are recorded. | ✅ COMPLIANT for Slice 5 |

### Issues Found — Final Slice 5

**CRITICAL**:
- None.

**WARNING**:
- None for Slice 5. Prior printer hardware caveat from Slice 3 remains outside this verification scope.

**SUGGESTION**:
- Add a future Pester-style harness for diagnostics/health scripts to automate archive structure and redaction checks without temp-shell validation.

### Final Verdict — Slice 5

PASS — Slice 5 satisfies slow logs and diagnostics completion with final admin VM evidence, automated test evidence, and no Slice 6 work started.

## Slice 5 Acceptance — 2026-06-28

Slice 5 adds threshold-only observability without tuning or product feature changes. Slow logs emit only when configured thresholds are exceeded and include safe structured context only. Diagnostics now exports redacted logs, selected config metadata, service metadata, log path metadata, and skipped-log metadata.

### Implementation Added

| Area | Files | Result |
|---|---|---|
| API request slow logs | `app/main.py`, `app/core/slowlog.py` | Middleware logs requests over `SLOW_API_REQUEST_MS` (default `1000`, `0` disables) with method/path/status/duration only. |
| API DB slow logs | `app/db/database.py`, `app/core/slowlog.py` | SQLAlchemy cursor events log statements over `SLOW_API_DB_MS` (default `500`, `0` disables) with operation/executemany only; no SQL params or secrets. Test stubs without SQLAlchemy events are safely skipped. |
| Desktop slow logs | `utils/slowlog.py`, `controllers/registro_controller.py`, `controllers/dashboard_controller.py`, `utils/ticket.py`, `utils/pdf.py` | Decorators cover registration, exit, dashboard refresh, table refresh, PDF generation, and printing over `SLOW_DESKTOP_MS` (default `1000`, `0` disables). Desktop reads env first, then `config.ini [observability]`. |
| Print Agent slow logs | `printer_agent/agent.py`, `app/core/slowlog.py` | Claim, stale-lock release, render, print, mark printed, and mark error steps log over `SLOW_PRINT_JOB_MS` (default `3000`, `0` disables). |
| Generated thresholds | `scripts/write_production_config.ps1` | Generates `SLOW_API_REQUEST_MS`, `SLOW_API_DB_MS`, `SLOW_PRINT_JOB_MS`, Desktop `[observability] SLOW_DESKTOP_MS`, and `production.json observability` metadata. |
| Diagnostics bundle | `scripts/collect_diagnostics.ps1` | Adds redacted `metadata/log-paths.json`, `metadata/config-summary.json`, `metadata/services.json`, `metadata/skipped-logs.json`; keeps redacted configs/logs and size-bounded log copying. |

### Local Validation Evidence

| Check | Result | Evidence |
|---|---|---|
| Required artifacts read | ✅ Pass | Proposal, design, production-observability spec, production-deployment spec, tasks, prior verify report, diagnostics/config/health scripts, API/Desktop/Print Agent source, and Engram apply-progress #149. |
| API RED | ✅ Pass | `python -m unittest tests.test_slowlog` initially failed with `ModuleNotFoundError: No module named 'app.core.slowlog'`. |
| Desktop RED | ✅ Pass | `python -m unittest tests.test_slowlog` initially failed with `ModuleNotFoundError: No module named 'utils.slowlog'`. |
| API GREEN targeted | ✅ Pass | `python -m unittest tests.test_slowlog tests.test_print_agent_service_main tests.test_service_main`: 7 tests passed. |
| Desktop GREEN targeted | ✅ Pass | `python -m unittest tests.test_slowlog tests.test_registro_controller`: 42 tests passed. |
| API full suite | ✅ Pass | `python -m unittest discover -s tests`: 26 tests passed. |
| Desktop full suite | ✅ Pass | `python -m unittest discover -s tests`: 102 tests passed. |
| API import smoke | ✅ Pass | `python -c "import app.main; print('app.main import OK')"` passed. |
| PowerShell parser | ✅ Pass | `collect_diagnostics.ps1`, `write_production_config.ps1`, and `check_production_health.ps1` parsed with no errors. |
| Diagnostics temp run | ✅ Pass | Temp `write_production_config.ps1` generated threshold config; temp `collect_diagnostics.ps1` created a `.zip`; extracted content included config/service/log-path/skipped-log metadata and did not contain seeded `super-secret-password`, `token=abc123`, or `api_key=xyz`. |
| Scope boundary | ✅ Pass | No DB indexes/schema changes, firewall changes beyond diagnostics metadata, mobile/Desktop production guidance, or new product features were implemented. |

### TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 5.1 Threshold slow logs | API `tests/test_slowlog.py`; Desktop `tests/test_slowlog.py` | Unit | API service/agent targeted tests passed 4/4 before full suite; Desktop registration targeted suite passed after decoration; full suites passed after implementation | ✅ API and Desktop tests were written first and failed on missing `slowlog` modules | ✅ API targeted 7/7, Desktop targeted 42/42, API full 26/26, Desktop full 102/102 | ✅ Covers fast quiet path, slow safe/redacted path, and threshold `0` disable path for API/agent and Desktop helpers | ✅ Shared helper/decorator keeps instrumentation small and safe; SQLAlchemy event registration skips test stubs without event support |
| 5.2 Diagnostics completion | PowerShell parser + temp diagnostics bundle validation | Installer script/manual-gated | N/A — installer has no automated runner; parser and temp execution used | ✅ Temp diagnostics initially failed on PowerShell 5.1 generic-list/empty-array archive behavior | ✅ Parser passed; temp diagnostics zip created; redaction and required metadata checks passed | ✅ Bundle validation seeded `password`, `token`, and `api_key` values, verified absence after extraction, and checked required metadata files | ✅ Replaced fragile generic-list serialization and guaranteed `skipped-logs.json` is emitted even when no logs are skipped |

### Spec Compliance Matrix — Slice 5

| Requirement | Slice 5 scenario/evidence | Result |
|---|---|---|
| Threshold-Based Slow Operation Logs | Synthetic tests prove fast operations stay quiet, slow operations emit one safe structured log, and `0` disables logging. | ✅ COMPLIANT |
| Required Instrumentation Coverage | API requests, API DB, Desktop registration/exit/dashboard/table/PDF/print, Print Agent claim/render/print/retry/mark paths, and generated installer health threshold defaults are covered. | ✅ COMPLIANT for Slice 5 local apply |
| Redacted Diagnostics Bundle | Temp bundle includes logs/config/service/log-path metadata and redacts seeded password/token values. | ✅ COMPLIANT locally |
| Production Health Checks | Prior Slice 4 health checks preserved; Slice 5 only adds diagnostics/log metadata and does not mutate firewall/service behavior. | ✅ PRESERVED |
| Validation Evidence Matrix | Automated API/Desktop tests, parser checks, temp diagnostics execution, and scope-boundary evidence recorded here. | ✅ COMPLIANT for apply; final VM release evidence remains future verify work |

### Issues Found — Slice 5

**CRITICAL**:
- None for local Slice 5 apply.

**WARNING**:
- Final production value still depends on running the generated installer in the controlled admin VM and reviewing real slow-log/diagnostics output under installed paths.

**SUGGESTION**:
- Add a future Pester-style harness for diagnostics/health scripts to automate archive contents and redaction checks without temp-shell validation.

### Final Verdict

PASS LOCALLY — Slice 5 satisfies threshold slow logs and diagnostics completion within the approved local apply boundary. Slice 6 remains unstarted.

---

# Historical Verification Report: ecosystem-production-readiness-audit — Slice 4 Final Firewall + Health

**Mode**: OpenSpec + Engram, Strict TDD constrained to Desktop/API/Mobile product code. Slice 4 touched installer scripts and Inno Setup wiring only; no API health endpoint behavior changed.
**Current verification scope**: FINAL Slice 4 / Phase 4 Firewall and Health after user-provided admin/VM validation evidence. Slice 5 was not started.
**Verdict**: PASS WITH PRINTER WARNING — Slice 4 satisfies idempotent firewall rule management and production health-check requirements. The only warning is expected: `PRINTER_NAME` is not configured, while one printer was detected.

## Final Slice 4 Acceptance — 2026-06-28

Slice 4 is accepted as complete for the firewall and production health-check scope. The implementation keeps Inno Setup as orchestrator, manages exactly one installer-owned firewall rule by stable display name/group, validates narrow inbound TCP Private-profile access for the configured API port, and runs a production health gate after API and Print Agent service setup.

### Final Manual VM/Admin Evidence

| Lifecycle / health case | Result | Evidence source |
|---|---|---|
| Fresh installation | ✅ Pass | User reported fresh install executed correctly. |
| Reinstall/update | ✅ Pass | User reported reinstall/update executed correctly after the idempotency and validator corrections. |
| API service | ✅ Pass | Health output: API service running. |
| API health endpoint | ✅ Pass | Health output: HTTP 200. |
| MySQL service and port | ✅ Pass | Health output: MySQL service running and `127.0.0.1:3306` reachable. |
| Print Agent service | ✅ Pass | Health output: Print Agent service running. |
| Firewall rule | ✅ Pass | Health output: firewall rule allows inbound TCP private-profile traffic for port 8000. |
| Firewall idempotency | ✅ Pass | `@(Get-NetFirewallRule -Group "Estacionamiento Central").Count` returned `1`, proving no duplicate owned rule after reinstall/update. |
| SumatraPDF | ✅ Pass | Health output found `C:\EstacionamientoCentral\tools\SumatraPDF\SumatraPDF.exe`. |
| Print Spooler | ✅ Pass | Health output: Print Spooler running. |
| Printer availability | ⚠️ Expected warning | `PRINTER_NAME` is not configured; detected printer count=1. This is a non-blocking hardware/config warning by design. |

### Final Local Verification Evidence

| Check | Result | Evidence |
|---|---|---|
| Required artifacts read | ✅ Pass | Proposal, design, both delta specs, tasks, previous verify report, installer scripts, `.iss`, and apply-progress Engram #149. |
| PowerShell parser | ✅ Pass | `manage_firewall_rule.ps1` and `check_production_health.ps1` parsed with no errors. |
| Firewall validator SelfTest | ✅ Pass | `manage_firewall_rule.ps1 -Action SelfTest` exited 0 and accepted `True/Inbound/Allow/Private/TCP/8000`. |
| Firewall manager DryRun | ✅ Pass | `manage_firewall_rule.ps1 -Action DryRun` exited 0 without mutating firewall state. |
| Production health DryRun | ✅ Pass | `check_production_health.ps1 -Action DryRun` exited 0 without querying real services/firewall. |
| Owned-rule scope static check | ✅ Pass | No `Set-NetFirewallPortFilter`/`Set-NetFirewallRule` in-place mutation path remains; rollback/uninstall remove only exact DisplayName+Group owned rules. |
| Narrow firewall static check | ✅ Pass | No broad `LocalPort Any` or `*` rule found; rule creation uses TCP and Private profile. |
| Health firewall validation static check | ✅ Pass | Health checker uses normalized enabled/string/profile/port comparison helpers. |
| Installer wiring static check | ✅ Pass | `.iss` copies firewall/health scripts, runs firewall setup before health, and removes the owned firewall rule on uninstall. |
| Task boundary | ✅ Pass | `tasks.md` now marks Slice 4 tasks 4.1/4.2 complete; Slice 5 tasks 5.1/5.2 remain unchecked. |

### Spec Compliance Matrix — Slice 4 Final

| Requirement | Slice 4 scenario/evidence | Result |
|---|---|---|
| Installer-Orchestrated Deployment | Existing Inno Setup installer remains owner and runs firewall + health after API/Print Agent setup. | ✅ COMPLIANT |
| Idempotent Firewall Rule Management | Fresh install and reinstall/update pass; one owned group rule remains; rollback/uninstall path is scoped to exact owned identity. | ✅ COMPLIANT |
| Production Health Checks | Health reports PASS/WARN status for API, DB, services, firewall, SumatraPDF, spooler, and printer readiness without destructive action. | ✅ COMPLIANT WITH EXPECTED PRINTER WARNING |
| Validation Evidence Matrix | Manual fresh install/reinstall and local parser/SelfTest/DryRun/static checks are recorded; prior Slice 2/3 incident history is preserved below. | ✅ COMPLIANT for Slice 4 |
| Slow logs and diagnostics completion | Later slice; intentionally not started. | ➖ Not evaluated in this scope |

### Firewall Idempotency Fix Path Summary

The first Slice 4 incident showed reinstall/update failed during the firewall update path after fresh install created the rule and rollback removed it. The correction replaced fragile in-place mutation with an exact owned-rule no-op when the rule already matches, or remove/recreate for mismatched/duplicated owned DisplayName+Group rules. A follow-up incident showed the rule already had desired values but the validator rejected it; the validator now normalizes boolean-ish, enum/string, profile, protocol, and scalar/array local-port values while preserving strict Private/TCP/exact-port requirements. Final VM evidence proves this path: reinstall/update succeeds and the owned firewall group count is exactly one.

### Issues Found — Slice 4 Final

**CRITICAL**:
- None for Slice 4 firewall and health scope.

**WARNING**:
- Printer availability remains WARN because `PRINTER_NAME` is not configured. This is expected and non-blocking; a real target printer name should be configured before production printer sign-off.

**SUGGESTION**:
- Add a future non-mutating Pester-style harness for firewall/health scripts to lock desired-state normalization and owned-rule scoping without requiring admin firewall mutation.

### Final Verdict

PASS WITH PRINTER WARNING — Slice 4 satisfies firewall idempotency and production health-check requirements with final manual VM/admin evidence plus local parser/SelfTest/DryRun/static validation. Slice 5 remains unstarted.

## Slice 4 Local Apply Notes — 2026-06-28

### Implementation Added
- Added `scripts\manage_firewall_rule.ps1` with `InstallOrUpdate`, `Uninstall`, `Rollback`, and `DryRun`. It manages only one owned inbound TCP rule by stable display name `EstacionamientoCentral API Port 8000` and group `Estacionamiento Central`, reads the configured API port from `config\api.env`, updates the existing owned rule instead of duplicating it, and removes only matching name/group rules on uninstall/rollback.
- Added `scripts\check_production_health.ps1` with safe PASS/WARN/FAIL checks for API service state, local `/api/v1/health`, MySQL service and TCP port, Print Agent service state, owned firewall rule/port, SumatraPDF path, spooler, and printer availability. Printer absence is WARN; API/DB/service/firewall/Sumatra failures are hard FAIL.
- Wired `EstacionamientoCentral.iss` to copy both scripts, generate production config before services, install/update firewall after API and Print Agent services, run production health after firewall setup, and remove the owned firewall rule on uninstall. Health failure attempts rollback of owned firewall/API/Print Agent resources.
- No DB/schema, slow-log, diagnostics completion, mobile/Desktop guidance, or API endpoint behavior changes were made.

### Local Validation Evidence
| Check | Result | Evidence |
|---|---|---|
| Required artifacts read | ✅ Pass | Proposal, design, production-deployment spec, production-observability spec, tasks, previous verify report, and apply-progress Engram #149. |
| PowerShell parser | ✅ Pass | `manage_firewall_rule.ps1`, `check_production_health.ps1`, `write_production_config.ps1`, `manage_api_service.ps1`, and `manage_print_agent_service.ps1` parsed with no errors. |
| Temporary config generation | ✅ Pass | `write_production_config.ps1 -AppDir <temp> -ApiPort 8123` generated `config\api.env`, `config\print-agent.env`, and `production.json` without logging secrets. |
| Firewall manager DryRun | ✅ Pass | `manage_firewall_rule.ps1 -AppDir <temp> -Action DryRun` exited 0 and reported stable rule/group with configured port `8123`; no real firewall mutation was performed. |
| Production health DryRun | ✅ Pass | `check_production_health.ps1 -AppDir <temp> -Action DryRun` exited 0 and reported intended API/DB/service/firewall/Sumatra/printer checks; no service/firewall mutation was performed. |
| Firewall static scope | ✅ Pass | Static check confirmed stable name/group, TCP local-port scoping, no broad `Any`/`*` port rule, and uninstall/rollback removal limited to owned name/group. |
| Installer wiring static check | ✅ Pass | `.iss` copies the new scripts, generates production config before service setup, runs firewall setup after API/Print Agent setup, runs health afterward, and unregisters the owned firewall rule on uninstall. |
| API health endpoint behavior | ➖ Not changed | No API endpoint source was modified; no API product tests were required or run for Slice 4. |

### Previously Remaining Manual Validation — superseded by Final Slice 4 Acceptance above
- Manually compile the Inno Setup installer after this Slice 4 apply.
- Run controlled admin/VM fresh install and reinstall/update. Confirm exactly one enabled owned firewall rule exists with display name `EstacionamientoCentral API Port 8000`, group `Estacionamiento Central`, protocol TCP, and local port from generated `config\api.env`.
- Confirm uninstall/rollback removes only that owned firewall rule and leaves unrelated firewall rules untouched.
- Confirm production health produces PASS for API service, `/api/v1/health`, MySQL service/port, Print Agent service, firewall rule, and SumatraPDF path; WARN is acceptable for printer absence/offline hardware caveat.
- Confirm no DB/schema changes, slow-log instrumentation, diagnostics completion, or mobile/Desktop guidance changes were introduced in this slice.

## Slice 4 Firewall Reinstall/Update Correction — 2026-06-28

**Scope**: ONLY the approved Slice 4 correction for firewall reinstall/update idempotency failure. Slice 5 was not started.

**Incident evidence**: Fresh install created the owned firewall rule successfully. Reinstall/update failed during firewall update, and rollback correctly removed the owned rule. Audit identified the fragile in-place mutation path around `Set-NetFirewallPortFilter -AssociatedNetFirewallRule`.

**Correction applied**:
- `scripts\manage_firewall_rule.ps1` now queries owned rules by exact display name `EstacionamientoCentral API Port 8000` plus group `Estacionamiento Central`.
- If exactly one owned rule already matches enabled inbound allow Private-profile TCP traffic for the configured API port, the script logs an idempotent no-op and exits 0.
- If owned rules are mismatched or duplicated, the script removes only those owned DisplayName+Group rules and recreates a single correct rule. It no longer mutates the port filter in place.
- Top-level error logging now records the exception message and script stack trace before exiting non-zero.
- `scripts\check_production_health.ps1` now validates firewall direction, action, and profile in addition to enabled/protocol/port.

**Local validation added**:
- PowerShell parser checks passed for `manage_firewall_rule.ps1` and `check_production_health.ps1`.
- `manage_firewall_rule.ps1 -Action DryRun` exited 0 without mutating firewall state.
- `check_production_health.ps1 -Action DryRun` exited 0.
- Static check found no `Set-NetFirewallPortFilter -AssociatedNetFirewallRule` update path remaining.
- Static checks confirmed idempotent no-op logic, remove/recreate logic, and Rollback/Uninstall filtering by owned DisplayName+Group.

**Previously remaining manual validation**: Recompile the installer, then rerun the controlled admin/VM fresh install followed by reinstall/update. Confirm reinstall/update exits cleanly, leaves exactly one matching owned firewall rule, and uninstall/rollback removes only that owned rule while preserving unrelated firewall rules. This was superseded by the Final Slice 4 Acceptance evidence above.

## Slice 4 Firewall Validator False-Negative Correction — 2026-06-28

**Scope**: ONLY the approved Slice 4 correction for the firewall validator false negative. Slice 5 was not started.

**Incident evidence**: Fresh install created the owned firewall rule and the logged values matched the desired state: `enabled=True`, `direction=Inbound`, `action=Allow`, `profile=Private`, `protocol=TCP`, `local_port=8000`, `desired_port=8000`. `Assert-OwnedRuleIsNarrow` still threw `Owned firewall rule does not match desired state`.

**Correction applied**:
- `scripts\manage_firewall_rule.ps1` now normalizes boolean-ish enabled values, enum/string direction/action/protocol values, profile values, and scalar/array local-port values before desired-state comparison.
- The validator remains strict: it still requires enabled, inbound, allow, explicit Private-profile inclusion, TCP, and exact configured local port. `Profile=Any` is not accepted as narrow.
- Added non-mutating `SelfTest` action to exercise the validator with the exact reported desired-state values.
- `scripts\check_production_health.ps1` uses the same normalized boolean/string/profile/port comparison helpers for firewall health validation.

**Local validation added**:
- PowerShell parser checks passed for `manage_firewall_rule.ps1` and `check_production_health.ps1`.
- `manage_firewall_rule.ps1 -Action SelfTest` exited 0 and accepted the mocked desired state: `True/Inbound/Allow/Private/TCP/8000`.
- `manage_firewall_rule.ps1 -Action DryRun` exited 0 without mutating firewall state.
- `check_production_health.ps1 -Action DryRun` exited 0.
- Static checks found no `Set-NetFirewallPortFilter`, no `Set-NetFirewallRule`, no all-port firewall rule, and rollback/uninstall removal remains scoped to exact owned DisplayName+Group rules.

**Previously remaining manual validation**: Recompile the installer, then rerun controlled admin/VM fresh install and reinstall/update. Confirm the reinstall/update exits cleanly, leaves exactly one matching owned firewall rule, and uninstall/rollback removes only that owned rule while preserving unrelated rules. This was superseded by the Final Slice 4 Acceptance evidence above.

---

# Historical Verification Report: ecosystem-production-readiness-audit — Slice 3 Final with Hardware Caveat

**Mode**: OpenSpec + Engram, Strict TDD constrained to Desktop/API/Mobile product code. Slice 2 touched installer/API packaging and service scripts only; no API product behavior change was found.
**Current verification scope**: FINAL Slice 3 / Phase 3 Print Agent lifecycle after manual VM/admin validation up to the hardware boundary. Slice 4 was not started.
**Cumulative evidence preserved**: Slice 1 / Phase 1 Installer Foundation evidence remains summarized below.
**Verdict**: PASS WITH HARDWARE CAVEAT for Slice 3 Print Agent lifecycle. Local safe checks pass, Slice 3 task boundaries are respected, and user-provided VM/admin evidence proves service install/start/reboot, reinstall/update idempotency, uninstall preservation, Sumatra production path wiring, and one controlled queue job consumed exactly once into the expected hardware-boundary failure state. Physical thermal print success remains unproven because the VM lacks the real printer.

## Final Slice 3 Acceptance — 2026-06-28

Slice 3 is accepted as complete for the Print Agent service lifecycle scope, with a hardware caveat. The final implementation uses a PyInstaller `onedir` Print Agent payload, WinSW automatic Windows service ownership, final installed paths in generated XML, installer-generated `SUMATRA_PATH={app}\tools\SumatraPDF\SumatraPDF.exe`, duplicate-agent prevention, and non-destructive queue/retry semantics.

### Final Manual VM/Admin Evidence

| Lifecycle case | Result | Evidence source |
|---|---|---|
| Fresh installation | ✅ Pass | User reported fresh install executed normally. |
| Service creation/start | ✅ Pass | `EstacionamientoCentralPrintAgent` status reported `Running`. |
| Reboot recovery | ✅ Pass | After reboot, service remained `Running`. |
| Reinstall/update preserving DB | ✅ Pass | User reported reinstall/update succeeded preserving DB with no duplicate Print Agent service. |
| Reinstall/update not preserving DB | ✅ Pass | User reported reinstall/update succeeded without preserving DB with no duplicate Print Agent service. |
| Uninstall | ✅ Pass | User reported uninstall preserves data/logs. |
| Sumatra production config | ✅ Pass | Service logs show `SUMATRA_PATH=C:\EstacionamientoCentral\tools\SumatraPDF\SumatraPDF.exe`. |
| Queue consumption / failure semantics | ✅ Pass | Controlled MySQL job inserted with `max_intentos=1`; Print Agent consumed it and updated `estado=ERROR`, `intentos=1`, `locked_by=NULL`, `last_error='Sumatra print failed rc=1 ...'`. |
| Physical thermal print | ⚠️ Hardware caveat | VM uses Microsoft Print to PDF / lacks real thermal printer, so physical print success is not proven in this slice. |

### Final Local Verification Evidence

| Check | Result | Evidence |
|---|---|---|
| Required artifacts read | ✅ Pass | Proposal, design, both delta specs, tasks, previous verify report, and apply-progress Engram #149. |
| API / Print Agent tests | ✅ Pass | `python -m unittest discover -s tests` in API repo: 23 tests passed. Targeted `python -m unittest tests.test_print_agent_service_main`: 2 tests passed. |
| PowerShell parser | ✅ Pass | `manage_print_agent_service.ps1`, `stage_print_agent_payload.ps1`, and `write_production_config.ps1` parsed with no errors. |
| Print Agent service DryRun | ✅ Pass | `scripts\manage_print_agent_service.ps1 -AppDir C:\Users\matia\estacionamiento-central-installer -Action DryRun` exited 0. |
| Generated config check | ✅ Pass | Temporary `write_production_config.ps1` run generated `config\print-agent.env` and `production.json` with `tools\SumatraPDF\SumatraPDF.exe`. |
| WinSW XML static checks | ✅ Pass | Template is valid XML, uses `Automatic`, has three restart-on-failure entries, passes `SUMATRA_PATH`, and contains no `python` or `run_agent_forever`. |
| Installer wiring static checks | ✅ Pass | `.iss` packages `payload\print-agent`, packages `tools\SumatraPDF`, runs `manage_print_agent_service.ps1 -Action InstallOrUpdate`, and unregisters the owned service on uninstall. |
| Payload exclusions | ✅ Pass | No `.env`, logs, locks, `__pycache__`, `tests`, or `print_out` paths found under `payload\print-agent`. |
| Developer Sumatra path exclusion | ✅ Pass | No installer scripts/templates/payload files contain `C:\Users\matia\AppData\Local\SumatraPDF`. |
| Portable Sumatra staged | ✅ Pass | `tools\SumatraPDF\SumatraPDF.exe` exists in the installer workspace. |
| Task boundary | ✅ Pass | `tasks.md` now marks Slice 3 tasks 3.1 and 3.2 complete with a hardware caveat; Slice 4 remains unchecked. |

### Spec Compliance Matrix — Slice 3 Final

| Requirement | Slice 3 scenario/evidence | Result |
|---|---|---|
| Installer-Orchestrated Deployment | Existing Inno Setup installer remains owner; Print Agent service work is wired into `.iss` without replacing the installer. | ✅ COMPLIANT |
| Installer-Owned Print Agent Lifecycle — queued jobs survive update | Manual lifecycle proves service install/start/reboot/reinstall/uninstall; controlled job was consumed exactly once and preserved queue failure state (`ERROR`, `intentos=1`, unlocked) at the hardware boundary. | ✅ COMPLIANT WITH HARDWARE CAVEAT |
| Central Production Configuration | Installer-generated Print Agent env and WinSW XML carry `SUMATRA_PATH={app}\tools\SumatraPDF\SumatraPDF.exe`; service logs confirm installed path. | ✅ COMPLIANT |
| Data-Safe Deployment Operations | Reinstall/update works with and without DB preservation; uninstall preserves data/logs; Print Agent does not delete print jobs. | ✅ COMPLIANT |
| Validation Evidence Matrix | Fresh install, reboot, reinstall/update, uninstall, API/Print Agent tests, parser/static/DryRun checks, and queue-processing evidence are recorded. | ✅ COMPLIANT for Slice 3; physical print remains hardware caveat |
| Firewall, health checks, slow logs, mobile guidance | Later slices; Slice 4+ intentionally not started. | ➖ Not evaluated in this scope |

**Compliance summary for Slice 3 scenarios**: 5/5 Slice 3 scenarios compliant; 1 physical-print outcome remains hardware-dependent and must be validated on real printer hardware.

### TDD Compliance

Strict TDD mode is active for Desktop/API/Mobile. Slice 3 touched API Print Agent entrypoint/config behavior and installer scripts. Product-code test evidence exists for the API/Print Agent change: `tests/test_print_agent_service_main.py` covers service-safe defaults and installer-provided `SUMATRA_PATH`; targeted and full API test suites passed. Installer scripts have no automated unit runner, so parser/static/DryRun/manual VM evidence is used for installer behavior.

| Check | Result | Details |
|---|---|---|
| TDD Evidence reported | ✅ | Apply-progress #149 includes a TDD Cycle Evidence table for Print Agent Sumatra config and installer script checks. |
| RED confirmed | ✅ | Apply-progress records the targeted test first failed with `KeyError: 'sumatra_path'`; file exists and now covers the behavior. |
| GREEN confirmed | ✅ | Targeted test passed 2/2; full API suite passed 23/23. |
| Triangulation adequate | ✅ | Defaults and installer override paths are both covered. |
| Safety net | ✅ | Existing targeted test file plus full API suite were run after the config/entrypoint change. |
| Assertion quality | ✅ | Assertions verify concrete config values; no tautologies, ghost loops, or smoke-only assertions found. |

### Test Layer Distribution

| Layer | Tests/checks | Files | Tools |
|---|---:|---:|---|
| Unit | 2 targeted tests; 23 full API tests | 4 API test files | Python `unittest` |
| PowerShell parser/static | 3 parser checks + XML/static checks | 3 scripts + template + `.iss` | PowerShell parser/XML/string checks |
| Installer/service dry-run | 1 dry-run smoke | `manage_print_agent_service.ps1` | PowerShell execution |
| Manual VM/admin | lifecycle + queue job evidence | Installed service/DB/logs | User-provided validation |

### Changed File Coverage

Coverage analysis skipped — no coverage tool detected/configured for this cross-repo installer/API slice.

### Issues Found — Slice 3 Final

**CRITICAL**:
- None for Slice 3 lifecycle scope.

**WARNING**:
- Physical thermal print success remains unproven because validation used Microsoft Print to PDF / no real thermal printer. The queue/failure semantics are proven up to the hardware boundary.

**SUGGESTION**:
- Validate the same controlled job on the real thermal printer before production release sign-off.
- Consider a non-mutating Pester-style harness for `manage_print_agent_service.ps1` to lock XML rendering, prerequisite gating, staging, and duplicate-service prevention in automated tests.

### Final Verdict

PASS WITH HARDWARE CAVEAT — Slice 3 satisfies the installer-owned Print Agent lifecycle, duplicate prevention, production Sumatra config, data-safety, and queue-processing semantics within the validated VM boundary. Slice 4 was not started; firewall and health-check work remain next.

## Final Slice 2 Acceptance — 2026-06-27

Slice 2 is accepted as complete for the API service deployment scope. The final implementation uses a PyInstaller `onedir` API payload, WinSW automatic Windows service ownership, clean staged payload replacement, update via owned-service `uninstall`/`install` instead of fragile `refresh`, and data/log preservation outside `{app}\api`.

### Final Manual VM/Admin Evidence

| Lifecycle case | Result | Evidence source |
|---|---|---|
| Fresh installation | ✅ Pass | User reported fresh installation completed normally. |
| Service creation/start | ✅ Pass | `EstacionamientoCentralAPI` status reported `Running`. |
| API health | ✅ Pass | API health returned HTTP 200 OK. |
| Logs | ✅ Pass | Logs exist and show success under `logs/api-service` and `logs/installer`. |
| Reboot recovery | ✅ Pass | After reboot, service remained `Running` and health stayed OK. |
| Reinstall/update preserving DB | ✅ Pass | User reported reinstall/update succeeded preserving DB with no duplicate services. |
| Reinstall/update not preserving DB | ✅ Pass | User reported reinstall/update succeeded without preserving DB with no duplicate services. |
| Uninstall | ✅ Pass | User reported uninstall leaves no API service. |
| Manual rollback | ✅ Pass | User reported rollback removes service and preserves data/logs. |

### Final Local Verification Evidence

| Check | Result | Evidence |
|---|---|---|
| API tests | ✅ Pass | `python -m unittest discover -s tests` in API repo: 21 tests passed. |
| Service entrypoint tests | ✅ Pass | `tests/test_service_main.py` covers production defaults, env host/port override, and `reload=False`. |
| PowerShell parser | ✅ Pass | `manage_api_service.ps1` and `stage_api_payload.ps1` parsed with no errors. |
| Service DryRun | ✅ Pass | `manage_api_service.ps1 -AppDir C:\Users\matia\estacionamiento-central-installer -Action DryRun` exited 0; log confirms WinSW and packaged API executable are present. |
| WinSW XML static checks | ✅ Pass | Template uses `{{API_EXE}}`, `Automatic`, three restart-on-failure entries, and contains no `python`, `uvicorn`, or `--reload`. |
| Update strategy static checks | ✅ Pass | No WinSW `refresh` command remains; script uses existing service detection, WinSW `uninstall`, `Wait-ForServiceRemoval`, WinSW `install`, and WinSW `start`. |
| WinSW logging static checks | ✅ Pass | `Invoke-WinSW` redirects stdout/stderr, logs command/exit code/stdout/stderr, and redacts secret-like values. |
| Payload exclusions | ✅ Pass | No `.venv`, `.env`, logs, locks, tests, caches, `printer_agent`, or `print_out` found under `payload\api`; payload executable and manifest are present. |
| Task boundary | ✅ Pass | `tasks.md` marks Slice 1 and Slice 2 tasks complete; Slice 3 and later tasks remain unchecked. |

### Final Verdict

PASS — Slice 2 satisfies the production-deployment requirements in scope for API service install/update/start/stop/uninstall/rollback with data/log preservation. Earlier incident history remains below for traceability: non-relocatable `.venv`, WindowsApps Python alias, PyInstaller strategy migration, clean replacement correction, and WinSW `refresh` replacement were all resolved before final acceptance.

## Historical Verification Log

The sections below are preserved incident history and earlier verification snapshots. Any older `FAIL`, `UNTESTED`, missing-payload, Python/venv, or WinSW `refresh` statements are superseded by the final acceptance evidence above and by the corrective notes dated after those incidents.

## Slice 3 Print Agent WinSW Final-Path Correction — 2026-06-28

**Scope**: ONLY the approved Slice 3 correction for Print Agent WinSW XML generated from a temporary staging path. Slice 4 was not started.

**Incident evidence**: Installer completed and `EstacionamientoCentralPrintAgent` service existed but stayed stopped. `print-agent-service.log` said WinSW install/start completed successfully, while the WinSW wrapper log showed it tried to launch `{app}\tmp\print-agent-service-staging\print-agent\EstacionamientoCentralPrintAgent.exe` with the staging working directory, then failed with file not found. The correct final executable path is `{app}\print-agent\EstacionamientoCentralPrintAgent.exe`.

**Correction applied**:
- `scripts\manage_print_agent_service.ps1` now writes the WinSW XML into the staging directory while its contents reference final installed paths: `{app}\print-agent\EstacionamientoCentralPrintAgent.exe`, `{app}\print-agent`, `{app}\print-agent\.env`, and `{app}\logs\print-agent-service`.
- Added `Assert-ServiceXmlUsesFinalPaths` so generated XML fails validation if it contains `tmp\print-agent-service-staging`, lacks the final print-agent executable path, or lacks the intended service log path.
- DryRun now renders the service XML and runs the same final-path assertion without installing or starting a Windows service.

**Validation added**:
- PowerShell parser check passed for `scripts\manage_print_agent_service.ps1`.
- `scripts\manage_print_agent_service.ps1 -AppDir C:\Users\matia\estacionamiento-central-installer -Action DryRun` passed.
- Static checks confirmed the template keeps stable service id/name placeholders, `Automatic` startup, three restart-on-failure entries, direct packaged executable execution, and no dev launcher/Python path.
- Static guard check confirmed the script no longer rewrites XML path variables to staging before rendering and includes the final-path assertion.
- Payload exclusion check passed: no `.env`, logs, locks, `__pycache__`, `tests`, or `print_out` paths were found under `payload\print-agent`.

**Remaining manual validation**: Recompile the installer after this correction, then rerun the controlled admin/VM install or reinstall. Confirm the generated installed XML under `{app}\print-agent` references `{app}\print-agent\EstacionamientoCentralPrintAgent.exe` and not `{app}\tmp\print-agent-service-staging`, the service reaches `Running`, logs write under `{app}\logs\print-agent-service`, queued print jobs print exactly once after reboot, reinstall/update does not double-print, and uninstall/rollback remove only the owned service while preserving queue/data/logs.

## Slice 3 SumatraPDF Production Configuration Correction — 2026-06-28

**Scope**: ONLY the approved Slice 3 correction for Print Agent SumatraPDF production configuration. Slice 4 was not started.

**Incident evidence**: The Print Agent service installed and reached `Running`, but the VM had no SumatraPDF installation. Print Agent logs showed the old developer default path `C:\Users\matia\AppData\Local\SumatraPDF\SumatraPDF.exe`, and the installer-generated `print-agent.env`/WinSW XML did not pass `SUMATRA_PATH`.

**Correction applied**:
- `scripts\write_production_config.ps1` now writes `SUMATRA_PATH={app}\tools\SumatraPDF\SumatraPDF.exe` by default into `config\print-agent.env` and records the same value in `production.json`.
- `payload\print-agent\EstacionamientoCentralPrintAgent.xml.template` now passes `SUMATRA_PATH` to the service process.
- `scripts\manage_print_agent_service.ps1` renders the configured SumatraPDF path into XML, reports it during `DryRun`, rejects developer-local SumatraPDF paths in generated XML, and fails `InstallOrUpdate` before service mutation if the configured executable is missing.
- API Print Agent code no longer defaults to the developer-local SumatraPDF path; dev/manual runs must provide `SUMATRA_PATH` explicitly.
- No portable `SumatraPDF.exe` was found in the installer workspace or payload. `tools\SumatraPDF\README.md` was added as a placeholder/instruction file; no internet download was performed.

**Validation added**:
- API tests passed after the Print Agent default/config behavior change: `python -m unittest discover -s tests` ran 23 tests successfully.
- PowerShell parser checks passed for `scripts\write_production_config.ps1` and `scripts\manage_print_agent_service.ps1`.
- Temporary config generation proved `config\print-agent.env` includes `SUMATRA_PATH` pointing to `tools\SumatraPDF\SumatraPDF.exe`, and `production.json` includes `sumatraPath`.
- `scripts\manage_print_agent_service.ps1 -AppDir C:\Users\matia\estacionamiento-central-installer -Action DryRun` passed and logged the configured SumatraPDF path without requiring the executable.
- Static checks confirm the WinSW XML template includes `SUMATRA_PATH`, and installer scripts/templates no longer contain the old developer-local SumatraPDF path outside historical verification notes.

**Remaining manual validation**: Place the approved portable `SumatraPDF.exe` at installer `tools\SumatraPDF\SumatraPDF.exe`, compile the Inno Setup installer again, and rerun the controlled admin/VM install or reinstall. Confirm `{app}\config\print-agent.env` and the installed WinSW XML pass `SUMATRA_PATH={app}\tools\SumatraPDF\SumatraPDF.exe`, the service reaches `Running`, queued print jobs print exactly once after reboot, and reinstall/update still does not double-print.

## Completeness

| Metric | Value |
|---|---:|
| Tasks total | 12 |
| Slice 1 tasks complete | 2/2 |
| Slice 2 tasks complete | 2/2 marked complete |
| Later-slice tasks complete | 0 |
| Tasks incomplete | 8 |

`tasks.md` marks only Phase 1 tasks 1.1/1.2 and Phase 2 tasks 2.1/2.2 complete. Phases 3-6 remain unchecked, as required for Slice 2 scope discipline.

## Validation Performed

| Check | Result | Evidence |
|---|---|---|
| Required artifacts read | ✅ Pass | Proposal, design, both delta specs, tasks, previous verify report, apply-progress Engram #149 |
| Slice 1 evidence preservation | ✅ Pass | Previous Slice 1 parser/smoke/diagnostics/manual ISCC evidence retained in this cumulative report |
| PowerShell parser check | ✅ Pass | `manage_api_service.ps1` parsed with no errors via `System.Management.Automation.Language.Parser.ParseFile` |
| API service DryRun smoke | ✅ Pass | Temp `{app}` with `config\api.env` and XML template returned exit 0; log recorded host `0.0.0.0`, port `8123`, WinSW/Python absent as expected for dry run |
| WinSW XML static checks | ✅ Pass | Valid XML; service id/name placeholders; automatic start; 3 restart-on-failure entries; log path placeholder; Uvicorn command has no `--reload` |
| Installer wiring static checks | ✅ Pass | `.iss` includes `manage_api_service.ps1`, `assets\winsw\*`, `payload\api\*`, API dirs, install action, uninstall action |
| Manual Inno Setup compile | ✅ Pass by user evidence | User manually compiled `EstacionamientoCentral.iss` with Inno Setup after Slice 2 and reported no errors. `ISCC.exe` is not on PATH locally. |
| Manual API launcher preservation | ✅ Pass | `C:\Users\matia\estacionamiento-central-api\run.ps1` still exists and remains a dev/manual launcher using `--reload`; service XML/script do not call it |
| Forbidden scope creep | ✅ Pass | No mobile changes; API repo only shows runtime lock file `printer_agent/logs/print_agent.lock`; no Print Agent lifecycle, firewall automation, slow logs, DB schema/index changes introduced by Slice 2 |
| Runtime API service install/start/health/reboot | ❌ Not proven | No local service installation was performed; `assets\winsw\EstacionamientoCentralAPI.exe` and real API payload/runtime are not present in the installer tree |

## Build & Tests Execution

**Build**: ✅ Installer compile accepted from manual user evidence.

```text
User manually compiled EstacionamientoCentral.iss with Inno Setup after Slice 2 and reported no errors.
Verifier did not run ISCC.exe because it is not on PATH.
```

**Tests / executable checks**: ⚠️ Static and dry-run checks passed; runtime service behavior not proven.

```text
Parser OK: manage_api_service.ps1
DryRun OK; api-service.log recorded API host=0.0.0.0 port=8123; WinSW present=False; Python payload present=False.
WinSW XML static checks: id placeholder, Automatic start, restart policy, log path, no --reload, uvicorn command all passed.
Installer wiring static checks: service script/assets/payload/install/uninstall entries all passed.
```

**Coverage**: ➖ Not available. Installer scripts have no detected coverage runner; no Desktop/API/Mobile product code was changed.

## Spec Compliance Matrix

| Requirement | Slice scenario/evidence | Result |
|---|---|---|
| Installer-Orchestrated Deployment | Existing `EstacionamientoCentral.iss` extended; no replacement installer introduced | ✅ COMPLIANT |
| Central Production Configuration | Slice 1 generated central config files and backups; Slice 2 consumes `{app}\config\api.env` | ✅ COMPLIANT for Slices 1-2 |
| Redacted Diagnostics Bundle | Slice 1 diagnostics bundle/redaction smoke passed | ✅ COMPLIANT for Slice 1 scaffold |
| Data-Safe Deployment Operations | Slice 2 stops/removes only `EstacionamientoCentralAPI`; no DB/schema/mobile/Print Agent lifecycle changes | ✅ COMPLIANT for Slice 2 scope |
| API Windows Service Lifecycle — no `--reload` and service metadata | WinSW XML command uses `.venv\Scripts\python.exe -m uvicorn app.main:app --host {{API_HOST}} --port {{API_PORT}}`; no `--reload` | ✅ COMPLIANT statically |
| API Windows Service Lifecycle — API survives reboot | No runtime install/reboot/health validation; production WinSW exe and API payload/runtime are absent | ❌ UNTESTED / NOT RELEASE-READY |
| API Windows Service Lifecycle — safe rollback | Script backs up API dir and preserves logs; uninstall/rollback stop/remove owned service only | ⚠️ PARTIAL: rollback does not automatically restore prior payload/env despite design/task wording |
| Print Agent service, Firewall, Health, Slow logs, Mobile guidance | Not in Slice 2 | ➖ Not evaluated in this verify scope |

**Compliance summary for Slice 2 API service scenarios**: 1/3 fully compliant; 1 partial; 1 untested.

## Correctness (Static Evidence)

| Requirement | Status | Notes |
|---|---|---|
| Stable service identity | ✅ Implemented | `$ServiceId = EstacionamientoCentralAPI`; display name `Estacionamiento Central API` |
| Production service command avoids dev launcher | ✅ Implemented | Service XML calls Python/Uvicorn directly; does not call `run.ps1`; template has no `--reload` |
| Logs available | ✅ Implemented | Installer log `{app}\logs\installer\api-service.log`; WinSW log path `{app}\logs\api-service` with roll-by-size policy |
| Automatic startup and restart | ✅ Implemented statically | XML has `<startmode>Automatic</startmode>` and three restart `onfailure` entries |
| Install/update ownership | ✅ Implemented statically | Script stops owned service, backs up API dir, copies payload/env/WinSW, install/refresh/start, then health-checks |
| Uninstall safety | ✅ Implemented | Stops/removes only `EstacionamientoCentralAPI`; logs preserved |
| Rollback restore | ⚠️ Partial | Rollback stops/removes service and tells operator to restore backup manually; it does not restore prior payload/env automatically |
| Production payload completeness | ❌ Missing for release | `payload\api` currently contains README + XML template only; WinSW executable is intentionally not vendored |

## Coherence (Design)

| Design decision | Followed? | Notes |
|---|---|---|
| Extend existing Inno Setup installer | ✅ Yes | `.iss` adds API service assets/script wiring only |
| WinSW-managed API service | ⚠️ Partial | WinSW service config and manager script exist; executable must be supplied before real install |
| Service command with no `--reload` | ✅ Yes | Static XML/script checks passed |
| Preserve manual `run.ps1` fallback | ✅ Yes | API repo launcher remains unchanged and service path does not depend on it |
| Logs under `{app}\logs\api-service` | ✅ Yes | XML and directory wiring present |
| Stop/remove only owned service on uninstall | ✅ Yes | Service id is stable and scoped |
| Restore prior env/payload backup on rollback | ⚠️ Partial | Backups are created, but rollback action only logs manual restore guidance |
| Minimum-intervention slice boundary | ✅ Yes | No Print Agent lifecycle, firewall, slow logs, mobile, or DB/schema implementation found |

## TDD Compliance

Strict TDD mode is active for Desktop/API/Mobile product code. Slice 2 modified installer/API packaging and service scripts only, not API product behavior. No product-code test files were expected or changed. Because the Slice 2 core service behavior has no safe local automated runner and no runtime install/reboot evidence, the compliance gap is reported as runtime validation missing rather than TDD protocol failure for product code.

| Check | Result | Details |
|---|---|---|
| TDD Evidence reported | ➖ N/A | Apply-progress #149 reports installer/service validation evidence, not product-code TDD cycles |
| All product tasks have tests | ➖ N/A | No Desktop/API/Mobile product behavior touched |
| RED/GREEN confirmed | ➖ N/A | No product tests changed |
| Service behavior confirmed | ❌ No | Static/dry-run passed, but install/start/reboot/health did not run |
| Safety net for modified files | ⚠️ Partial | Safe local parser/static/dry-run checks executed; no full production service smoke |

## Test Layer Distribution

| Layer | Tests/checks | Files | Tools |
|---|---:|---:|---|
| PowerShell parser/static | 1 parser check | 1 | PowerShell parser |
| Installer/service dry-run | 1 dry-run smoke | 1 | PowerShell execution |
| XML/installer static checks | 2 static checks | 2 | PowerShell/XML parse/string checks |
| Desktop/API/Mobile product tests | 0 | 0 | Not run; product behavior untouched |

## Changed File Coverage

Coverage analysis skipped — no coverage tool detected for installer scripts.

## Assertion Quality

No test files were created or modified for this slice; assertion quality audit is not applicable.

## Quality Metrics

**Linter**: ➖ Not available for installer scripts.
**Type Checker**: ➖ Not available for installer scripts.

## Issues Found

**CRITICAL**:
- Runtime API service lifecycle is not proven. The Slice 2 core scenario “API survives reboot” has no passing runtime evidence, and the installer tree currently lacks the approved WinSW executable plus real API payload/runtime required for `InstallOrUpdate` to succeed on a production machine.

**WARNING**:
- Rollback is only partially automated: `Rollback` stops/removes the owned service and preserves backups/logs, but does not restore prior payload/env automatically as described by the design/task rollback wording.
- The WinSW executable is intentionally absent (`assets\winsw\EstacionamientoCentralAPI.exe` must be supplied before release). This is acceptable for source control hygiene but must be closed before production installer validation.
- API repo working tree still contains a modified runtime lock file: `printer_agent/logs/print_agent.lock`. It is not Slice 2 product behavior, but it should not be included in a PR/commit.

**SUGGESTION**:
- Add a non-destructive Pester-style harness for `manage_api_service.ps1` to verify XML rendering, backup selection, rollback restore behavior, and command selection without installing a service.
- For final Slice 2 acceptance, run a controlled VM/manual checklist with WinSW + API payload staged: install, health, reboot, reinstall/update, uninstall, rollback, and log inspection.

## Risks

- A compiled installer can still fail during install if `assets\winsw\EstacionamientoCentralAPI.exe` or `.venv\Scripts\python.exe` is absent from the staged payload.
- Service account/environment differences may only appear during real WinSW execution, not during DryRun.
- Later slices still carry unreduced production-readiness risks: Print Agent lifecycle, firewall idempotency, full health checks, slow-log instrumentation, and mobile/Desktop guidance.

## Final Verdict

FAIL — Slice 2 is well-scoped and its static/dry-run checks pass, but the API Windows Service lifecycle is not production-verified yet. The implementation should not be treated as release-ready until the WinSW executable/API payload are staged and install/start/health/reboot/rollback evidence is captured.

## Corrective Apply Notes — 2026-06-26

**Scope**: ONLY Slice 2 / API WinSW Service Deployment critical verification gaps. Slice 3 was not started.

**Correction applied**:
- Added `scripts/stage_api_payload.ps1` to stage the real FastAPI source payload from `C:\Users\matia\estacionamiento-central-api` into installer `payload\api` with exclusions for `.env`, `.git`, `.venv` by default, logs, `print_out`, `printer_agent`, tests, `__pycache__`, bytecode, and lock files.
- Generated `payload\api\API_PAYLOAD_MANIFEST.json` proving `app\main.py`, `requirements.txt`, and `run.ps1` are staged while `python_runtime_present=false` remains explicit.
- Updated `scripts/manage_api_service.ps1` dry-run/install validation so incomplete payload, missing runtime, and missing WinSW fail clearly before service installation.
- Updated rollback so `Rollback` stops/removes only `EstacionamientoCentralAPI` and restores the latest backed-up API payload/env when available.
- Wired `scripts\stage_api_payload.ps1` into the installer file list and updated API/WinSW README guidance.

**Validation added**:
- PowerShell parser checks pass for `manage_api_service.ps1` and `stage_api_payload.ps1`.
- `stage_api_payload.ps1 -Clean` copied 42 API source/runtime-support files and generated the manifest.
- Payload exclusion checks found no `.env`, `.log`, `.lock`, `printer_agent`, or `tests` files under `payload\api`.
- `manage_api_service.ps1 -Action DryRun` passes with staged source payload.
- `manage_api_service.ps1 -Action InstallOrUpdate` fails before service changes with explicit missing prerequisites: `.venv\Scripts\python.exe` and `assets\winsw\EstacionamientoCentralAPI.exe`.

**Remaining release gate**: Runtime service lifecycle remains unproven until an approved local WinSW executable and production API virtual environment are staged, then validated in a controlled admin/VM install with health, reboot, update, uninstall, and rollback evidence.

## Runtime Staging Follow-up — 2026-06-26

**Scope**: ONLY Slice 2 runtime staging prerequisites for a manual Inno Setup compile. Slice 3 was not started.

**Actions attempted**:
- Searched local workspace for `WinSW`/`winsw`/`EstacionamientoCentralAPI.exe`; no plausible local WinSW executable was found, and no download was performed.
- Re-ran `scripts\stage_api_payload.ps1 -Clean`; API source payload was refreshed from `C:\Users\matia\estacionamiento-central-api` and exclusions remained active.
- Confirmed the API `requirements.txt` is UTF-16 encoded and decoded it to a temporary UTF-8 requirements file for tooling compatibility.
- Attempted to create `payload\api\.venv` and install requirements in offline/no-download mode. Dependency installation failed because no local wheel/index source contained `annotated-doc==0.0.4`; the incomplete `.venv` was removed so the payload is not falsely reported as runtime-ready.

**Validation added**:
- PowerShell parser checks pass for `manage_api_service.ps1` and `stage_api_payload.ps1`.
- `manage_api_service.ps1 -Action DryRun` passes with the staged source payload.
- `manage_api_service.ps1 -Action InstallOrUpdate` fails before service mutation with explicit missing prerequisites for `payload\api\.venv\Scripts\python.exe` and `assets\winsw\EstacionamientoCentralAPI.exe`.
- Payload exclusion check passed: no `.env`, logs, lock files, tests, `printer_agent`, `__pycache__`, or runtime outputs were found in `payload\api`; `run.ps1` remains present.

**Current release gate**: Manual installer compile can validate packaging shape only. Production service lifecycle validation remains blocked until the approved WinSW executable and a dependency-complete API `.venv` are staged without violating the no-download constraint.

## Final Slice 2 Runtime-Ready Verification — 2026-06-26

**Scope**: ONLY Slice 2 / API Service Deployment after correction and runtime staging. Slice 3 was not started.

### Result

**Verdict**: PASS WITH WARNINGS for Slice 2 runtime-ready staging.

The installer tree now contains the required WinSW executable path, API source payload, API virtual environment, and manifest evidence. Static parser checks, XML checks, source-payload exclusion checks, and `DryRun` pass. The verifier intentionally did **not** run `InstallOrUpdate` because the script proceeds to stop/install/start the `EstacionamientoCentralAPI` Windows service when prerequisites are present; that lifecycle validation requires an admin/VM manual run.

### Validation Performed

| Check | Result | Evidence |
|---|---|---|
| Required SDD artifacts read | ✅ Pass | Proposal, design, production-deployment spec, production-observability spec, tasks, previous verify report, and apply-progress Engram #149 |
| Expected WinSW executable path | ✅ Pass | `C:\Users\matia\estacionamiento-central-installer\assets\winsw\EstacionamientoCentralAPI.exe` exists by user/manual staging evidence and filesystem check |
| Expected API Python runtime | ✅ Pass | `C:\Users\matia\estacionamiento-central-installer\payload\api\.venv\Scripts\python.exe` exists |
| Expected API service entrypoint | ✅ Pass | `C:\Users\matia\estacionamiento-central-installer\payload\api\app\main.py` exists |
| Expected payload manifest | ✅ Pass | `C:\Users\matia\estacionamiento-central-installer\payload\api\API_PAYLOAD_MANIFEST.json` exists |
| Runtime imports | ✅ Pass | Payload Python imported `fastapi`, `uvicorn`, `sqlalchemy`, `pymysql`, and `pydantic_settings` successfully |
| Manifest runtime flag | ✅ Pass | `python_runtime_present=true` |
| Source payload exclusions | ✅ Pass | Manifest lists exclusions for `.env`, logs, locks, tests, `printer_agent`, and caches; no source-payload violations were found outside `.venv` |
| PowerShell parser checks | ✅ Pass | `scripts\manage_api_service.ps1` and `scripts\stage_api_payload.ps1` parsed with no errors |
| API service DryRun | ✅ Pass | `scripts\manage_api_service.ps1 -AppDir C:\Users\matia\estacionamiento-central-installer -Action DryRun` exited 0 |
| `InstallOrUpdate` safety gate | ✅ Pass / intentionally skipped | Not run because prerequisites are now present and the script would stop/install/start the Windows service |
| WinSW XML service config | ✅ Pass | No `--reload`; ID/name placeholders rendered by script from stable `EstacionamientoCentralAPI` / `Estacionamiento Central API`; `Automatic` startup; three restart-on-failure entries; `{{LOG_DIR}}` logging path; Uvicorn command uses `.venv` Python |
| Manual Inno Setup compile | ✅ Pass by user evidence | User manually compiled the installer successfully after API `.venv` and WinSW were staged |
| Forbidden scope creep | ✅ Pass with note | No Slice 2 evidence of Print Agent lifecycle, firewall automation, slow logs, mobile behavior, or DB schema/index changes. API repo still has local modified `printer_agent/logs/print_agent.lock` and must not be committed. |

### Runtime Command Evidence

```text
EXISTS assets\winsw\EstacionamientoCentralAPI.exe = True
EXISTS payload\api\.venv\Scripts\python.exe = True
EXISTS payload\api\app\main.py = True
EXISTS payload\api\API_PAYLOAD_MANIFEST.json = True
IMPORTS_OK

PARSER_OK scripts\manage_api_service.ps1
PARSER_OK scripts\stage_api_payload.ps1
DRYRUN_EXIT=0

MANIFEST_python_runtime_present=True
MANIFEST_include_venv=False
SOURCE_EXCLUSION_VIOLATIONS=0
VENV_TEST_OR_CACHE_DIRS=231
XML_STARTMODE=Automatic
XML_ONFAILURE_COUNT=3
XML_HAS_RELOAD=False
```

### Spec Compliance Matrix — Slice 2 Final

| Requirement | Slice 2 scenario/evidence | Result |
|---|---|---|
| Installer-Orchestrated Deployment | Existing Inno Setup installer remains owner; runtime assets/payload are staged in installer tree | ✅ COMPLIANT |
| API Windows Service Lifecycle — no `--reload`, service metadata, logs, restart | WinSW template and script configure stable service identity, automatic startup, restart policy, log path, Uvicorn command without `--reload` | ✅ COMPLIANT statically |
| API Windows Service Lifecycle — runtime-ready prerequisites | WinSW executable, API `.venv`, source entrypoint, manifest, and key imports are present/valid | ✅ COMPLIANT for staging |
| API Windows Service Lifecycle — API survives reboot | Requires real Windows service install/start/health/reboot on admin/VM; not run because it mutates service state | ⚠️ MANUAL VALIDATION REMAINS |
| API Windows Service Lifecycle — safe rollback | Script restores latest API backup when available and removes only owned `EstacionamientoCentralAPI` | ✅ COMPLIANT statically / dry-run only |
| Data-Safe Deployment Operations | No destructive DB operation found in Slice 2 checks; owned service scope only | ✅ COMPLIANT for Slice 2 |
| Print Agent, Firewall, Slow logs, Mobile guidance | Later slices; not implemented in Slice 2 | ➖ Not evaluated in this scope |

**Compliance summary for Slice 2 staging scenarios**: 4/4 staging/static scenarios compliant; 1 lifecycle scenario remains manual/VM-only.

### TDD Compliance

Strict TDD mode is active for Desktop/API/Mobile product code. This verification validates packaging/service scripts/runtime staging only. No Desktop/API/Mobile product behavior changes or product test files were part of this Slice 2 runtime staging correction, so product-code TDD checks remain not applicable. Runtime staging is covered by executable filesystem/import/parser/dry-run checks above.

### Issues Found

**CRITICAL**:
- None for Slice 2 runtime-ready staging.

**WARNING**:
- Full Windows service lifecycle remains manual: `InstallOrUpdate`, health, reboot recovery, update/reinstall, uninstall, and rollback must be validated in an admin/VM environment because running it locally would mutate service state.
- The staged `.venv` contains third-party package `tests` and `__pycache__` directories (`VENV_TEST_OR_CACHE_DIRS=231`). Source-payload exclusions still pass, but production packaging can be slimmed later if installer size becomes a problem.
- API repo working tree still contains modified runtime state: `printer_agent/logs/print_agent.lock`; do not include it in commits/PRs.

**SUGGESTION**:
- Add a non-mutating service harness or Pester tests around `manage_api_service.ps1` to validate rendered XML, prerequisite gating, backup selection, and rollback restore without touching Windows services.

### Remaining Manual Validation

- Run installer/service lifecycle in a controlled admin VM: install/update, service start, `/api/v1/health`, reboot recovery, reinstall/update idempotency, uninstall, rollback restore, and log inspection.
- Confirm the manually staged WinSW binary provenance/checksum before release.

### Final Verdict

PASS WITH WARNINGS — Slice 2 is runtime-ready for controlled manual service lifecycle validation. It is not yet end-to-end production-proven until the admin/VM lifecycle checklist passes.

## Slice 2 Runtime Packaging Correction — 2026-06-26

**Scope**: ONLY the confirmed API service runtime packaging defect. Slice 3 was not started.

**Manual incident evidence**: The installer completed and Desktop worked, but `EstacionamientoCentralAPI` stayed stopped. WinSW reported it could not find `C:\Users\matia\AppData\Local\Programs\Python\Python313\python.exe`, proving the bundled Windows `.venv` was non-relocatable through `pyvenv.cfg` developer paths.

**Correction applied**:
- Removed bundled `.venv` as a production artifact and excluded `.venv` from `stage_api_payload.ps1` and Inno packaging.
- Added `scripts\prepare_api_runtime.ps1` to create `{app}\api\.venv` in the final installed location, normalize UTF-16 requirements to UTF-8 for pip, install dependencies, validate imports, and reject developer-path venv metadata.
- Updated `manage_api_service.ps1` so `InstallOrUpdate` copies the source payload/config first, prepares and validates the runtime, then writes WinSW XML and starts the service.
- Updated payload/WinSW guidance to document install-time runtime creation and the accepted temporary internet dependency for pip.

**Remaining release gate**: The user should manually compile the installer again after this correction, then run a controlled admin install. The service lifecycle still needs manual validation because running `InstallOrUpdate` locally mutates Windows service state.

## Slice 2 WindowsApps Python Alias Correction — 2026-06-26

**Scope**: ONLY the confirmed WindowsApps Python alias/runtime-prerequisite false-green failure. Slice 3 was not started.

**Incident evidence**: In a VM/admin install, the installer appeared successful but no `EstacionamientoCentralAPI` service existed, health failed, and `api-runtime.log` showed Python resolving to `C:\Users\vboxuser\AppData\Local\Microsoft\WindowsApps\python.exe` before attempting `-m venv`.

**Correction applied**:
- `scripts\prepare_api_runtime.ps1` now rejects any Python candidate whose path resolves under `Microsoft\WindowsApps`, supports explicit `API_PYTHON_EXE`, and validates candidates by executing Python 3 with `venv` support before accepting them.
- Runtime resolution priority remains `API_PYTHON_EXE` → `py -3` → `python`.
- Failure text now tells operators to install real Python 3, disable the Windows Store App Execution Alias, or set `API_PYTHON_EXE`.
- Installer API service setup now runs through checked Pascal script execution and aborts with log pointers when `manage_api_service.ps1` exits non-zero, avoiding a silent false-green API install.
- Payload README documents the real Python prerequisite and WindowsApps alias rejection.

**Validation added**:
- PowerShell parser checks pass for changed service/runtime scripts.
- `prepare_api_runtime.ps1 -DryRun` passes in the current dev environment with a real Python candidate.
- Non-mutating alias override check rejects an `API_PYTHON_EXE` path containing `Microsoft\WindowsApps` with an actionable prerequisite message.
- `manage_api_service.ps1 -Action DryRun` passes.
- Installer static check confirms API service setup is no longer a hidden `[Run]` entry and non-zero API setup exits are checked in `CurStepChanged`.
- Static payload check confirms no `.venv` is packaged under `payload\api`.

**Remaining manual validation**: Recompile the installer manually after this correction, then rerun the controlled admin/VM install to prove service creation, `/api/v1/health`, logs, reboot recovery, reinstall/update, uninstall, and rollback.

## Slice 2 PyInstaller Runtime Strategy Correction — 2026-06-27

**Scope**: ONLY Slice 2 API runtime strategy correction. Slice 3 was not started.

**Decision applied**: WinSW remains the Windows service wrapper, but it now runs the PyInstaller-packaged API executable directly instead of `python -m uvicorn` or any target-machine/install-time Python virtual environment.

**Correction applied**:
- Added API `service_main.py` as the production executable entrypoint. It runs Uvicorn programmatically with `reload=False` and reads `API_HOST`/`API_PORT` from process env or the installed `.env` file.
- Added PyInstaller build artifacts: `EstacionamientoCentralAPI.spec`, `build_api_exe.ps1`, and compatibility wrapper `build_api_executable.ps1`.
- Installed missing API runtime dependencies from `requirements.txt` using controlled pip and rebuilt the PyInstaller `onedir` distribution.
- Re-staged installer `payload\api` from `dist\EstacionamientoCentralAPI`; manifest now records `packaging=pyinstaller-onedir`, `api_executable_present=true`, and `install_time_runtime_required=false`.
- Updated/validated WinSW XML and `manage_api_service.ps1` so the service executable is `{{API_EXE}}` / `{app}\api\EstacionamientoCentralAPI.exe`, with no Python, Uvicorn command, `.venv`, or `--reload` in the main path.
- Kept `prepare_api_runtime.ps1` only as deprecated fallback; it is no longer copied by the installer nor called by the service manager.
- Updated `design.md` so the active Slice 2 architecture matches the PyInstaller executable strategy instead of the earlier venv/Uvicorn command.

**Validation added**:
- `python -m pip show pyinstaller` confirmed PyInstaller 6.16.0; missing API requirements, including `PyMySQL`, were installed from decoded UTF-16 `requirements.txt` before the final build.
- `build_api_executable.ps1 -Clean` completed successfully and produced `dist\EstacionamientoCentralAPI\EstacionamientoCentralAPI.exe`.
- Executable smoke passed: started the packaged exe on `127.0.0.1:8124` and `GET /api/v1/health` returned `{"status":"ok"}`; process was stopped afterwards.
- API tests passed: `python -m unittest discover -s tests` ran 21 tests successfully.
- PowerShell parser checks passed for `manage_api_service.ps1`, `stage_api_payload.ps1`, `build_api_exe.ps1`, and `build_api_executable.ps1`.
- `scripts\manage_api_service.ps1 -AppDir C:\Users\matia\estacionamiento-central-installer -Action DryRun` exited 0.
- XML static check passed: template executable is `{{API_EXE}}`, start mode is `Automatic`, restart-on-failure count is 3, and no `python`, `uvicorn`, or `--reload` command is present.
- Payload exclusion check passed: no `.env`, logs, locks, tests, `printer_agent`, `print_out`, `.venv`, or `__pycache__` paths were found under staged `payload\api`.
- `ISCC.exe` is not on PATH locally, so final installer compilation remains manual.

**Remaining manual validation**: User should manually compile the Inno Setup installer again, then run controlled admin/VM service lifecycle validation: install/update, service start, `/api/v1/health`, reboot recovery, reinstall/update idempotency, uninstall, rollback restore, and log inspection.

## Slice 2 Reinstall/Update Replacement Correction — 2026-06-27

**Scope**: ONLY the confirmed API service reinstall/update failure after the PyInstaller fresh-install path passed. Slice 3 was not started.

**Incident evidence**: Fresh install with PyInstaller + WinSW reached service `Running`, `/api/v1/health` HTTP 200, logs OK, and reboot check OK. Reinstall/update still failed during installer API setup, consistent with in-place overlay of `{app}\api` after service stop while WinSW/PyInstaller executable or DLL handles may still be closing.

**Correction applied**:
- `scripts\manage_api_service.ps1` now stages the new API payload into `{app}\tmp\api-service-staging\api` first.
- The staged API directory receives the packaged payload, copied WinSW service wrapper, generated `.env`, and generated WinSW XML before replacing the live `{app}\api` directory.
- Existing installs stop only the owned `EstacionamientoCentralAPI` service, log service state, wait/retry for lingering processes whose executable path is under `{app}\api`, back up the current API directory, then replace `{app}\api` cleanly using retry/backoff for copy/remove/move operations.
- Logs/data/config/report directories remain outside `{app}\api` and are not deleted by the replacement flow.
- `EstacionamientoCentral.iss` no longer points operators to deprecated `logs\installer\api-runtime.log`; API setup failures now point to `logs\installer\api-service.log` and `logs\api-service\`.

**Validation added**:
- PowerShell parser check passed for `scripts\manage_api_service.ps1`.
- `scripts\manage_api_service.ps1 -Action DryRun` passed; `InstallOrUpdate` was intentionally not run locally because it mutates Windows service state.
- Static checks confirmed the replacement flow uses temporary staging plus retry helpers and no longer overlay-copies `payload\api` directly into `{app}\api`.
- XML static check still confirms the service executes the packaged `EstacionamientoCentralAPI.exe` directly, with no Python, Uvicorn, or `--reload` command.
- Payload exclusion checks remain OK for secrets/logs/locks/tests/cache/runtime-output exclusions.

**Remaining manual validation**: Recompile the Inno Setup installer after this correction, then rerun the admin/VM lifecycle path starting with reinstall/update over the currently working fresh install. Confirm service `Running`, `/api/v1/health` 200, logs, reboot recovery, uninstall, rollback preservation, and no deletion of logs/data/config/report directories.

## Slice 2 WinSW Refresh Correction — 2026-06-27

**Scope**: ONLY the confirmed reinstall/update failure at `Running WinSW command: refresh`. Slice 3 was not started.

**Incident evidence**: Fresh install works with the PyInstaller payload: service reaches `Running`, `/api/v1/health` returns HTTP 200, logs are written, and reboot recovery passes. Reinstall/update fails after clean payload replacement at WinSW `refresh`, indicating `refresh` is too weak/fragile after replacing wrapper/XML/env/PyInstaller payload.

**Correction applied**:
- `scripts\manage_api_service.ps1` now detects whether `EstacionamientoCentralAPI` existed before service stop/replacement.
- Existing updates stop the owned service and run WinSW `uninstall` using the existing wrapper before deleting/replacing `{app}\api`; if the service exists but the wrapper is missing, the script fails explicitly instead of deleting blindly.
- A new wait helper retries until `Get-Service EstacionamientoCentralAPI` is absent before replacing the API directory.
- After clean payload replacement, the script always runs WinSW `install`, then `start`, then the health check; the update path no longer uses `refresh`.
- `Invoke-WinSW` now redirects stdout/stderr, logs command, exit code, stdout, and stderr to `logs\installer\api-service.log`, and redacts secret-like key/value output before logging.
- `design.md` and `tasks.md` were updated to document the uninstall/install update strategy.

**Validation added**:
- PowerShell parser check passed for `scripts\manage_api_service.ps1`.
- `scripts\manage_api_service.ps1 -AppDir C:\Users\matia\estacionamiento-central-installer -Action DryRun` passed.
- Static check passed: `InstallOrUpdate` uses existing-service detection, WinSW `uninstall`, waits for service removal, then always WinSW `install` + `start`; no `refresh` command remains in the script.
- Static check passed: `Invoke-WinSW` captures/logs command, exit code, stdout, and stderr.
- XML static check still confirms the service executes the packaged `EstacionamientoCentralAPI.exe` directly, with no Python, Uvicorn, or `--reload` command.

**Remaining manual validation**: Recompile the Inno Setup installer after this correction, then rerun the admin/VM lifecycle path starting with reinstall/update over the currently working fresh install. Confirm service `Running`, `/api/v1/health` 200, WinSW uninstall/install logs, reboot recovery, uninstall, rollback preservation, and no deletion of logs/data/config/report directories.
