# Live Test Follow-up (2026-02-22)

## Scope

- Change: `m2-bpm-runtime-hardening`
- Workspace: `ANC_v2_worktrees/review-layers-modules`
- Goal: backfill OpenClaw live tests for completed W1/W2/W3/W3-B work.

## Execution Mode

1. Preferred path: run via OpenClaw `qa` agent (`openclaw agent --agent qa ...`).
2. Fallback path: Codex directly executes the same live runner when QA-agent channel is unstable.
3. All suite results are validated from persisted JSON reports under `docs/design/modules/evidence/bpm-runtime/`.

## Suite Results

| Suite | Runner | Mode | Report | Result |
|---|---|---|---|---|
| W1 `TC-INS-001~005` | `python3 tests/m2-bpm-runtime/run_tc_ins.py --run-live-migration` | QA agent | `docs/design/modules/evidence/bpm-runtime/w1_tc_ins_report.json` | pass (5/5) |
| W2 `TC-GCC-001~003` | `python3 tests/m2-bpm-runtime/run_tc_gcc.py` | QA agent + Codex fallback | `docs/design/modules/evidence/bpm-runtime/w2_tc_gcc_report.json` | pass (3/3) |
| W3 `TG-SCH-001~004 + TG-EVT-001~003` | `python3 tests/m2-bpm-runtime/run_tc_tg.py` | QA agent | `docs/design/modules/evidence/bpm-runtime/w3_tc_tg_report.json` | pass (7/7) |
| W3-B `TC-QA-PROC-001~002` | `python3 tests/m2-bpm-runtime/run_tc_qa_proc.py` | QA agent | `docs/design/modules/evidence/bpm-runtime/w3b_tc_qa_proc_report.json` | pass (2/2) |

## QA Agent Runtime Notes

1. QA agent run IDs:
   - TG suite: `5e86d97b-64eb-464c-aca5-383f47b3c901`
   - QA-PROC suite: `5749aaeb-d60a-4e00-85bc-7cb47491ba16`
2. During GCC execution, OpenClaw gateway had intermittent restart (`gateway closed (1012): service restart`), causing unstable QA-agent CLI return behavior.
3. GCC suite was re-run by Codex (same live runner) and converged to pass (3/3). The persisted report is the final truth source.

## Thread-6 Regression Entrypoint Status

- Command: `python3 tests/m2-bpm-runtime/run_post_dev_regression.py --mode live`
- Result: `failed` (fail-closed)
- Blocking reason: missing required file `tests/m2-bpm-runtime/live_regression_cases.md`
- Evidence: `docs/design/modules/evidence/bpm-runtime/latest_live_regression_result.json`

