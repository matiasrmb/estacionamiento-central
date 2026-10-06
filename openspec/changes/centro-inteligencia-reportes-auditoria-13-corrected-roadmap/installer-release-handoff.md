# Installer and Release Handoff: Corrected Reporting Intelligence and Audit Roadmap

## Scope Boundary

This artifact is a Desktop-repo planning handoff for Installer and release alignment. It does not modify Installer, API, Mobile, Desktop runtime code, tests, branches, commits, pushes, or pull requests.

Installer implementation must wait for an installer-scoped derivative or explicit release work after the API, Desktop, and Mobile repo-scoped derivatives land. The sibling Installer paths below are read-only evidence references captured from `D:\Desarrollo\EstacionamientoCentral\estacionamiento-central-installer`.

## Read-Only Evidence References

| Evidence path | Evidence used | Required installer/release outcome |
|---|---|---|
| `../estacionamiento-central-installer/EstacionamientoCentral.iss` | The installer script declares `AppVersion=1.3.0`, `OutputBaseFilename=Instalador_EstacionamientoCentral_1.3.0`, packages Desktop from `app\EstacionamientoCentral\*`, packages API payload from `payload\api\*`, includes `stage_api_payload.ps1`, and runs API service/production-health checks during install. | Keep version and output naming aligned with the release. Package only API/Desktop payloads produced by the completed repo-scoped derivatives. Do not edit this script from the Desktop handoff; installer edits belong to a later installer-scoped derivative or explicit release task. |
| `../estacionamiento-central-installer/payload/api/API_PAYLOAD_MANIFEST.json` | The manifest records generated time, source API repo path/branch/head commit, tracked-change state, copied file count, required executable SHA-256 values, excluded secret/log/cache patterns, and payload notes. It also states the manifest verifies staged executables against source dist at staging time and does not attest that the dist was built from source commit. | Regenerate or refresh the manifest only in release/installer scope after the API derivative lands. Verify API executable and schema-migration executable hashes, clean source state, and source revision provenance before packaging. |
| `../estacionamiento-central-installer/**` | Installer owns packaging, payload staging, WinSW/API service setup, managed schema script execution, firewall setup, and production health validation. | Treat the whole sibling installer repository as read-only evidence in this Desktop-root change. Any installer-script, payload, or release-bundle edits require the later installer-scoped derivative or explicit release work. |

## Release Alignment Requirements

### API Payload Alignment

- The API payload packaged by Installer must come from the API derivative that implements the corrected reporting contract.
- The payload manifest must identify the API source revision and required executable hashes for `EstacionamientoCentralAPI.exe` and `EstacionamientoCentralSchemaMigrations.exe`.
- The manifest must not be treated as source-build attestation unless the later release process adds that guarantee explicitly.
- CSV compatibility, export deferral, capacity metadata, anomaly contracts, and corrected metric names must be settled in the API derivative before staging.

### Desktop Payload Alignment

- The Desktop payload packaged by Installer must include the Desktop derivative that renders the corrected Intelligence Center labels, fallback warnings, capacity state, and deferred export state.
- Installer release work must confirm the Desktop package version and installer `AppVersion`/output filename refer to the same release train.
- Desktop local fallback remains non-official and incomplete; Installer must not document or package it as closure truth.

### Mobile Release Alignment

- Mobile is not packaged by this Installer, but release readiness must wait for the Mobile derivative verification because Mobile consumes the same canonical API reporting contract.
- Mobile quick-consultation labels and no full-center/export boundary must be verified before the ecosystem release is declared ready.

## Required Release Verification

| Repo / area | Minimum verification after derivatives land |
|---|---|
| API | Run `python -m unittest discover -s tests` in `../estacionamiento-central-api` after the API derivative and before staging the API payload. |
| Desktop | Run `python -m unittest discover -s tests` in this repo after the Desktop derivative and before packaging the Desktop payload. |
| Mobile | Run `flutter test` and `flutter analyze` in `../estacionamiento_central_mobile` after the Mobile derivative. Record runtime harness availability or `N/A` with reason. |
| Installer | Run an installer/release checklist in `../estacionamiento-central-installer` after staging final payloads: confirm `AppVersion`/output filename, API manifest source revision and hashes, Desktop payload version/source, excluded secrets/logs/cache patterns, service setup scripts present, production-health checklist, and rollback instructions. |

## Installer Checklist Expectations

- Confirm `EstacionamientoCentral.iss` release version and output filename match the target release.
- Confirm the staged API manifest references the post-derivative API source revision and clean source state.
- Confirm required API executables are present and their SHA-256 values match the manifest.
- Confirm Desktop payload was built from the post-derivative Desktop source and is the payload referenced by Installer.
- Confirm API/Desktop reporting behavior is not represented as complete until API, Desktop, and Mobile derivative verification has passed.
- Confirm Installer packaging excludes secrets, certificates, logs, caches, virtual environments, and test artifacts.
- Confirm install-time API service setup, managed schema path, firewall setup, and production health validation are covered by the installer release checklist.
- Confirm rollback instructions name the specific installer/payload files or release bundle that can be reverted without changing source derivatives.

## Work Unit Evidence

| Evidence | Required value |
|---|---|
| Focused test command and exact result | Structural readback only for this Desktop planning artifact. Command captured in `apply-progress.md`; no runtime Installer/API/Mobile code was touched. |
| Runtime harness command/scenario and exact result | N/A: Phase 5 is a planning-only Installer/release handoff in the Desktop repo. Runtime verification belongs to repo-scoped derivatives and later installer/release work. |
| Rollback boundary | Remove this file, revert only Phase 5 task checkboxes in `tasks.md`, and remove only the Phase 5 section in `apply-progress.md`. |

## Handoff Status

Phase 5 is complete when this artifact exists, Installer read-only evidence paths are referenced, release verification expectations include API unittest, Desktop unittest, Mobile test/analyze, and an Installer checklist after repo-scoped derivatives land, tasks 5.1 through 5.3 are checked, and `apply-progress.md` records structural verification results.
