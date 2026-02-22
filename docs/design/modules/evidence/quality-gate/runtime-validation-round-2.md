# Quality Gate Runtime Validation - Round 2

- Date: 2026-02-21
- Scope: `sys.qa.test-compiler` -> `sys.qa.evaluation-runner` -> `sys.qa.regression-runner` -> `sys.qa.verdict-normalizer` + hold/registry/archive side skills
- Evidence root: `docs/design/modules/evidence/quality-gate/runtime-validation-round-2/outputs/`

## What Was Executed

1. Compile `TEST.md` into datapoints and profile map.
2. Run `quality_eval_runner` in `objective` mode (OpenJudge rule-match graders).
3. Run `quality_eval_runner` in `regression` mode.
4. Run `regression-runner` over `M3,M4` (per-module orchestration).
5. Normalize verdict with `verdict-normalizer`.
6. Run `hold-triage` with log/phase deltas.
7. Run `registry-validator` against `registry_contract_tool.py verify`.
8. Run `evidence-archiver` with traceability refs.
9. Run `quality_eval_runner` in `subjective` mode (A/B tie case).
10. Run `quality_eval_runner` with `LLM-Judge` testcase and missing API key.

## Key Results

- `objective`: `pass`
- `regression`: `pass`
- `regression-runner`: `pass`
- `verdict-normalizer`: `pass`
- `hold-triage`: `pass` with action `debug`
- `registry-validator`: `pass`
- `evidence-archiver`: `pass`
- `subjective`: `hold` (`review`, tie win_rate=0.5), exit code `30`
- `llm-judge missing key`: `test_invalid`, exit code `20`

Machine summary:
- `docs/design/modules/evidence/quality-gate/runtime-validation-round-2/outputs/runtime_summary.json`

## Interpretation

1. OpenJudge execution path is active and no longer marker-only.
2. Subjective A/B path enforces seed and reproducible round logs.
3. LLM-as-Judge path is wired and fail-closes when credentials are missing.
