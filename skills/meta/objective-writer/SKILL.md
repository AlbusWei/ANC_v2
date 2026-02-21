---
name: "objective-writer"
description: "Draft objective contracts with measurable success criteria and fail-closed boundaries"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
---

# objective-writer

## Objective

将原始需求归一为可执行 Objective 契约，确保目标、约束、成功标准可被后续 Spec/Test 直接消费。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m3-objective-authoring
input_contract:
  format: json
  required:
    - objective_context
    - stakeholders
    - constraints
    - success_criteria
  validation:
    - objective_context must describe problem and desired outcome
    - constraints must include explicit non-goals
    - success_criteria must be measurable
output_contract:
  format: markdown
  required:
    - objective_ref
    - objective_statement
    - success_criteria
    - scope_baseline
    - non_goals
  machine_judgement:
    - output includes all required sections
    - success_criteria are testable
    - non_goals are explicit
fail_closed_rules:
  - missing measurable success criteria
  - missing scope boundary or non-goals
  - objective conflicts with system-level constraints
test_mount:
  test_doc: skills/meta/objective-writer/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```

## Input Contract

- Format: json
- Required fields: objective_context, stakeholders, constraints, success_criteria

## Output Contract

- Format: markdown
- Required fields: objective_ref, objective_statement, success_criteria, scope_baseline, non_goals
