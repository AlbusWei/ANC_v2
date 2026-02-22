## ADDED Requirements

### Requirement: Construction Plane Must Track M2 BPM Runtime Hardening As In Progress
Construction plane governance SHALL explicitly track this change as In Progress until all planned rounds are completed.

#### Scenario: Thread 0 scaffold submission updates construction plane
- **WHEN** Thread 0 completes scaffold initialization and submits its commit
- **THEN** `docs/architecture/construction_plane.md` marks `m2-bpm-runtime-hardening` as In Progress
- **AND** milestone `Q-001` remains open and is not marked closed by this scaffold round
