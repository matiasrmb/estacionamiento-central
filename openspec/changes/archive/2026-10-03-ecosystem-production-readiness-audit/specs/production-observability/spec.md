# Delta for production-observability

## ADDED Requirements

### Requirement: Threshold-Based Slow Operation Logs

The system MUST instrument slow operations and log only executions above configured thresholds. Logs MUST avoid secrets and unnecessary payload data.

Affected repos: desktop, API, Print Agent.

#### Scenario: Normal operations stay quiet

- GIVEN an operation completes below its threshold
- WHEN desktop, API, or agent instrumentation evaluates it
- THEN no slow-operation log is emitted

#### Scenario: Slow operation is captured

- GIVEN an operation exceeds its threshold
- WHEN instrumentation completes
- THEN one structured slow log is written
- AND the entry identifies area, operation, duration, and safe context

### Requirement: Required Instrumentation Coverage

Instrumentation MUST cover desktop registration, exit, dashboard refresh, table refresh, PDF generation, and printing; API endpoints and DB operations; Print Agent job claim/print/retry; and installer health checks.

Affected repos: desktop, API, Print Agent, installer.

#### Scenario: Critical flows have slow-log evidence

- GIVEN validation exercises a critical production flow
- WHEN any covered step exceeds its threshold
- THEN the responsible component emits a slow log
- AND normal successful steps below threshold remain unlogged

### Requirement: Redacted Diagnostics Bundle

The system MUST provide a diagnostics bundle that collects relevant desktop/API/agent/installer logs and configuration metadata. Secrets, passwords, tokens, and private keys MUST be redacted before export.

Affected repos: installer, desktop, API, Print Agent.

#### Scenario: Support bundle is safe to share

- GIVEN diagnostics collection is requested
- WHEN the bundle is generated
- THEN it includes relevant logs and config metadata
- AND sensitive values are redacted or omitted

### Requirement: Production Health Checks

Health checks MUST validate API reachability, DB connectivity, service state, firewall rule ownership, Print Agent status, and printer readiness where safely possible. Checks MUST distinguish warnings from hard failures.

Affected repos: installer, API, Print Agent, mobile guidance.

#### Scenario: Health check reports actionable status

- GIVEN a production machine has API, DB, firewall, agent, and printer configured
- WHEN health checks run
- THEN each safe dependency reports pass, warning, or fail
- AND unsafe or unavailable checks are reported without destructive action

### Requirement: Validation Evidence Matrix

The change MUST produce validation evidence for fresh install, upgrade, reinstall, rollback, reboot recovery, mobile connection, print job processing, and available automated tests.

Affected repos: all related repos.

#### Scenario: Release evidence is complete

- GIVEN implementation is ready for verification
- WHEN validation is executed
- THEN evidence covers each required lifecycle case
- AND missing automated coverage is documented with manual proof
