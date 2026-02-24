# bpm-runtime-hardening-audit-foundation Specification

## Purpose
定义 M2 BPM runtime hardening 的可审计基线要求，确保回合级证据、checkpoint/commit 对账与 live regression 前置约束可 Fail-Closed。

## Requirements

### Requirement: Baseline Audit Scaffolding Must Exist Before Runtime Hardening Development
The M2 BPM runtime hardening change SHALL create auditable baseline artifacts before any runtime re-implementation tasks are started.

#### Scenario: Baseline scaffolding initialized
- **WHEN** Thread 0 initializes the change scaffolding
- **THEN** `tests/m2-bpm-runtime/TEST.md` and `tests/m2-bpm-runtime/run_post_dev_regression.py` are present
- **AND** `runtime_data/execution/evidence/bpm-runtime/` exists with pre-created evidence placeholders

### Requirement: Checkpoint To Commit Mapping Must Be Persisted For Every Code-Change Round
For each code-change thread round, the workflow MUST persist one mapping record that links Entire checkpoint and Git commit.

#### Scenario: Thread round with code changes is committed
- **WHEN** a thread round from Thread 1 to Thread 6 creates a commit
- **THEN** one new JSONL record is appended to `runtime_data/execution/evidence/bpm-runtime/checkpoint_commit_map.jsonl`
- **AND** the record includes `round_id`, `entire_checkpoint_id`, `commit_sha`, `changed_files`, and `ts`

### Requirement: M6 Live Regression Plan Must Be Defined Before Thread 6 Execution
The change SHALL define live-regression execution rules before starting Thread 6 so that runtime validation can fail-closed.

#### Scenario: Live regression prerequisites are reviewed before Thread 6
- **WHEN** the team prepares to run Thread 6
- **THEN** `runtime_data/execution/evidence/bpm-runtime/m6_live_regression_plan.md` specifies round_id naming, git-range collection, checkpoint/commit reconciliation, and pass criteria
- **AND** missing `Entire-Checkpoint` trailer in any prior commit is treated as a hard failure condition for Thread 6 completion
