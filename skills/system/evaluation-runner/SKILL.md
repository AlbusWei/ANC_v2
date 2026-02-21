---
name: "evaluation-runner"
description: "Run objective/subjective/regression evaluations through unified runner contract"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
---

# evaluation-runner

## Objective

作为统一评测执行入口，在 objective/subjective/regression 模式下输出可追溯评测证据。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m1-unified-quality-gate
input_contract:
  format: json
  required:
    - preparation_bundle_ref
    - actual_output_refs
    - evaluation_mode
  validation:
    - preparation_bundle_ref must be resolvable
    - actual_output_refs must be non-empty list
    - evaluation_mode must be objective or subjective or regression
output_contract:
  format: json
  required:
    - raw_eval_ref
    - runner_log_ref
    - execution_state_ref
    - evaluation_verdict
  machine_judgement:
    - output is valid json
    - evaluation_verdict is pass or fail or hold or test_invalid
    - raw_eval_ref and runner_log_ref are traceable
fail_closed_rules:
  - invalid execution protocol must fail
  - missing critical input must fail
  - unparseable verdict payload must fail
test_mount:
  test_doc: skills/system/evaluation-runner/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```
