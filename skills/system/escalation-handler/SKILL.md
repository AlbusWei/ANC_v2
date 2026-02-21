---
name: "escalation-handler"
description: "Execute governed escalation chain for BPM runtime anomalies"
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

在运行异常、补跑失败或风险无法判定时，按升级链执行升级并输出可审计记录。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m2-bpm-runtime-escalation
input_contract:
  format: json
  required:
    - incident_ref
    - escalation_policy_ref
    - current_owner
    - evidence_ref
  validation:
    - escalation policy must define actor->owner->bpm->admin->human
    - incident_ref must include severity and reason
    - evidence_ref must be reachable
output_contract:
  format: json
  required:
    - escalation_ref
    - final_owner
    - escalation_decision
    - escalation_trace
  machine_judgement:
    - escalation_decision is escalate or resolve
    - escalation_trace has at least one hop
    - final_owner is in escalation chain
fail_closed_rules:
  - escalation chain missing required hop
  - escalation target bypasses governance chain
  - incident evidence missing or unreachable
test_mount:
  test_doc: skills/system/escalation-handler/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```
