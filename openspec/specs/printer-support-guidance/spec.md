# Delta for Printer Support Guidance

## ADDED Requirements

### Requirement: Define supported print path

Affected repos: Desktop, API, printer agent.
The system MUST document and surface that the supported ticket printing path is SumatraPDF plus a configured Windows printer using a validated vendor or thermal driver.

#### Scenario: Operator reviews printer support

- GIVEN an operator opens printer setup or diagnostics
- WHEN support guidance is shown
- THEN it MUST identify SumatraPDF path and configured printer name as required settings
- AND it MUST state that unvalidated generic thermal drivers are unsupported or unreliable

### Requirement: Provide test print and diagnostics

Affected repos: Desktop, API, printer agent.
The system MUST provide a test-print workflow and diagnostics that expose configuration status, printer availability, queue/job outcome, and last visible print error when available.

#### Scenario: Test print succeeds

- GIVEN SumatraPDF and printer name are configured
- WHEN an operator runs test print
- THEN the system MUST create a test ticket print attempt
- AND it MUST show a successful result when the print path accepts the job

#### Scenario: Test print fails

- GIVEN the print path is missing or rejected by the printer system
- WHEN an operator runs test print
- THEN diagnostics MUST show the missing or failing setting
- AND guidance SHOULD include fallback actions such as Windows test page, save PDF, or reprint last ticket/job

## MODIFIED Requirements

## REMOVED Requirements
