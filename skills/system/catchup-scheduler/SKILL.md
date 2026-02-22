---
name: "catchup-scheduler"
description: "Perform catchup scheduling inside catchup window and route overflow to escalation"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
---

# catchup-scheduler

## Objective

在漏跑场景下按动态策略计算补跑窗口并执行补跑，超窗场景输出升级建议。

策略编写参考：`docs/design/processes/trigger-runtime-policy-guidelines.md`。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m2-trigger-governance-runtime
input_contract:
  format: json
  required:
    - missed_run_ref
    - catchup_policy_ref
    - trigger_policy_ref
    - runtime_state_ref
  validation:
    - catchup_policy_ref must define dynamic window function
    - dynamic window must be derivable from trigger_type and risk_level
    - missed_run_ref must include expected_run_at
    - runtime_state_ref must include latest successful run
output_contract:
  format: json
  required:
    - catchup_decision
    - catchup_run_ref
    - catchup_reason_ref
    - escalation_hint
  machine_judgement:
    - catchup_decision is run or skip or escalate
    - catchup reason is non-empty
    - escalation_hint exists when decision is escalate
fail_closed_rules:
  - missed run evidence missing
  - catchup policy missing or not evaluable
  - catchup decision ambiguous
test_mount:
  test_doc: skills/system/catchup-scheduler/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```

## Runtime Entrypoint

1. 可执行入口：`skills/system/catchup-scheduler/scripts/catchup_scheduler_runner.py`
2. 最小命令：
   - `python3 skills/system/catchup-scheduler/scripts/catchup_scheduler_runner.py --input <input.json> --output <output.json> --run <catchup_run.json> --reason <catchup_reason.json>`
