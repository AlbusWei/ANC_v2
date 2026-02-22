---
name: "evaluation-runner"
description: "Run objective, subjective, and regression evaluation through quality_eval_runner and emit unified verdict artifacts"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
version: "0.2.0"
---

# evaluation-runner

## Objective

提供统一评测执行入口 `quality_eval_runner`，使用 OpenJudge 真执行评测链输出可追溯 verdict 工件，并支持 LLM-as-Judge 路径。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m1-unified-quality-gate
input_contract:
  format: cli
  required:
    - preparation_bundle_ref
    - actual_output_refs
    - evaluation_mode
  validation:
    - preparation_bundle_ref must be resolvable
    - preparation_bundle_ref must include test_datapoints_ref and tc_profile_map_ref
    - actual_output_refs must be non-empty list
    - evaluation_mode must be objective or subjective or regression
output_contract:
  format: json
  required:
    - raw_eval_ref
    - runner_log_ref
    - execution_state_ref
    - evaluation_verdict
    - gate_decision
    - evidence_ref
    - reasons
  machine_judgement:
    - output is valid json
    - evaluation_verdict is pass or fail or hold or test_invalid
    - raw_eval_ref and runner_log_ref are traceable
fail_closed_rules:
  - invalid execution protocol must fail
  - pre-run contract errors must return test_invalid
  - llm-judge mode without model credentials must return test_invalid
  - unparseable verdict payload must fail
test_mount:
  test_doc: skills/system/qa/evaluation-runner/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
references:
  runner_contract: skills/system/qa/evaluation-runner/references/runner-contract.md
  cli_script: skills/system/qa/evaluation-runner/scripts/quality_eval_runner
```

## Input Contract

- Format: CLI
- Required fields:
  - `--preparation-bundle`
  - `--mode objective|subjective|regression`
  - `--actual-output` (one or more)

## Output Contract

- Format: json
- Required fields:
  - `raw_eval_ref`
  - `runner_log_ref`
  - `execution_state_ref`
  - `evaluation_verdict`
  - `gate_decision`
  - `evidence_ref`
  - `reasons[]`

## Execution Steps

1. 解析 `preparation_bundle_ref` 并校验最小字段。
2. 加载 `actual_output_refs`，按 mode 执行评测。
3. `objective/regression`：按 datapoint 的 `evaluation_method` 调度 OpenJudge grader（`StringMatch` 或 LLM graders）。
4. `subjective`：执行盲测 A/B，使用 listwise 比较（优先 `LLMGrader` / 可选 `SimpleRubricsGenerator`），记录 seed、随机映射与每轮 judge 结果，输出 `accept|reject|review` 对应 `pass|fail|hold`。
5. `LLM-Judge`：可从 `TEST.md` 编译产物读取 `grader_selection/grader_weights/min_score_per_grader` 动态选择 grader；
   支持 `auto_rubric_task_description` 触发 OpenJudge `SimpleRubricsGenerator` 自动生成 rubric grader。
6. 对 LLM grader 错误做分类：临时错误 -> `hold`；模型/凭据/无效请求 -> `test_invalid`；其他执行异常 -> `fail`。
7. 输出 `raw_eval_ref`、运行日志与 verdict。
8. 返回码遵循 `M1-openjudge-adapter-spec`：`0/20/30/40/50`。

最小执行命令：

```bash
skills/system/qa/evaluation-runner/scripts/quality_eval_runner run \
  --preparation-bundle docs/design/modules/evidence/quality-gate/smoke/preparation_bundle.index.json \
  --mode objective \
  --actual-output docs/design/modules/evidence/quality-gate/smoke/actual_output.pass.txt \
  --module M3 \
  --output-dir docs/design/modules/evidence/quality-gate/smoke/evaluation-runner
```

LLM-as-Judge（需要环境变量 `OPENAI_API_KEY`）：

```bash
skills/system/qa/evaluation-runner/scripts/quality_eval_runner run \
  --preparation-bundle docs/design/modules/evidence/quality-gate/runtime-validation-round-2/outputs/preparation_bundle_llm.index.json \
  --mode objective \
  --actual-output docs/design/modules/evidence/quality-gate/runtime-validation-round-2/fixtures/actual_output_pass.txt \
  --judge-model gpt-5.3-codex \
  --module M3 \
  --output-dir docs/design/modules/evidence/quality-gate/runtime-validation-round-2/outputs/evaluation-runner-llm
```

## Fail-Closed Rules

- mode 非法或关键输入缺失时返回 `test_invalid` 或 `fail`。
- `LLM-Judge` 缺失 `judge_model` 或 `OPENAI_API_KEY` 时返回 `test_invalid`。
- `LLM-Judge` 模型不受支持（例如 provider 返回 unsupported model）时返回 `test_invalid`。
- verdict 不可解析时返回 `fail`。
- 证据写入失败时返回 `fail`。

## References

- CLI 契约说明：`skills/system/qa/evaluation-runner/references/runner-contract.md`
