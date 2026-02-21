---
name: "process-instance-manager"
description: "Maintain runtime health and recovery state for governed process instances"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
---

# process-instance-manager

## Objective

在 HOLD 或异常场景下维护流程实例健康状态，并输出恢复证据。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m1-unified-quality-gate
input_contract:
  format: json
  required:
    - hold_case_ref
    - action_execution_ref
    - runtime_health_policy_ref
  validation:
    - hold_case_ref must be resolvable
    - action_execution_ref must be traceable
    - runtime_health_policy_ref must define recovery checks
output_contract:
  format: json
  required:
    - health_maintenance_ref
    - runtime_recovery_state
  machine_judgement:
    - health_maintenance_ref is present
    - runtime_recovery_state is recovering or stabilized or failed
    - output is valid json
fail_closed_rules:
  - health check failed and unrecoverable must fail
  - recovery actions without evidence must fail
  - policy parsing failure must fail
test_mount:
  test_doc: skills/system/process-instance-manager/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```
