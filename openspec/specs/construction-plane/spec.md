# construction-plane Specification

## Purpose
TBD - created by archiving change m6-construction-round-sync. Update Purpose after archive.
## Requirements
### Requirement: M6 Runtime Round Must Emit Complete Evidence Bundle
The construction-plane-governance runtime round MUST produce a complete evidence bundle with deterministic references for each AP phase.

#### Scenario: Successful runtime round emits all required references
- **WHEN** a governance round runs from p1 to p5 with valid inputs
- **THEN** the output bundle includes `m6_update_bundle_ref`, `linkage_report_ref`, `openspec_sync_ref`, `registry_verify_report_ref`, `construction_plane_delta_ref`, `open_questions_ref`, `round_evidence_log_ref`, and `round_close_summary_ref`
- **AND** `round_evidence_log_ref` contains `round_open`, zero or more `checkpoint_synced`, and terminal `round_close`

### Requirement: Round Close Must Fail On Checkpoint Commit Mismatch
The runtime gate MUST fail-closed when checkpoint and commit counts diverge.

#### Scenario: checkpoint_count differs from commit_count
- **WHEN** `round_close` carries different values for `checkpoint_count` and `commit_count`
- **THEN** runtime verification returns failure
- **AND** round close is rejected with structured error output

### Requirement: Construction Plane Must Track M2 BPM Runtime Hardening As In Progress
Construction plane governance SHALL explicitly track this change as In Progress until all planned rounds are completed.

#### Scenario: Thread 0 scaffold submission updates construction plane
- **WHEN** Thread 0 completes scaffold initialization and submits its commit
- **THEN** `docs/architecture/construction_plane.md` marks `m2-bpm-runtime-hardening` as In Progress
- **AND** milestone `Q-001` remains open and is not marked closed by this scaffold round

### Requirement: Construction Plane Must Close M2 Gate Only After Live Regression Pass
Construction plane governance SHALL close `Q-001` only after live regression and gate reconciliation pass.

#### Scenario: Thread 6 close-out updates construction plane
- **WHEN** Thread 6 finishes live regression and gate reconciliation
- **THEN** `docs/architecture/construction_plane.md` closes `Q-001`
- **AND** close-out evidence includes passed `verify`/`verify-m2`/`verify-m6` plus live regression result

### Requirement: Runtime-Closure Change Must Provide Delta Specs Before Archive
The `m1-quality-gate-runtime-closure` change MUST include at least one OpenSpec delta spec with scenario blocks before archive is allowed.

#### Scenario: Delta spec package exists and passes validation
- **WHEN** the change enters close-out stage
- **THEN** `openspec/changes/m1-quality-gate-runtime-closure/specs/**/spec.md` exists
- **AND** each changed requirement includes at least one `#### Scenario:`
- **AND** `openspec validate m1-quality-gate-runtime-closure --json` returns pass

### Requirement: Runtime-Closure Round Must Record Carryover And Resolution Path
Construction plane governance MUST preserve both carryover state and resolution plan when OpenSpec sync is incomplete, and close the carryover only after validation passes.

#### Scenario: Round closes with pending OpenSpec sync
- **WHEN** round close evidence marks `sync_status = needs_sync`
- **THEN** `docs/architecture/construction_plane.md` keeps the item in `In Progress` or `Next`
- **AND** closure summary references the unresolved delta/spec scenario gap

#### Scenario: Carryover is resolved in follow-up closure
- **WHEN** delta specs are added and OpenSpec validation passes
- **THEN** the change can be archived
- **AND** construction plane updates remove the stale `needs_sync` carryover from active backlog

### Requirement: Construction Plane Must Define Session2~Session7 Dependency Chain For M3 Change
Construction plane governance MUST define an explicit dependency chain and DoD for Session2 through Session7 of `m3-self-development-e2e-online`.

#### Scenario: construction_plane includes executable session DoD
- **WHEN** Session1 updates construction-plane
- **THEN** `docs/architecture/construction_plane.md` includes a dedicated section for `m3-self-development-e2e-online`
- **AND** the section explicitly defines `Session2 -> Session3 -> Session4 -> Session5 -> Session6 -> Session7` dependencies
- **AND** each session DoD binds to concrete files and validation commands

### Requirement: Session1 Must Initialize M6 Evidence Directory With round_open Event
Session1 MUST initialize a new M6 evidence directory and persist a valid `round_open` event for this change.

#### Scenario: Session1 writes baseline evidence files
- **WHEN** Session1 creates the M6 evidence baseline
- **THEN** directory `runtime_data/execution/evidence/construction-plane/R-20260222-M6-m3-self-development-e2e-online-01/` exists
- **AND** it contains `scope_baseline.md`、`open_questions.md`、`thread_handoff.md`、`round-evidence.jsonl`
- **AND** the first JSONL record has `event=round_open` with matching `round_id` and `openspec_ref`

