# M2 BPM Runtime Hardening Test Entry

## Scope

This test mount is the execution entry for `m2-bpm-runtime-hardening` rounds.
Thread 0 provides scaffolding only; runtime behavior re-implementation is out of scope.

## Entrypoint

- Regression runner: `tests/m2-bpm-runtime/run_post_dev_regression.py`
- Expected mode for Thread 6: live regression (non-simulated)

## Fail-Closed Policy

- Missing Entire/OpenClaw precheck evidence: FAIL.
- Missing checkpoint/commit mapping for any required round: FAIL.
- Any commit without `Entire-Checkpoint:` trailer in Thread 1~5 history: FAIL.
- Live regression not executed in Thread 6: FAIL.

## Minimal Execution Contract

1. Ensure evidence directory exists: `docs/design/modules/evidence/bpm-runtime/`.
2. Collect git range and write `git_range.txt` before live run.
3. Execute regression runner and persist output evidence.
4. Reconcile checkpoint/commit mapping before declaring done.
