---
name: "manual-task"
description: "Execute BPM actor task from natural-language dispatch context and archive protocol evidence"
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

# manual-task

## Objective

作为通用执行入口，让 Actor 按 BPM 分发的自然语言任务执行阶段工作，并按协议沉淀可追溯结果。

该技能是“自然语言任务执行 + 协议留档”能力：适用于 inline_ap 场景下的通用阶段执行。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-manual-task-fallback
input_contract:
  format: json
  required:
    - objective_ref
    - acceptance_criteria
    - expected_outputs
  validation:
    - legacy mode requires objective_ref + task_ref + acceptance_criteria + expected_outputs
    - dispatch mode allows objective_ref from task_dispatch.objective_ref
    - dispatch mode requires task_dispatch.instance_id/phase_id/actor/session_binding/evidence_dir
    - dispatch mode must include session_binding.session_id
    - acceptance_criteria must be explicit (or use dispatch default)
    - expected_outputs must declare at least one artifact path
output_contract:
  format: json
  required:
    - output_ref
    - evidence_ref
    - decision
    - reason
    - mode
  machine_judgement:
    - output_ref and evidence_ref are present
    - decision is pass or fail
    - reason is non-empty
    - dispatch mode emits task_completion payload
fail_closed_rules:
  - missing required input fields
  - missing evidence_ref
  - unverifiable acceptance criteria
test_mount:
  test_doc: skills/system/manual-task/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
references:
  runner_script: skills/system/manual-task/scripts/manual_task_runner.py
```
