## ADDED Requirements

### Requirement: M3 Change Must Provide A Structured Gap Baseline Matrix
The change MUST provide a structured M3 gap baseline matrix that captures design closure status and execution ownership for subsequent sessions.

#### Scenario: Session1 publishes matrix with required fields
- **WHEN** Session1 completes baseline documentation
- **THEN** `openspec/changes/m3-self-development-e2e-online/m3-gap-baseline.md` exists
- **AND** each row includes `设计条目`、`应有资产`、`现状`、`阻断级别`、`归属会话`、`验收条件`
- **AND** `阻断级别` only uses `S0|S1|S2`

### Requirement: M3 Manifest Closure Gaps Must Be Explicitly Tracked Before Implementation
The change MUST explicitly track manifest closure gaps between M3 primary flows and development-loop-core-standard before any implementation session begins.

#### Scenario: Session2 gate checks manifest closure items
- **WHEN** Session2 starts closure work
- **THEN** the matrix includes explicit rows for `full-development`、`hotfix`、`refactor` phase execution syntax gaps
- **AND** the matrix includes explicit rows for missing `process_type` and missing `governance_bundle`
- **AND** each closure row defines measurable acceptance conditions

### Requirement: Planned But Missing Assets Must Have Session Ownership And Acceptance Gates
The change MUST assign missing assets to concrete sessions and define acceptance gates for each asset.

#### Scenario: Session3 has explicit ownership for planned assets
- **WHEN** Session1 baseline is reviewed
- **THEN** the matrix includes `sys.arch.impact-analyzer`、`sys.admin.release-manager`、`registry-sync`、`escalation`、`release-manager-agent`
- **AND** each item is mapped to Session3 with file/registry validation gates
- **AND** acceptance gates include `python3 shared/registry/registry_contract_tool.py verify` pass criteria

### Requirement: Lifecycle Target Must Be Capped At Review For This Change
This change MUST cap lifecycle progression at `review` and MUST NOT promote assets to `active` in this round.

#### Scenario: Session7 close-out enforces review-only target
- **WHEN** Session7 performs close-out reconciliation
- **THEN** all lifecycle outcomes in this change remain at or below `review`
- **AND** no close-out statement claims `active` promotion
- **AND** any `active` attempt is treated as fail-closed
