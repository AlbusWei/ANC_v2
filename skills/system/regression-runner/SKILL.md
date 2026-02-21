---
name: "regression-runner"
description: "Run cross-module regression and emit release gate candidate"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
---

# regression-runner

## Objective

执行跨模块回归验证，输出回归评测报告与发布门禁候选结论。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m1-unified-quality-gate
input_contract:
  format: json
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
  machine_judgement:
    - output is valid json
    - release_gate_candidate is pass or fail or hold
    - regression_report_ref includes module level verdicts
fail_closed_rules:
  - missing regression evidence must fail
  - unparseable regression result must fail
  - any module P0 fail must block release
test_mount:
  test_doc: skills/system/regression-runner/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```
