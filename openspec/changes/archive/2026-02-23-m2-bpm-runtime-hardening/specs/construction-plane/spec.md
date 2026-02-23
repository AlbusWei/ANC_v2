## ADDED Requirements

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
