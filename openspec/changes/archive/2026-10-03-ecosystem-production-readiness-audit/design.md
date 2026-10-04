# Design: Ecosystem Production Readiness Audit

## 1. Architecture overview and deployment topology

Minimum-intervention topology stays LAN/local: Inno Setup owns install/update; Desktop and API share local MySQL; Mobile calls FastAPI over LAN; API writes `print_jobs`; one local Print Agent prints through SumatraPDF.

```text
Inno Setup ── installs/configures ── Desktop + MySQL80 + API WinSW service + Print Agent + firewall
Desktop ── MySQL ── API ── print_jobs ── Print Agent ── SumatraPDF/Spooler/Printer
Mobile ── HTTP LAN :8000 /api/v1 ───────┘
```

## 2. Installer orchestration design

Extend `EstacionamientoCentral.iss`; do not replace it. Add files under installer `assets/winsw/`, `payload/api/`, and `scripts/*.ps1|bat`. Run order: MySQL existing steps → backup/generate config → install/update API service → install/update Print Agent launcher → firewall rule → health checks → optional Desktop launch. All new scripts must be idempotent and log under `{app}\logs\installer`.

## 3. API service design

Use WinSW as the Windows service wrapper and run the PyInstaller-packaged API executable directly. Service: `EstacionamientoCentralAPI`; display name: `Estacionamiento Central API`; working directory: `{app}\api`; generated env file: `{app}\config\api.env` copied to `{app}\api\.env`; logs: `{app}\logs\api-service\*.log`; app logs remain API `logs/api.log`. Command: `{app}\api\EstacionamientoCentralAPI.exe` with no `--reload`, no `python -m uvicorn`, and no target-machine Python or install-time virtual environment in the main service path. WinSW restart: automatic startup, restart on non-zero exit with bounded delay. Install/update: stage the new PyInstaller `onedir` payload, wrapper, env, and XML under `{app}\tmp`; if the owned service exists, stop it and run WinSW `uninstall` with the existing wrapper before deleting/replacing `{app}\api`; wait until `EstacionamientoCentralAPI` is absent; back up the current API directory; replace `{app}\api` cleanly; then always run WinSW `install` from the new wrapper, `start`, and health check. WinSW command execution logs command, exit code, stdout, and stderr to `{app}\logs\installer\api-service.log` with secret-like values redacted. Uninstall/rollback: stop/remove only `EstacionamientoCentralAPI`, restore prior env/payload backup, keep logs.

## 4. API payload/runtime strategy

| Option | Tradeoff | Decision |
|---|---|---|
| Bundle source + venv | Lowest code change, easiest reuse of current FastAPI layout; larger installer and dependency install risk; proved fragile because Windows venvs can capture developer paths or WindowsApps Python aliases. | Rejected for the main service path. |
| PyInstaller API exe | Cleaner runtime with no target-machine Python prerequisite; higher packaging/debug risk and requires explicit build/staging before compiling the installer. | Selected for Slice 2 correction. |
| Keep manual `run.ps1` | Smallest diff; not production-ready. | Preserve for dev/manual fallback only. |

## 5. Print Agent lifecycle design

Installer owns a single agent launcher using existing `printer_agent/run_agent_forever.ps1` semantics. Prefer a second WinSW service named `EstacionamientoCentralPrintAgent` wrapping PowerShell or Python directly; fallback scheduled task only if service constraints appear. Preserve DB queue semantics: no deletion of `print_jobs`, no reset of `IMPRIMIENDO` except existing stale-lock logic. Duplicate prevention: keep lock file plus service single-instance ownership; installer must stop old task/service before starting the owned service. Logs: `{app}\logs\print-agent` plus existing agent logs. Recovery: auto-start, restart on failure, spooler/printer preflight remains warning/retry, not destructive.

## 6. Firewall automation design

PowerShell script manages one inbound TCP rule: name `EstacionamientoCentral API Port 8000`, group `Estacionamiento Central`, local port from generated config, profile `Private` by default. Idempotency: query by group/name, update if port changed, never create duplicates. Rollback/uninstall removes only matching group/name.

## 7. Config generation/backup strategy

Create `{app}\config\production.json` as installer source of truth plus generated files: Desktop `{app}\_internal\config.ini`, API `{app}\api\.env` or `{app}\config\api.env`, Print Agent env values, and mobile QR/guidance URL. Back up changed configs to `{app}\backups\config\yyyyMMdd_HHmmss\`. Preserve dev files in repos. Secrets must be generated or reused from prior backup; do not log passwords/JWT.

## 8. Observability design

Add threshold-only slow logs. Defaults: API request >1000ms, API DB query >500ms, Desktop UI/controller paths >1000ms, PDF/print job steps >3000ms, installer health step >5000ms. API: middleware in `app/main.py`, DB timing wrappers in `app/db/database.py`, structured safe fields only. Desktop: small helper around registration/exit/dashboard/table/PDF/print paths. Agent: time claim/render/print/mark. Diagnostics bundle script collects installer/API/agent/Desktop logs and selected config metadata with redaction patterns for password, secret, token, key.

## 9. Health-check design

Installer checks: admin, MySQL service/DB login, API port availability, service state, firewall rule, generated config, Sumatra path, printer presence/spooler. Runtime API keeps `/health` simple and adds local/admin-safe dependency health for DB/service metadata where safe; `/db/ping` remains admin-protected. Agent health is file/status based unless an API status table is later justified.

## 10. Cross-project change boundaries

Installer carries orchestration and scripts. API changes only for production config, service-safe startup, health, logging/timing. Desktop changes only for slow logs/config compatibility. Mobile changes only remove dev-IP production dependency and update connection guidance. No schema changes unless measured slow logs justify them later.

## 11. Data safety, rollback, upgrade/reinstall

No destructive DB action by default; keep existing explicit reset prompt. Upgrade is stop-copy-start with config backups. Reinstall updates owned service/firewall identities. Rollback restores previous config/payload and stops/removes new services if health fails. Print jobs, tickets, reports, DB backups, and logs remain.

## 12. Validation matrix

| Case | Evidence |
|---|---|
| Fresh install/reboot | API and agent auto-start; `/api/v1/health` passes. |
| Upgrade/reinstall | No duplicate services/firewall rules; configs backed up. |
| Rollback/uninstall | Owned service/rule removed or restored; data/logs preserved. |
| Mobile LAN | QR/manual URL reaches health endpoint. |
| Print | Pending job claims once, prints or retries safely. |
| Tests | Desktop/API `python -m unittest discover -s tests`; mobile `flutter test`; installer manual checklist/build. |

## 13. Risks and mitigations

- PyInstaller runtime packaging can miss hidden imports or native files → build and smoke the packaged executable before compiling the installer; keep manual `run.ps1` fallback for development/manual recovery only.
- Service account/env/cwd mistakes → WinSW XML uses explicit working directory/env/logs and health gate.
- Duplicate agents can double-print → service-owned lifecycle, lock file, stop legacy launcher before start.
- Secrets in diagnostics → allowlist metadata and redact keys by pattern.
- Installer diff will exceed 400 lines → chained PRs required before apply.

## 14. Work-unit / PR slicing recommendation

Review budget is 400 changed lines and strategy is ask-always; expect chained PRs. Recommended slices: (1) installer config backup + diagnostics scaffolding, (2) API WinSW service payload/install/update/rollback, (3) Print Agent service lifecycle, (4) firewall automation and installer health checks, (5) slow-operation instrumentation, (6) mobile/Desktop minimal guidance/logging. Each slice must include its validation evidence and rollback scope.
