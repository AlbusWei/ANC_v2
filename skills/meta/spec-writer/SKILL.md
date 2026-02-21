---
name: "spec-writer"
description: "Generate objective-aligned technical spec with enforceable constraints"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
---

# spec-writer

## Objective

将 Objective 形式化为可执行、可测试、可审计的规范文档。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-phase1-min-loop
input_contract:
  format: json
  required:
    - objective_ref
    - problem_statement
    - constraints
  validation:
    - objective_ref must be provided
    - problem_statement must be specific and testable
    - constraints must be explicit
output_contract:
  format: markdown
  required:
    - scope
    - input_contract
    - output_contract
    - acceptance_criteria
    - risks
  machine_judgement:
    - output includes all required sections
    - acceptance_criteria are testable
    - risks include rollback direction
fail_closed_rules:
  - missing required input fields
  - output missing required sections
  - objective conflicts with SSOT
test_mount:
  test_doc: /Users/albus/MyProjects/ANC_v2/skills/meta/spec-writer/TEST.md
  methodology_ref: /Users/albus/MyProjects/ANC_v2/docs/architecture/test_methodology.md
```

## Input Contract

- Format: json
- Required fields: objective_ref, problem_statement, constraints

## Output Contract

- Format: markdown
- Required fields: scope, input_contract, output_contract, acceptance_criteria, risks

## Behavior Specification

1. 对齐 objective_ref，明确范围与非目标。
2. 输出结构中必须出现 I/O 契约和验收条件。
3. 标注风险与回滚策略。

## Constraints

- 不得输出无法验证的模糊条款。
- 不得与 SSOT 冲突。

## Version

- Current: 0.1.0
- Status: Draft
