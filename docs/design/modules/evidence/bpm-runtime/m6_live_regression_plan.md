# M6 Live Regression Plan (Pre-Embedded)

## Scope

This plan defines the live-regression contract for `m2-bpm-runtime-hardening` in Thread 6.
Thread 0 initializes policy only; execution evidence is generated in later rounds.

## Round ID Naming Rule

- Rule: `R-YYYYMMDD-M2-m2-bpm-runtime-hardening-T<thread_no>`
- Examples:
  - `R-20260222-M2-m2-bpm-runtime-hardening-T1`
  - `R-20260222-M2-m2-bpm-runtime-hardening-T6`
- Constraint: one code-change round maps to one commit and one checkpoint record.

## Git-Range Collection Rule

- `git_range.txt` MUST store the exact comparison range used for Thread 6 regression.
- Format:
  - `base_commit=<sha>`
  - `head_commit=<sha>`
  - `range=<base>..<head>`
- Recommended base: Thread 0 scaffold commit SHA.
- Recommended head: latest Thread 6 candidate commit SHA.

## Checkpoint/Commit Reconciliation Rule

- Data source: `checkpoint_commit_map.jsonl`.
- Minimum fields per JSONL line:
  - `round_id`
  - `entire_checkpoint_id`
  - `commit_sha`
  - `changed_files`
  - `ts`
- Reconciliation checks:
  - Count of Thread 1~5 code-change commits equals mapping record count for Thread 1~5.
  - Every mapped commit includes `Entire-Checkpoint:` trailer.
  - Every `commit_sha` resolves in current branch history.

## Pass Criteria

Thread 6 may be marked Done only if ALL are true:
1. A non-simulated live regression run is executed once and recorded.
2. Reconciliation checks all pass.
3. No Thread 1~5 commit is missing `Entire-Checkpoint:` trailer.
4. Regressions required by `tests/m2-bpm-runtime/TEST.md` pass.

Fail-Closed:
- Any unmet criterion causes Thread 6 failure and status remains In Progress.
