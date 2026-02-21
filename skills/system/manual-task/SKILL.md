---
name: "manual-task"
description: "Execute controlled human-in-the-loop task with evidence output"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
---

# manual-task

## Objective

在需要人工介入时，以可追溯、可审计方式执行最小任务并返回结构化证据。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-manual-task-fallback
input_contract:
  format: json
  required:
    - objective_ref
    - task_ref
    - acceptance_criteria
  validation:
    - objective_ref must be provided
    - task_ref must point to a reachable document
    - acceptance_criteria must be explicit
output_contract:
  format: json
  required:
    - output_ref
    - evidence_ref
    - decision
    - reason
  machine_judgement:
    - output_ref and evidence_ref are present
    - decision is pass or fail
    - reason is non-empty
fail_closed_rules:
  - missing required input fields
  - missing evidence_ref
  - unverifiable acceptance criteria
test_mount:
  test_doc: skills/system/manual-task/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```
