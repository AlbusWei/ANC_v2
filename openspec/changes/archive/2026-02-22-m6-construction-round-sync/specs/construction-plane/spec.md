## ADDED Requirements

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
