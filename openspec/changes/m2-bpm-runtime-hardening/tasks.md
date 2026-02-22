## 1. Governance Preconditions

- [x] 1.1 Verify Entire is enabled with `manual-commit` and start a bridge session for this change.
- [x] 1.2 Switch OpenClaw workspace to current worktree and pass minimal config/skill verification.
- [x] 1.3 Capture command evidence for prechecks in change evidence notes.

## 2. Thread 0 Baseline Scaffold

- [x] 2.1 Initialize `tests/m2-bpm-runtime/TEST.md` with scope, entrypoint, and fail-closed test policy.
- [x] 2.2 Initialize `tests/m2-bpm-runtime/run_post_dev_regression.py` as executable regression runner skeleton.
- [x] 2.3 Initialize evidence directory files: `checkpoint_commit_map.jsonl`, `git_range.txt`, and `m6_live_regression_plan.md`.
- [x] 2.4 Update `docs/architecture/construction_plane.md` to mark `m2-bpm-runtime-hardening` as In Progress（Thread 0 基线阶段）。

## 3. Thread 1-5 Checkpoint/Commit Audit Loop

- [x] 3.1 After each code-change commit, run bridge `sync` with changed-file attribution.
- [x] 3.2 Append one JSONL mapping record with required fields to `checkpoint_commit_map.jsonl`.
- [x] 3.3 Verify latest commit contains `Entire-Checkpoint:` trailer via `git log -1 --pretty=raw`.

## 4. Thread 6 Live Regression Closure

- [x] 4.1 Collect actual git range for Thread 1~6 and write `git_range.txt`.
- [x] 4.2 Execute one non-simulated live regression run via the post-dev regression entrypoint.
- [x] 4.3 Reconcile checkpoint/commit counts and fail-closed when any prior commit misses `Entire-Checkpoint:` trailer.
- [x] 4.4 Update construction-plane status and close `Q-001` only after live regression pass criteria are satisfied.
