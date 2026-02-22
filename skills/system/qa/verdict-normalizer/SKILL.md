---
name: "verdict-normalizer"
description: "Normalize objective, subjective, and regression evaluation outputs into one gate_decision"
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

# verdict-normalizer

## Objective

聚合分项评测输出并生成统一 `gate_decision`、`reasons[]` 和最终门禁证据。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m1-unified-quality-gate
input_contract:
  format: json_or_cli
  required:
    - objective_eval_ref
    - regression_eval_ref
    - aggregation_rules_ref
  validation:
    - objective_eval_ref and regression_eval_ref must be resolvable
    - subjective_eval_ref is optional only when explicitly disabled
    - aggregation_rules_ref must enforce P0 fail precedence
output_contract:
  format: json
  required:
    - gate_decision
    - reasons
    - evidence_ref
    - final_gate_verdict_ref
  machine_judgement:
    - gate_decision is pass or fail or hold or test_invalid
    - reasons is non-empty list
    - final_gate_verdict_ref is traceable
fail_closed_rules:
  - missing key evaluation package must fail
  - unparseable aggregation result must fail
  - missing evidence chain must fail
test_mount:
  test_doc: skills/system/qa/verdict-normalizer/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
references:
  aggregation_rules: skills/system/qa/verdict-normalizer/references/aggregation-rules.md
  script: skills/system/qa/verdict-normalizer/scripts/normalize_verdict.py
```

## Input Contract

- Format: json or CLI
- Required fields:
  - `objective_eval_ref`
  - `regression_eval_ref`
  - `aggregation_rules_ref`
- Optional:
  - `subjective_eval_ref`

## Output Contract

- Format: json
- Required fields:
  - `gate_decision`
  - `reasons[]`
  - `evidence_ref`
  - `final_gate_verdict_ref`

## Execution Steps

1. 加载各评测包并校验可解析性。
2. 解析 objective/regression（含 `release_gate_candidate`）并检测 P0 fail 证据。
3. 按优先级执行聚合：`fail > hold > test_invalid > pass`。
4. 写入 `final_gate_verdict_ref` 与 `aggregation_trace`。
5. 输出统一门禁结构。

最小执行命令：

```bash
python3 skills/system/qa/verdict-normalizer/scripts/normalize_verdict.py \
  --objective-eval docs/design/modules/evidence/quality-gate/smoke/objective_eval.json \
  --regression-eval docs/design/modules/evidence/quality-gate/smoke/regression_eval.json \
  --aggregation-rules docs/design/modules/evidence/quality-gate/smoke/aggregation_rules.json \
  --output-dir docs/design/modules/evidence/quality-gate/smoke/verdict-normalizer
```

## Fail-Closed Rules

- 任一关键评测包缺失或不可解析即 `fail`。
- 聚合结果不在允许枚举内即 `fail`。
- 证据写入失败即 `fail`。

## References

- 聚合规则：`skills/system/qa/verdict-normalizer/references/aggregation-rules.md`
