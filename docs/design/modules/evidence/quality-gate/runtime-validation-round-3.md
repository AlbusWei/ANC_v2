# Quality Gate Runtime Validation - Round 3

- Date: 2026-02-22
- Scope: `sys.qa.test-compiler` + `sys.qa.evaluation-runner` (dynamic grader + strict model config)
- Evidence root: `docs/design/modules/evidence/quality-gate/runtime-validation-round-3/outputs/`

## What Was Executed

1. Re-compile dynamic LLM test plan:
   - `python3 skills/system/qa/test-compiler/scripts/compile_test_doc.py ...`
2. Run `quality_eval_runner` objective mode with strict user config:
   - `OPENAI_BASE_URL=https://right.codes/codex/v1`
   - `OPENAI_API_KEY=<provided>`
   - `--judge-model GPT-5.2`
3. Run `quality_eval_runner` subjective mode using round-2 rule datapoints to validate blind A/B trace recording (`blind_assignment` + `judge_result` per round).
4. Run `quality_eval_runner` subjective mode with strict LLM config (`GPT-5.2` + `OPENAI_BASE_URL`) to validate unsupported-model fail-closed mapping.

## Key Results

- `test-compiler`: `pass`
- `evaluation-runner` objective (LLM dynamic grader): `test_invalid`
  - reason: `judge_model_unsupported:GPT-5.2:...`
  - exit code: `20`
- `evaluation-runner` subjective (rule fallback path): `hold` with complete blind A/B comparison trace
  - exit code: `30`
- `evaluation-runner` subjective (LLM listwise, strict config): `test_invalid`
  - reason: `judge_model_unsupported:GPT-5.2:...`
  - exit code: `20`

Machine summary:
- `docs/design/modules/evidence/quality-gate/runtime-validation-round-3/outputs/runtime_summary.json`

## Interpretation

1. Runner now classifies unsupported judge model as `test_invalid` (Fail-Closed) instead of generic `fail`.
2. Subjective mode now records blind assignment metadata and per-round judge result payloads（rule fallback 可运行，LLM listwise 在当前账号约束下正确 fail-close）。
3. Dynamic grader planning remains test-plan-driven (`grader_selection/grader_weights/min_score_per_grader/must_pass_graders`) and auditable in compiled datapoints.
