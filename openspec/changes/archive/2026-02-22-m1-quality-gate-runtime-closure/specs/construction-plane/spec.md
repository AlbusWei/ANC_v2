## ADDED Requirements

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
