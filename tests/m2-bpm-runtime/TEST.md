# M2 BPM Runtime Hardening Test Entry

## Scope

This test mount is the execution entry for `m2-bpm-runtime-hardening` rounds.
Thread 0 provides scaffolding only; runtime behavior re-implementation is out of scope.

## Entrypoint

- Regression runner: `tests/m2-bpm-runtime/run_post_dev_regression.py`
- W1 instance suite runner: `tests/m2-bpm-runtime/run_tc_ins.py`
- W2 governed config suite runner: `tests/m2-bpm-runtime/run_tc_gcc.py`
- W3 trigger runtime suite runner: `tests/m2-bpm-runtime/run_tc_tg.py`
- W3-B QA process orchestration suite runner: `tests/m2-bpm-runtime/run_tc_qa_proc.py`
- W4 system-analyst P1 suite runner: `tests/m2-bpm-runtime/run_tc_anl.py`
- Expected mode for Thread 6: live regression (non-simulated)

## Evidence Inputs

- Preconditions evidence: `docs/design/modules/evidence/bpm-runtime/precheck_apply_ready_evidence.md`
- Round map: `docs/design/modules/evidence/bpm-runtime/checkpoint_commit_map.jsonl`
- Commit range: `docs/design/modules/evidence/bpm-runtime/git_range.txt`
- Live plan: `docs/design/modules/evidence/bpm-runtime/m6_live_regression_plan.md`

## Fail-Closed Policy

- Missing Entire/OpenClaw precheck evidence: FAIL.
- Missing checkpoint/commit mapping for any required round: FAIL.
- Any commit without `Entire-Checkpoint:` trailer in Thread 1~5 history: FAIL.
- Live regression not executed in Thread 6: FAIL.

## Mapping Contract

Each JSONL record in `checkpoint_commit_map.jsonl` must include:

- `round_id`
- `entire_checkpoint_id`
- `commit_sha`
- `changed_files`
- `ts`

## W1 Instance Core Cases

- Case doc: `tests/m2-bpm-runtime/TC-INS.md`
- Required pass set: `TC-INS-001~005`
- Suggested command:
  - `python3 tests/m2-bpm-runtime/run_tc_ins.py --run-live-migration`

## W2 Governed Config Core Cases

- Case doc: `tests/m2-bpm-runtime/TC-GCC.md`
- Required pass set: `TC-GCC-001~003`
- Suggested command:
  - `python3 tests/m2-bpm-runtime/run_tc_gcc.py`

## W3 Trigger Runtime Core Cases

- Case doc: `tests/m2-bpm-runtime/TC-TG.md`
- Required pass set: `TG-SCH-001~004`, `TG-EVT-001~003`
- Suggested command:
  - `python3 tests/m2-bpm-runtime/run_tc_tg.py`

## W3-B QA Process Core Cases

- Case doc: `tests/m2-bpm-runtime/TC-QA-PROC.md`
- Required pass set: `TC-QA-PROC-001~002`
- Suggested command:
  - `python3 tests/m2-bpm-runtime/run_tc_qa_proc.py`

## W5 System Analyst Production Cases

- Case doc: `tests/m2-bpm-runtime/TC-ANL.md`
- Required pass set: `TC-ANL-001~003`
- Suggested command:
  - `python3 tests/m2-bpm-runtime/run_tc_anl.py`

## Minimal Execution Contract

1. Ensure evidence directory exists: `docs/design/modules/evidence/bpm-runtime/`.
2. Collect git range and write `git_range.txt` before live run.
3. Execute regression runner and persist output evidence.
4. Reconcile checkpoint/commit mapping before declaring done.
