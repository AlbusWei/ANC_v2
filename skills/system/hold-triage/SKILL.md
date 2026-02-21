---
name: "hold-triage"
description: "Collect progress signals and classify hold actions"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
---

# hold-triage

## Objective

将 HOLD 场景标准化为证据采集、分类与动作执行，避免固定超时误杀。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m1-unified-quality-gate
input_contract:
  format: json
  required:
    - hold_case_ref
    - runtime_log_ref
    - execution_state_ref
    - triage_policy_ref
  validation:
    - hold_case_ref must be resolvable
    - progress signals must include log delta and phase progress and output heartbeat
    - triage_policy_ref must define continue retry debug fail
output_contract:
  format: json
  required:
    - progress_signals_ref
    - triage_action
    - triage_report_ref
    - action_execution_ref
  machine_judgement:
    - triage_action is continue or retry or debug or fail
    - triage_report_ref is present and traceable
    - action_execution_ref reflects selected triage action
fail_closed_rules:
  - missing progress signals and unable to recover evidence must fail
  - triage decision absent must fail
  - evidence chain untraceable must fail
test_mount:
  test_doc: skills/system/hold-triage/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```
