# Ecosystem production readiness audit

Read-only SDD exploration for `ecosystem-production-readiness-audit`. Scope covers FASE 0 through FASE 4 only; no product code was changed.

## Exploration: ecosystem production readiness audit

### Current State

The ecosystem is split across four sibling repos:

| Area | Repo | Current role |
|---|---|---|
| Desktop | `C:\Users\matia\estacionamiento-central` | PySide6/MySQL desktop app, local reports/tickets, PyInstaller build, OpenSpec umbrella. |
| API | `C:\Users\matia\estacionamiento-central-api` | FastAPI LAN API using SQLAlchemy/PyMySQL, JWT auth, versioned `/api/v1`, print job creation, printer agent. |
| Mobile | `C:\Users\matia\estacionamiento_central_mobile` | Flutter app using Dio, secure storage, QR/manual API server setup, Sunmi printing. |
| Installer | `C:\Users\matia\estacionamiento-central-installer` | Inno Setup installer bundling desktop payload, MySQL 8.4.8 zip, schema/config scripts. This is the highest-priority production path. |

The production topology is local/LAN-first: Desktop and API share a local MySQL database; mobile calls the API over HTTP LAN; API creates PC print jobs in MySQL; a local Print Agent polls and prints PDFs through SumatraPDF; mobile can also print some Sunmi tickets locally.

### Affected Areas

- `estacionamiento-central-installer/EstacionamientoCentral.iss` — production install/update orchestration for desktop, MySQL, schema, config, shortcuts, and future API/agent deployment.
- `estacionamiento-central-installer/scripts/*.bat` — MySQL lifecycle, DB reset/import, app user creation, generated desktop `config.ini`.
- `estacionamiento-central-api/run.ps1` — current manual API launch, LAN URL detection, QR generation, Uvicorn startup.
- `estacionamiento-central-api/app/core/config.py` — API `.env`/environment defaults and production safety boundary.
- `estacionamiento-central-api/app/db/database.py` — SQLAlchemy engine, pool, and MySQL connection dependency.
- `estacionamiento-central-api/app/core/logging.py` — current rotating API logs; natural home for slow-operation instrumentation.
- `estacionamiento-central-api/printer_agent/*` — print job polling, retries, stale lock recovery, SumatraPDF print execution, current task launcher scripts.
- `estacionamiento-central/schema.sql` — canonical DB schema including `print_jobs` queue and operational tables.
- `estacionamiento-central/utils/db.py` — desktop `config.ini` discovery and MySQL connection behavior.
- `estacionamiento-central/utils/ticket.py` — desktop SumatraPDF direct print path.
- `estacionamiento-central/docs/performance_baseline.md` and `tools/perf_baseline.py` — existing desktop performance baseline tooling.
- `estacionamiento_central_mobile/lib/core/config.dart` — mobile fallback API URL is hardcoded to a development LAN IP.
- `estacionamiento_central_mobile/lib/core/http_client.dart` and `lib/features/settings/presentation/server_settings_screen.dart` — mobile API client, health check, QR/manual server setup.
- `estacionamiento_central_mobile/android/app/src/main/AndroidManifest.xml` — HTTP LAN support via `INTERNET` and `usesCleartextTraffic=true`.

### FASE 0 — Workspace discovery

Discovered files/resources that matter for production readiness:

| Repo | Scripts/config/docs/tools found |
|---|---|
| Desktop | `README.md`, `requirements.txt`, `config.ini`, `schema.sql`, `EstacionamientoCentral.spec`, `docs/performance_baseline.md`, `tools/perf_baseline.py`, `tests/`, top-level tariff/cierre smoke scripts. |
| API | `.env`, UTF-16 `requirements.txt`, `run.ps1`, `app/`, `tests/`, `logs/`, `print_out/`, `printer_agent/run_agent*.ps1|cmd`, `printer_agent/logs/`. |
| Mobile | `pubspec.yaml`, `analysis_options.yaml`, `README.md`, `android/gradlew.bat`, `android/app/src/main/AndroidManifest.xml`, `lib/`, `test/widget_test.dart`. |
| Installer | `EstacionamientoCentral.iss`, `scripts/*.bat`, `scripts/my.ini`, bundled `mysql/mysql-8.4.8-winx64.zip`, bundled `app/EstacionamientoCentral/**`, `output/`. |

Notable absence: no firewall automation was found in installer/API scripts (`netsh`, `New-NetFirewallRule`, `Remove-NetFirewallRule`, or equivalent). No Windows Service/NSSM/WinSW deployment was found for the API. The Print Agent has task-friendly scripts but no installer-managed lifecycle yet.

### FASE 1 — Technical inventory

| Area | Inventory |
|---|---|
| Desktop | Python 3.11+/PySide6, `mysql-connector-python`, FPDF, SumatraPDF printing, PyInstaller packaging. Reads `config.ini` from PyInstaller `_MEIPASS`/executable dir or repo root. Uses local MySQL directly. |
| API | FastAPI, Uvicorn, SQLAlchemy, PyMySQL, Pydantic Settings, JWT with `python-jose`, rotating file logging. Manual launcher loads `.env`, generates connection QR, runs `uvicorn --reload` on `0.0.0.0:8000`. |
| Mobile | Flutter/Dart, Dio, Provider, GoRouter, secure storage, mobile scanner, Sunmi printer. Server URL can be saved via QR/manual setup; fallback URL is a dev LAN IP. |
| Installer | Inno Setup admin installer. Bundles PyInstaller desktop app, MySQL zip, MySQL service setup (`MySQL80`), schema import/reset, app DB user creation, generated desktop config. |
| Shared resources | Desktop `schema.sql` is the schema source used by installer payload. MySQL is shared by desktop/API/print agent. Tickets/reports are local file outputs. |

### FASE 2 — Dependency map

```text
Desktop ──direct MySQL──┐
                        ├── MySQL estacionamiento_db ── print_jobs ── Print Agent ── SumatraPDF ── POS58 Printer
API ───── SQLAlchemy ───┘
  ▲
  │ HTTP LAN :8000 /api/v1
Mobile ── Dio/JWT/QR config ── Sunmi printer optional path
Installer ── installs Desktop + MySQL today; should own API/Agent/firewall/config lifecycle next
```

Bottlenecks and single points of failure:

- MySQL is the central single point of failure for desktop, API, mobile workflows, and PC print jobs.
- API is currently manually started; mobile fails when `run.ps1` is not running or firewall blocks port 8000.
- Print Agent is a single local poller; it has stale-lock recovery and retries, but install/update/startup ownership is not integrated into the installer.
- Printer availability depends on Windows Spooler, exact printer name, and SumatraPDF path.
- Config is split across desktop `config.ini`, installer-generated `config.ini`, API `.env`, mobile secure storage/default URL, and scripts with fixed paths/credentials.

### FASE 3 — Audit

| Domain | Findings |
|---|---|
| Architecture | The overall split is workable for a local/LAN system, but production ownership is incomplete: installer does not deploy API, Print Agent, firewall, or API config. Desktop and API both write to the same DB, so schema/config changes must be coordinated. |
| UI/UX | Mobile has QR/manual server setup and health check, which is good. Desktop README installation path has stale/inconsistent config path wording. Installer UX already prompts before DB reset, which should be preserved. |
| Performance | Desktop has baseline tooling and target (<1s frequent operations with 50 vehicles), but runtime instrumentation is not centralized. API has logging but no endpoint/DB slow-operation timing. PDF/print and UI refresh paths are not slow-log instrumented. |
| Database | Schema includes useful indexes for `print_jobs`; other operational queries may need targeted index review after measuring real slow queries. Installer root/app credentials are fixed in scripts; desktop dev config still uses root. |
| API | Security has production guard for `JWT_SECRET` only when `ENV=prod`, but `.env` is dev-like and manual launcher uses `--reload`. No installed service, health recovery, firewall rule, or generated production env exists. |
| Mobile | Depends on API availability over cleartext LAN HTTP. Base URL persistence is good, but fallback dev IP is unsafe for production packaging. Error messages still assume `run.ps1`, not a production service. |
| Installer | Strongest existing production foundation and must be extended, not replaced. It handles MySQL, DB preservation/reset, app config generation, and app launch. Missing API service install/update, Print Agent lifecycle, firewall lifecycle, SumatraPDF strategy, and config centralization. |

### Approaches

1. **Extend the existing Inno Setup installer as ecosystem orchestrator** — Keep `EstacionamientoCentral.iss` and scripts as the production entry point, adding API/Print Agent/firewall/config steps incrementally.
   - Pros: Preserves current installer investment, one admin-controlled flow, lowest user disruption, matches current Windows deployment model.
   - Cons: Inno/BAT/PowerShell complexity grows; needs careful rollback and idempotency.
   - Effort: Medium/High.

2. **Create a separate deployment tool/installer** — Build a new installer or external deployment manager for API/agent/firewall.
   - Pros: Cleaner separation in theory.
   - Cons: Violates the user priority to work over the existing installer, duplicates install state, increases support burden.
   - Effort: High.

3. **Keep API/agent as manual post-install steps** — Document `run.ps1`, scheduled task, and manual firewall configuration.
   - Pros: Lowest implementation effort.
   - Cons: Not production-ready; startup/reboot/firewall failures remain common and hard to support.
   - Effort: Low implementation, high operational cost.

### Recommendation

Use Approach 1: extend the existing Inno Setup installer in small, reversible work units. For API automatic deployment, choose **WinSW-managed Windows Service** as the preferred mechanism for this ecosystem: it gives service semantics, restart policy, stdout/stderr log files, explicit XML config, uninstall support, and does not require hand-installing NSSM. Compared with Scheduled Task, it is more observable and service-like; compared with raw `sc.exe`, it handles Python process wrapping/logging better; compared with NSSM, it is easier to vendor and configure declaratively in the installer.

### FASE 4 — Prioritized implementation plan

#### Critical

| Improvement | Problem | Impact | Benefit | Affected files | Dependencies | Risks | Rollback | Validation |
|---|---|---|---|---|---|---|---|---|
| Installer-owned API Windows Service using WinSW | API currently starts manually through `run.ps1` with `--reload`. | Mobile/API workflows fail after reboot or if operator forgets launcher. | Automatic startup, restart, logs, consistent production command. | `estacionamiento-central-installer/EstacionamientoCentral.iss`, new installer script/assets for WinSW, API service command/env. | Built API payload or Python runtime/venv strategy; generated `.env`; port choice. | Service starts with wrong cwd/env; update leaves stale service. | Stop/remove service and restore manual `run.ps1`. | Fresh install, reboot, service running, `/api/v1/health` OK, logs written. |
| Installer-owned Print Agent lifecycle | Print Agent has scripts but no installer-managed install/update/start/recovery. | PC tickets can queue forever after reboot/update. | Reliable printing recovery and support diagnostics. | `printer_agent/run_agent_forever.ps1`, `run_agent_task.cmd`, installer scripts, `EstacionamientoCentral.iss`. | API env, DB access, SumatraPDF, printer name. | Duplicate agents, stale lock file, bad printer name. | Remove task/service, stop agent, keep DB jobs intact. | Reboot, create print job, agent claims/prints, error/retry logs visible. |
| Firewall rule automation with idempotency and rollback | No firewall automation found for API port. | Mobile cannot connect despite API running. | One installer-controlled LAN access path. | Installer `.iss` and new PowerShell/BAT firewall script. | API port from generated config. | Duplicate rules or overly broad rule. | Delete rules by stable name/group only. | Install twice: no duplicates; mobile reaches `/health`; uninstall/rollback removes expected rule. |
| Centralized generated production config | Config split across desktop `config.ini`, API `.env`, mobile fallback, and scripts; secrets/paths are fixed in multiple places. | Drift between desktop/API/agent/installer; hard support. | Single installer-generated source for DB/API/print settings. | `scripts/write_app_config.bat`, new API env writer, `.iss`, API `config.py`, mobile production docs/settings. | Decide install paths, service account, DB user/password policy. | Breaking dev configs if mixed with prod generation. | Preserve existing config backups; restore previous files. | Generated desktop/API configs match, API/desktop connect to DB, agent reads printer settings. |

#### High

| Improvement | Problem | Impact | Benefit | Affected files | Dependencies | Risks | Rollback | Validation |
|---|---|---|---|---|---|---|---|---|
| Replace dev API runtime flags for production | `run.ps1` uses `uvicorn --reload`; `.env` says `ENV=dev`. | Lower stability/security in production. | Predictable API process with prod env and safe JWT requirement. | `run.ps1`, service command, `.env` generation, `app/core/config.py`. | Service deployment. | Production fails if JWT not generated. | Revert service command/env to dev during testing only. | Service starts without reload; prod JWT present; auth still works. |
| Installer update strategy for API/agent files | Installer currently copies desktop payload; API/agent payload ownership is undefined. | Updates can leave old API/agent code running. | Repeatable upgrades with stop-copy-start flow. | `.iss`, new scripts, API/agent payload layout. | Service/agent lifecycle. | Interrupting active operations. | Stop services, restore backup copy if start fails. | Upgrade install preserves DB, updates files, service versions/logs confirm restart. |
| Slow-operation instrumentation | No runtime slow logs for desktop/API/PDF/print/UI refresh. | Performance regressions are anecdotal. | Logs only slow operations, keeping noise low. | Desktop controllers/views/utils, API middleware/repos, printer agent, PDF utilities. | Threshold policy per operation. | Over-logging sensitive data or slowing hot paths. | Feature flag/threshold disables instrumentation. | Synthetic slow call emits one structured log; normal calls stay quiet. |
| Remove evidenced hardcoded production blockers | Mobile fallback dev IP, fixed Sumatra path/default printer, fixed installer credentials/paths are brittle. | New installs can silently point to wrong machine/resources. | Safer production packaging and fewer site-specific edits. | `mobile/lib/core/config.dart`, API `.env` generation, printer agent env, installer scripts. | Central config plan. | Removing fallback before installer config exists. | Keep manual settings screen and backup configs. | Clean install requires/loads generated URL; no dev IP in release path. |
| Production diagnostics bundle | Logs exist in several places but no one-command collection. | Support needs manual folder hunting. | Faster troubleshooting. | Installer scripts, API `logs/`, `printer_agent/logs/`, desktop logs if added. | Log path standardization. | Collecting secrets if careless. | Disable command; redact config. | Run diagnostics command; archive contains expected redacted logs. |

#### Medium

| Improvement | Problem | Impact | Benefit | Affected files | Dependencies | Risks | Rollback | Validation |
|---|---|---|---|---|---|---|---|---|
| DB index review from measured slow queries | Schema has print job indexes but other paths need evidence-based review. | Possible slow dashboards/reports/cierres as data grows. | Targeted indexes without guessing. | `schema.sql`, repos/controllers using active/report queries. | Slow-operation logs/baseline data. | Bad indexes slow writes or complicate installer migrations. | Drop added index via migration rollback. | Baseline before/after shows improvement; writes remain acceptable. |
| Installer preflight checks | Current installer validates some MySQL state but not API port, printer, SumatraPDF, firewall state, or service conflicts. | Failures surface late or after install. | Clearer install UX and fewer broken installs. | `.iss`, scripts. | Final service/firewall design. | Blocking valid advanced setups. | Convert hard blocks to warnings where appropriate. | Test missing printer/Sumatra/port conflict paths. |
| Mobile production connection UX copy | Settings error tells users to verify `run.ps1`. | Confusing once API is a service. | Production-oriented guidance. | `server_settings_screen.dart`, QR scanner flow. | API service rollout. | Premature copy before deployment changes. | Keep generic wording compatible with manual/dev. | Failed health check gives correct action. |
| Health endpoints for dependencies | `/health` is simple; DB has separate ping. Agent/printer health is not exposed centrally. | Mobile can see API alive while DB/print is broken. | Better diagnostics and installer validation. | API health/db endpoints, printer agent status source. | Decide safe status details. | Leaking internals over LAN. | Keep detailed status admin-only/local. | Health reports API/DB/service state as designed. |

#### Low

| Improvement | Problem | Impact | Benefit | Affected files | Dependencies | Risks | Rollback | Validation |
|---|---|---|---|---|---|---|---|---|
| README/install doc alignment | README has stale path wording and manual Sumatra note while installer contains newer behavior. | User/support confusion. | Docs match production installer. | `README.md`, installer docs. | Final installer decisions. | Docs ahead of code. | Revert doc section. | Review checklist against actual clean install. |
| Version/source-of-truth cleanup | App/installer/mobile versions are separate. | Release mistakes. | Easier release process. | `app_version.py`, `.iss`, `pubspec.yaml`, release docs. | Release policy. | Over-engineering for small app. | Keep manual update checklist. | Release checklist catches version drift. |

### Risks

- The installer touches admin-level resources: MySQL service, firewall, future API/agent services. Idempotency and rollback are mandatory.
- Fixed credentials are present in repo/config/scripts; future work must avoid leaking values in logs/docs and should migrate carefully.
- API requirements file is UTF-16 encoded; tooling that assumes UTF-8 may fail.
- Desktop/API share the same DB directly, so schema/config changes can break cross-repo compatibility if not coordinated.
- Print reliability depends on Windows Spooler, SumatraPDF, exact printer names, and thermal printer timing.

### Ready for Proposal

Yes. Next phase should be `sdd-propose` for `ecosystem-production-readiness-audit`, scoped as a read-only-to-plan transition first, then implementation split into small installer-first changes. Because `chained_pr_strategy=ask-always` and the expected work exceeds 400 changed lines, ask before apply and plan chained PR slices.
