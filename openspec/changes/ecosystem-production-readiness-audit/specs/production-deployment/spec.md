# Delta for production-deployment

## ADDED Requirements

### Requirement: Installer-Orchestrated Deployment

The system MUST keep the existing Inno Setup installer as the deployment orchestrator for Desktop, API, Print Agent, firewall, and production config. Cross-project changes MUST include explicit technical justification and rollback impact.

Affected repos: installer, desktop, API, mobile.

#### Scenario: Existing installer remains owner

- GIVEN a production install or update is planned
- WHEN deployment work is designed
- THEN the existing installer is extended rather than replaced
- AND each non-installer repo change has a documented technical reason

### Requirement: API Windows Service Lifecycle

The installer MUST install, update, start, stop, and uninstall the API as an automatic Windows startup service. The recommended mechanism SHOULD be WinSW unless design evidence proves it impossible. The service MUST use generated production config, write logs, restart on failure, avoid `--reload`, and support safe rollback.

Affected repos: installer, API.

#### Scenario: API survives reboot

- GIVEN a fresh production install
- WHEN Windows reboots
- THEN the API starts automatically with production config
- AND health checks pass without running `run.ps1`

#### Scenario: Service rollback is safe

- GIVEN an update fails after service changes
- WHEN rollback runs
- THEN the owned service is stopped or restored
- AND prior config and logs remain available

### Requirement: Installer-Owned Print Agent Lifecycle

The installer MUST own Print Agent install, update, startup, recovery, and logging without breaking existing print job queue, claim, retry, stale-lock, or failure semantics.

Affected repos: installer, API Print Agent.

#### Scenario: Queued print jobs survive agent update

- GIVEN pending or failed print jobs exist
- WHEN the Print Agent is updated or restarted
- THEN jobs are not deleted or duplicated
- AND retry/recovery state remains valid

### Requirement: Idempotent Firewall Rule Management

The installer MUST create narrowly scoped, idempotent firewall rules for the configured API LAN port only. Rules MUST NOT duplicate across reinstall/update and MUST be removable on rollback/uninstall by stable identity.

Affected repos: installer, API/mobile connection path.

#### Scenario: Reinstall does not duplicate firewall rules

- GIVEN the installer has already opened the API LAN port
- WHEN install or repair runs again
- THEN exactly one owned rule identity exists
- AND rollback removes only that owned rule

### Requirement: Central Production Configuration

The installer MUST generate and back up production config centrally across desktop, API, Print Agent, and mobile connection guidance while preserving manual and development flows.

Affected repos: installer, desktop, API, mobile.

#### Scenario: Production config is generated without breaking dev

- GIVEN production config is generated during install
- WHEN desktop, API, agent, and mobile setup use it
- THEN shared DB/API/printer values are consistent
- AND existing manual/dev launch paths still work

### Requirement: Data-Safe Deployment Operations

Deployment MUST NOT perform destructive database operations by default. User data, reports, tickets, print jobs, and configs MUST be preserved unless explicitly backed up and approved by the operator.

Affected repos: installer, desktop, API.

#### Scenario: Upgrade preserves operational data

- GIVEN an existing production installation has data and print jobs
- WHEN upgrade, reinstall, rollback, or uninstall runs
- THEN data is preserved by default
- AND destructive actions require backup plus explicit approval
