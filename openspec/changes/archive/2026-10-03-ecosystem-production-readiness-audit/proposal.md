# Proposal: Ecosystem Production Readiness Audit

## Intent
Make the Windows/LAN ecosystem production-ready with minimum intervention. The installer is the priority path: extend it incrementally, with no rewrite and no implementation before approved specs/design/tasks.

## Problem and Operational Risks
- API starts manually with dev runtime; mobile breaks after reboot or omission.
- Installer does not own API service, Print Agent lifecycle, firewall, or production API config.
- Config is fragmented across desktop, API, mobile, scripts, and printer settings.
- Desktop/API/Print Agent share MySQL; uncoordinated changes can break compatibility.
- Printing depends on Windows Spooler, printer name, SumatraPDF path, and agent reliability.

## Scope
### Goals
- Installer-first hardening over current architecture.
- Justified, reversible cross-project changes only.
- Mandatory compatibility, rollback, diagnostics, and validation planning.
- Small work units; likely chained PRs because forecast exceeds 400 lines.

### Non-Goals
- No rewrite, cloud migration, or replacement installer.
- No speculative schema/index changes without measurements.
- No implementation before approved plan/spec/design/tasks.

## Capabilities
### New Capabilities
- `production-deployment`: Installer-owned API/agent/firewall/config.
- `production-observability`: Slow logs, diagnostics, validation evidence.

### Modified Capabilities
- None; no existing `openspec/specs/` capabilities found.

## Approach
Incremental installer-first hardening. Deploy the API as a **WinSW-managed Windows Service**: service semantics, restart policy, stdout/stderr logs, XML config, vendorable config/binary, and uninstall support. Prefer WinSW over NSSM to avoid manual wrapper dependency; over Scheduled Task for observability/service behavior; over raw `sc.exe` because Python/Uvicorn wrapping and logging are weaker.

## Affected Areas
| Area | Impact | Boundary |
|------|--------|----------|
| Desktop | Modified | Preserve DB/config behavior; compatible changes only. |
| API | Modified | Production service command/env, health/logging. |
| Mobile | Modified | Production-safe connection behavior; preserve QR/manual setup. |
| Installer | Modified | Highest priority; orchestrates API, agent, firewall, config, rollback. |
| Print Agent | Modified | Installer-managed lifecycle; preserve queue/retry semantics. |
| Firewall | New | Idempotent API-port rule; removable by stable name/group. |
| Config | Modified | Generated config with backups; no dev breakage. |
| Performance | New | Instrument slow operations before tuning. |

## Rollback and Compatibility
Preserve manual launch paths until validated. Back up generated configs, avoid destructive DB changes, stop/remove services cleanly, remove only owned firewall rules, and keep database/print jobs intact.

## Validation
Fresh install, upgrade, reboot recovery, `/api/v1/health`, mobile LAN connection, print job, firewall idempotency/removal, config restore, service logs, diagnostics, and available repo tests.

## Dependencies
- Approved specs/design/tasks; WinSW asset strategy; API payload/runtime strategy; admin privileges; printer policy.

## Success Criteria
- [ ] Installer installs/updates/rolls back API service, agent, firewall, and config.
- [ ] Desktop/API/Mobile remain compatible.
- [ ] Each cross-project change has technical justification and validation evidence.
