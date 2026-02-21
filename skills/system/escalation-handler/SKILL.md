---
name: "escalation-handler"
description: "Close hold cases or escalate through governed escalation chain"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
---

# escalation-handler

## Objective

按固定升级链完成 hold 案例收敛或升级，确保决策可追溯。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m1-unified-quality-gate
input_contract:
  format: json
  required:
    - hold_case_ref
    - triage_action
    - health_maintenance_ref
    - escalation_policy_ref
  validation:
    - triage_action must be continue or retry or debug or fail
    - escalation_policy_ref must define qa to bpm to admin chain
    - health_maintenance_ref must be traceable
output_contract:
  format: json
  required:
    - hold_resolution_ref
    - escalation_ref
    - final_resolution
  machine_judgement:
    - final_resolution is closed or escalated or failed
    - hold_resolution_ref is present
    - escalation_ref is required when final_resolution is escalated
fail_closed_rules:
  - missing closure decision must fail
  - invalid escalation chain must fail
  - missing evidence for escalation must fail
test_mount:
  test_doc: skills/system/escalation-handler/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```
