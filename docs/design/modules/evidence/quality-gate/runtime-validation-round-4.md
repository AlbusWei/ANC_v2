# Quality Gate Runtime Validation - Round 4

- Date: 2026-02-22
- Scope: `sys.qa.evaluation-runner` LLM-as-Judge run-through with model `gpt-5.3-codex`
- Evidence root: `docs/design/modules/evidence/quality-gate/runtime-validation-round-4/outputs/`

## Runtime Config

1. `OPENAI_BASE_URL=https://right.codes/codex/v1`
2. `OPENAI_API_KEY=<provided>`
3. `--judge-model gpt-5.3-codex`

## What Was Executed

1. Objective mode (dynamic grader plan):
   - `quality_eval_runner run --mode objective ...`
2. Subjective mode (LLM listwise blind A/B):
   - `quality_eval_runner run --mode subjective ... --subjective-rounds 3 --seed 13`
3. Objective mode without explicit `--judge-model` (verify default model switch):
   - `quality_eval_runner run --mode objective ...` (default `gpt-5.3-codex`)

## Key Results

- Objective LLM-as-Judge: `pass` (exit code `0`)
- Subjective LLM listwise A/B: `pass` (exit code `0`, `win_rate=1.0`, `subjective_verdict=accept`)
- Objective using default model config: `pass` (exit code `0`)

## Interpretation

1. Core LLM-as-Judge path now runs through successfully with `gpt-5.3-codex`.
2. Subjective listwise blind evaluation is executable and produces reproducible per-round trace (`seed/blind_assignment/rank/reason`).
3. Prior `GPT-5.2` unsupported-model fail-closed evidence remains in round-3 as negative-path governance proof.

Machine summary:
- `docs/design/modules/evidence/quality-gate/runtime-validation-round-4/outputs/runtime_summary.json`
