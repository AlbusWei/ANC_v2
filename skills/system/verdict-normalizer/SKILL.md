---
name: "verdict-normalizer"
description: "Normalize evaluation outputs into unified gate decision"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
---

# verdict-normalizer

## Objective

聚合分项评测输出并生成统一 `gate_decision` 与最终 verdict 证据。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m1-unified-quality-gate
input_contract:
  format: json
  required:
    - objective_eval_ref
    - subjective_eval_ref
    - regression_eval_ref
    - aggregation_rules_ref
  validation:
    - objective_eval_ref and regression_eval_ref must be resolvable
    - aggregation_rules_ref must include P0 fail precedence
    - subjective_eval_ref may be omitted only when explicitly disabled by profile
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
    - evidence_ref and final_gate_verdict_ref are traceable
fail_closed_rules:
  - missing key evaluation package must fail
  - unparseable aggregation result must fail
  - missing evidence chain must fail
test_mount:
  test_doc: skills/system/verdict-normalizer/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```
