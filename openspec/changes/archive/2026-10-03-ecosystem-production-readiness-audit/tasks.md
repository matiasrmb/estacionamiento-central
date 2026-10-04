# Tasks: Ecosystem Production Readiness Audit

## Review Workload Forecast

| Slice | Est. lines | Risk | PR boundary |
|---|---:|---|---|
| 1 Installer config/diagnostics scaffold | 250-380 | Medium | Installer only |
| 2 API WinSW service deployment | 350-550 | High | Installer + API |
| 3 Print Agent service lifecycle | 300-500 | High | Installer + Print Agent |
| 4 Firewall + health checks | 250-420 | Medium/High | Installer + API/mobile guidance |
| 5 Slow logs + diagnostics completion | 350-650 | High | Desktop/API/Print Agent/Installer |
| 6 Mobile/Desktop production guidance | 120-260 | Low | Mobile + Desktop docs/config |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

Recommended strategy: ask before apply; prefer feature-branch-chain because this spans sibling repos and installer integration should be validated before main release. Use stacked-to-main only if each slice can ship independently.

## Validation Ground Rules

- Desktop/API: write failing tests first where code has automated runners; run `python -m unittest discover -s tests` in affected repo.
- Mobile: write/update widget/unit tests first when behavior changes; run `flutter test` and `flutter analyze`.
- Installer: no runner detected; each installer task MUST add documented manual validation evidence unless a harness is added.
- Do NOT add DB indexes or schema tuning until slow-log measurements prove the query, cardinality, and before/after benefit.

## Phase 1: Installer Foundation / Slice 1

- [x] 1.1 Goal: config backup/generation scaffold; Files: `EstacionamientoCentral.iss`, `scripts/write_app_config.bat`, new `scripts/write_production_config.ps1`; Deps: none; Validation: manual fresh/upgrade config backup; Rollback: restore backup folder; Touches: Installer/Desktop/API/Print Agent/Mobile guidance.
- [x] 1.2 Goal: installer logs/diagnostics skeleton; Files: new `scripts/collect_diagnostics.ps1`, `{app}\logs\installer` wiring; Deps: 1.1; Validation: generated bundle redacts secret-like keys; Rollback: remove script/menu entry; Touches: Installer.

## Phase 2: API Service Deployment / Slice 2

- [x] 2.1 Goal: vendor WinSW/API payload layout; Files: `assets/winsw/*`, `payload/api/*`, `EstacionamientoCentral.iss`; Deps: 1.1; Validation: installer build includes assets; Rollback: preserve manual `run.ps1`; Touches: Installer/API.
- [x] 2.2 Goal: install/update/rollback `EstacionamientoCentralAPI`; Files: new `scripts/manage_api_service.ps1`, WinSW XML/env template, API prod config path; Deps: 2.1; Validation: reboot + `/api/v1/health`, logs written, no `--reload`; Rollback: stop/remove owned service, restore env/payload; Touches: Installer/API.

Correction note (2026-06-26): Slice 2 verification gap was addressed without starting Slice 3. Added safe API payload staging from `estacionamiento-central-api`, generated `API_PAYLOAD_MANIFEST.json`, kept `.env`/logs/cache/lock files out of installer payload, added explicit prerequisite failure for missing WinSW/runtime, and automated latest API payload/env restore during rollback. Runtime service install/start/reboot remains manual/VM validation until an approved local WinSW executable and production `.venv` are staged.

Runtime packaging correction (2026-06-26): Manual validation found the staged `payload\api\.venv` was non-relocatable because `pyvenv.cfg` referenced the developer Python under `C:\Users\matia`. Slice 2 now excludes bundled `.venv` from staging/packaging and creates `{app}\api\.venv` at install time via `scripts\prepare_api_runtime.ps1` after copying the API payload and before writing/starting WinSW. This controlled pip download is accepted for now; a future wheelhouse/portable runtime would reduce install-time internet risk.

WindowsApps Python alias correction (2026-06-26): Fresh admin/VM validation proved the installer could appear successful while runtime preparation resolved `python.exe` to the Windows Store App Execution Alias under `Microsoft\WindowsApps`, so no `EstacionamientoCentralAPI` service was installed and health failed. Slice 2 correction now rejects WindowsApps alias paths, validates `API_PYTHON_EXE`/`py -3`/`python` by executing Python 3 with `venv` support, and surfaces API service setup failure through installer code instead of silently allowing a false-green install. Slice 3 remains unstarted.

PyInstaller runtime strategy correction (2026-06-27): User and architect selected PyInstaller as the preferred API service runtime. Slice 2 now builds `EstacionamientoCentralAPI.exe` from a dedicated API `service_main.py`, stages the PyInstaller `onedir` distribution into installer `payload\api`, and updates WinSW/service management so the service executes the packaged API executable directly. The main service path no longer calls target-machine Python, `python -m uvicorn`, install-time `.venv`, or `--reload`; `prepare_api_runtime.ps1` is retained only as deprecated fallback and is not wired into `manage_api_service.ps1`. Slice 3 remains unstarted.

Reinstall/update correction (2026-06-27): VM evidence proved fresh PyInstaller service installs work, but reinstall/update can fail when `{app}\api` is overlay-copied after service stop while executable/DLL handles linger. Slice 2 correction now stages the new API payload into a temporary directory, copies WinSW/env/XML into that staged directory, logs service status and lingering process PIDs/paths, backs up the current `{app}\api`, waits for owned processes under `{app}\api` to exit, and replaces `{app}\api` cleanly with retry/backoff instead of overlay-copying. Logs/data/config/report directories remain outside `{app}\api` and are preserved. The installer error message now points to `logs\installer\api-service.log` and `logs\api-service\`; deprecated `api-runtime.log` guidance was removed. Slice 3 remains unstarted.

WinSW refresh correction (2026-06-27): Manual reinstall/update evidence showed the staged replacement path still failed at `Running WinSW command: refresh` after clean payload replacement. Slice 2 now treats update as uninstall/install for the owned service: detect service presence before replacement, stop the owned service, run WinSW `uninstall` with the existing wrapper before deleting `{app}\api`, wait until `EstacionamientoCentralAPI` is absent, replace the staged payload cleanly, then always run WinSW `install` and `start`. `Invoke-WinSW` now logs command, exit code, stdout, and stderr to `logs\installer\api-service.log` with secret-like values redacted. Slice 3 remains unstarted.

## Phase 3: Print Agent Lifecycle / Slice 3

- [x] 3.1 Goal: installer-owned `EstacionamientoCentralPrintAgent`; Files: `scripts/manage_print_agent_service.ps1`, agent launcher/env templates, `EstacionamientoCentral.iss`; Deps: 1.1; Validation: VM/admin evidence proves fresh install, service `Running`, reboot recovery, Sumatra production path config, uninstall preservation, and one controlled DB job consumed exactly once into the expected `ERROR` retry boundary; Rollback: stop/remove owned service only; Touches: Installer/Print Agent/API DB queue. Hardware caveat: physical thermal print success remains unproven because the VM uses Microsoft Print to PDF / lacks the real printer.
- [x] 3.2 Goal: duplicate-agent prevention; Files: `printer_agent/run_agent_forever.ps1` or service wrapper config; Deps: 3.1; Validation: reinstall/update with and without DB preservation produced no duplicate Print Agent service and the controlled job was not double-processed; Rollback: restore previous launcher semantics; Touches: Print Agent/Installer.

Correction note (2026-06-28): Manual Slice 3 validation found `EstacionamientoCentralPrintAgent` was created but stopped because the generated WinSW XML pointed at temporary staging paths under `{app}\tmp\print-agent-service-staging\print-agent` instead of final `{app}\print-agent`. The corrective apply updated `scripts\manage_print_agent_service.ps1` so XML generated into staging contains final installed executable, working directory, env, and service-log paths; DryRun now renders and validates XML fails if `tmp\print-agent-service-staging` appears. This incident is superseded by the final Slice 3 validation evidence below.

Correction note (2026-06-28): Manual Slice 3 validation then showed the VM had no SumatraPDF installed and the Print Agent fell back to the old developer default path. The corrective apply now generates `SUMATRA_PATH={app}\tools\SumatraPDF\SumatraPDF.exe` in `config\print-agent.env`, passes `SUMATRA_PATH` through the WinSW XML, fails `InstallOrUpdate` clearly when the configured SumatraPDF executable is missing, and removes the API Print Agent's developer-local default. Portable SumatraPDF is now staged under `tools\SumatraPDF\SumatraPDF.exe`. Final manual VM/admin validation proved service lifecycle, reboot survival, reinstall/update idempotency, uninstall data/log preservation, and one controlled print job consumed exactly once into the expected hardware-boundary `ERROR` state (`intentos=1`, `locked_by=NULL`, Sumatra rc=1). Tasks 3.1 and 3.2 are complete with a hardware caveat: physical thermal print success remains dependent on validating against the real printer.

## Phase 4: Firewall and Health / Slice 4

- [x] 4.1 Goal: idempotent API firewall rule; Files: new `scripts/manage_firewall_rule.ps1`, `.iss`; Deps: 2.2; Validation: user-provided admin/VM evidence proves fresh install and reinstall/update executed correctly, production health reported the firewall rule allows inbound TCP private-profile traffic for port 8000, and `@(Get-NetFirewallRule -Group "Estacionamiento Central").Count` returned `1`; Rollback: remove only owned rule; Touches: Installer/API/Mobile. Local parser/SelfTest/DryRun/static validation was rerun on 2026-06-28.
- [x] 4.2 Goal: production health checklist; Files: `scripts/check_production_health.ps1`, API safe health additions if needed; Deps: 2.2, 3.1, 4.1; Validation: user-provided admin/VM health output passed API service, API HTTP 200 health endpoint, MySQL service/port, Print Agent service, firewall rule, SumatraPDF path, and Print Spooler; printer availability correctly remained WARN because `PRINTER_NAME` is not configured while one printer was detected; Rollback: disable health gate, keep warnings; Touches: Installer/API/Print Agent. Local parser/DryRun/static validation was rerun on 2026-06-28.

Correction note (2026-06-28): Manual reinstall/update evidence found the firewall update path failed after a successful fresh install, while rollback correctly removed the owned rule. Slice 4 correction now avoids fragile in-place firewall mutation: `manage_firewall_rule.ps1` treats an existing exact owned rule with the desired enabled inbound allow Private TCP port state as an idempotent no-op, and removes/recreates only owned DisplayName+Group rules when mismatched or duplicated. `check_production_health.ps1` now validates direction/action/profile in addition to enabled/protocol/port. At the time, tasks 4.1 and 4.2 remained unchecked until the next admin VM install/reinstall confirmed the fix.

Correction note (2026-06-28): Follow-up incident evidence showed the created owned firewall rule already had the desired values (`enabled=True`, `direction=Inbound`, `action=Allow`, `profile=Private`, `protocol=TCP`, `local_port=8000`) but `Assert-OwnedRuleIsNarrow` still rejected it. The validator now normalizes boolean-ish, enum/string, profile, protocol, and scalar/array local-port values before comparison, keeps the strict Private/TCP/exact-port requirements, and adds a non-mutating `SelfTest` action with the reported mock values. At the time, tasks 4.1 and 4.2 remained unchecked pending real admin VM reinstall/update validation.

Final validation note (2026-06-28): User-provided admin/VM evidence after the idempotency and validator corrections proves Slice 4 complete. Fresh install and reinstall/update both executed correctly; production health reported PASS for API service, API `/api/v1/health` HTTP 200, MySQL service, MySQL `127.0.0.1:3306`, Print Agent service, owned firewall rule for inbound TCP private-profile port 8000, SumatraPDF at `C:\EstacionamientoCentral\tools\SumatraPDF\SumatraPDF.exe`, and Print Spooler. Printer availability correctly reported WARN because `PRINTER_NAME` is not configured while one printer exists. The firewall group count returned `1`, proving no duplicate owned firewall rule after reinstall/update. Slice 5 remains unstarted.

## Phase 5: Observability / Slice 5

- [x] 5.1 Goal: threshold slow logs; Files: API `app/main.py`, `app/db/database.py`, `app/core/slowlog.py`, Desktop `utils/slowlog.py` plus registration/exit/dashboard/table/PDF/print decorators, API `printer_agent/agent.py`; Deps: health paths stable; Validation: API/Desktop synthetic slow tests prove one safe log, fast path quiet, and threshold `0` disables; API full suite passed 26 tests; Desktop full suite passed 102 tests; Rollback: config/env threshold disables; Touches: Desktop/API/Print Agent.
- [x] 5.2 Goal: complete diagnostics bundle; Files: `scripts/collect_diagnostics.ps1`, `scripts/write_production_config.ps1`; Deps: 5.1; Validation: PowerShell parser passed, temp config generation emitted observability thresholds, diagnostics bundle included logs/config/service/log-path metadata and redacted `password`/`token` test secrets; Rollback: remove command; Touches: Installer/Desktop/API/Print Agent.

Slice 5 validation note (2026-06-28): Slow logging remains threshold-only and safe-context only. Defaults are API request `1000ms`, API DB `500ms`, Desktop `1000ms`, Print Agent `3000ms`; setting the generated/env threshold to `0` disables that channel. No DB indexes, schema changes, firewall mutations, mobile/Desktop production guidance, or product features were added.

Final Slice 5 validation note (2026-06-28): User-provided admin/VM evidence after compiling the installer proves fresh install and reinstall both executed without problems; diagnostics zips exist under `C:\EstacionamientoCentral\diagnostics`; each bundle includes `config`, `logs`, `metadata`, and root `metadata.json`; generated `api.env`, `print-agent.env`, and `production.json` include the slow-log thresholds and redact database passwords in diagnostics output. User also searched installed logs with `Select-String -Path "C:\EstacionamientoCentral\logs\**\*.log" -Pattern "SLOW|slow" -ErrorAction SilentlyContinue` and got no matches, confirming no noisy slow-log spam during normal operation. Slice 5 is complete. Slice 6 remains unstarted.

## Phase 6: Minimal Client Guidance / Slice 6

- [x] 6.1 Goal: remove production dev-IP dependency; Files: mobile `lib/core/config.dart`, `server_settings_screen.dart`; Deps: 2.2/4.1; Validation: QR/manual URL works, no release fallback to dev IP; Rollback: keep manual server settings; Touches: Mobile/API. Slice 6 validation added `test/core/config_test.dart`; `flutter test` passed 3 tests and `flutter analyze` reported no issues. Mobile copy now references the installed API service/server instead of `run.ps1`.
- [x] 6.2 Goal: desktop/API compatibility docs and no speculative tuning; Files: `README.md`, deployment notes, maybe `docs/performance_baseline.md`; Deps: 5.1; Validation: docs match clean install; Rollback: revert docs only; Touches: Desktop/API/Installer. Slice 6 docs now describe the validated installer flow: API service, Print Agent service, firewall, health, diagnostics, Sumatra path, mobile guidance, printer hardware caveat, and no speculative tuning without baseline/slow-log evidence.
