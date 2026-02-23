## ADDED Requirements

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
- **THEN** directory `docs/design/modules/evidence/construction-plane/R-20260222-M6-m3-self-development-e2e-online-01/` exists
- **AND** it contains `scope_baseline.md`、`open_questions.md`、`thread_handoff.md`、`round-evidence.jsonl`
- **AND** the first JSONL record has `event=round_open` with matching `round_id` and `openspec_ref`
