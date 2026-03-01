---
name: "regression-runner"
description: "Run cross-module regression by orchestrating evaluation-runner regression mode and emitting release gate candidates"
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

# regression-runner

## Objective

执行跨模块回归并输出 `regression_eval_ref`、`regression_report_ref` 与 `release_gate_candidate`。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m1-unified-quality-gate
input_contract:
  format: cli
  required:
    - regression_scope
    - profile_set
    - preparation_bundle_ref
    - actual_output_refs
  validation:
    - regression_scope must include target modules
    - preparation_bundle_ref must be resolvable
    - profile_set must include baseline profile
output_contract:
  format: json
  required:
    - regression_eval_ref
    - regression_report_ref
    - release_gate_candidate
    - gate_decision
    - evidence_ref
    - reasons
  machine_judgement:
    - output is valid json
    - release_gate_candidate is pass or fail or hold
    - regression_report_ref includes module-level summary
fail_closed_rules:
  - missing regression evidence must fail
  - unparseable regression result must fail
  - any module P0 fail must block release
test_mount:
  test_doc: skills/system/qa/regression-runner/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
references:
  regression_scope: skills/system/qa/regression-runner/references/regression-scope.md
  script: skills/system/qa/regression-runner/scripts/run_regression.py
```

## Input Contract

- Format: CLI
- Required fields:
  - `--regression-scope`
  - `--profile-set`
  - `--preparation-bundle`
  - `--actual-output` (one or more)

## Output Contract

- Format: json
- Required fields:
  - `regression_eval_ref`
  - `regression_report_ref`
  - `release_gate_candidate`
  - `gate_decision`
  - `evidence_ref`
  - `reasons[]`

## Execution Steps

1. 解析 regression scope 与准备包。
2. 按 `regression_scope` 对每个模块分别调用 `quality_eval_runner --mode regression`。
3. 汇总模块级结果并产出 release gate candidate（`fail > hold > pass`）。
4. 任何关键异常触发 Fail-Closed。

最小执行命令：

```bash
python3 skills/system/qa/regression-runner/scripts/run_regression.py \
  --regression-scope M3,M4,M5 \
  --profile-set quality-gate.baseline@1.0.0 \
  --preparation-bundle runtime_data/execution/evidence/quality-gate/smoke/preparation_bundle.index.json \
  --actual-output runtime_data/execution/evidence/quality-gate/smoke/actual_output.pass.txt \
  --output-dir runtime_data/execution/evidence/quality-gate/smoke/regression-runner
```

## Fail-Closed Rules

- 缺失准备包或实际输出时返回 `fail`。
- 子评测结果不可解析时返回 `fail`。
- 发现 P0 失败时 `release_gate_candidate=fail`。

## References

- 回归范围规范：`skills/system/qa/regression-runner/references/regression-scope.md`
